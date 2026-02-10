"""OpenAPI Spec Loader.

Provides the main SpecLoader class and utilities to transform a validated OpenAPI spec
into the internal IR dataclasses. This implementation covers a subset of the OpenAPI
surface, sufficient for the code emitter prototypes.
"""

from __future__ import annotations

import logging
import os
import warnings
from typing import Any, List, Mapping, cast

try:
    # Use the newer validate() API if available to avoid deprecation warnings
    from openapi_spec_validator import validate as validate_spec
except ImportError:
    try:
        from openapi_spec_validator import validate_spec  # type: ignore
    except ImportError:  # pragma: no cover – optional in early bootstrapping
        validate_spec = None  # type: ignore[assignment]

from pyopenapi_gen import IRSchema, IRSpec
from pyopenapi_gen.core.loader.operations import parse_operations
from pyopenapi_gen.core.loader.schemas import build_schemas, extract_inline_enums
from pyopenapi_gen.core.parsing.transformers.discriminator_enum_collector import (
    DiscriminatorEnumCollector,
    UnifiedDiscriminatorEnum,
)
from pyopenapi_gen.ir import NamingStrategy

__all__ = ["SpecLoader", "load_ir_from_spec"]

logger = logging.getLogger(__name__)

# Check for cycle detection debug flags in environment
MAX_CYCLES = int(os.environ.get("PYOPENAPI_MAX_CYCLES", "0"))


class SpecLoader:
    """Transforms a validated OpenAPI spec into IR dataclasses.

    This class follows the Design by Contract principles and ensures that
    all operations maintain proper invariants and verify their inputs/outputs.
    """

    def __init__(self, spec: Mapping[str, Any]):
        """Initialize the spec loader with an OpenAPI spec.

        Contracts:
            Preconditions:
                - spec is a valid OpenAPI spec mapping
                - spec contains required OpenAPI fields
            Postconditions:
                - Instance is ready to load IR from the spec
        """
        if not isinstance(spec, Mapping):
            raise ValueError("spec must be a Mapping")
        if "openapi" not in spec:
            raise ValueError("Missing 'openapi' field in the specification")
        if "paths" not in spec:
            raise ValueError("Missing 'paths' section in the specification")

        self.spec = spec
        self.info = spec.get("info", {})
        self.title = self.info.get("title", "API Client")
        self.version = self.info.get("version", "0.0.0")
        self.description = self.info.get("description")
        self.raw_components = spec.get("components", {})
        self.raw_schemas = self.raw_components.get("schemas", {})
        self.raw_parameters = self.raw_components.get("parameters", {})
        self.raw_responses = self.raw_components.get("responses", {})
        self.raw_request_bodies = self.raw_components.get("requestBodies", {})
        self.paths = spec["paths"]
        self.servers = [s.get("url") for s in spec.get("servers", []) if "url" in s]

    def validate(self) -> List[str]:
        """Validate the OpenAPI spec but continue on errors.

        Contracts:
            Postconditions:
                - Returns a list of validation warnings
                - The spec is validated using openapi-spec-validator if available
        """
        warnings_list = []

        if validate_spec is not None:
            try:
                from typing import Hashable

                validate_spec(cast(Mapping[Hashable, Any], self.spec))
            except Exception as e:
                warning_msg = f"OpenAPI spec validation error: {e}"
                # Always collect the message
                warnings_list.append(warning_msg)

                # Heuristic: if this error originates from jsonschema or
                # openapi_spec_validator, prefer logging over global warnings
                # to avoid noisy test output while still surfacing the issue.
                origin_module = getattr(e.__class__, "__module__", "")
                if (
                    isinstance(e, RecursionError)
                    or origin_module.startswith("jsonschema")
                    or origin_module.startswith("openapi_spec_validator")
                ):
                    logger.warning(warning_msg)
                else:
                    # Preserve explicit warning behavior for unexpected failures
                    warnings.warn(warning_msg, UserWarning)

        return warnings_list

    def _create_unified_enum_schema(self, enum_metadata: UnifiedDiscriminatorEnum) -> IRSchema:
        """
        Create IRSchema for unified discriminator enum.

        Args:
            enum_metadata: UnifiedDiscriminatorEnum metadata

        Returns:
            IRSchema for the unified enum

        Contracts:
            Preconditions:
                - enum_metadata has name, values, and description
            Postconditions:
                - Returns valid IRSchema with enum values
                - generation_name and final_module_stem are set correctly
        """
        from pyopenapi_gen.core.utils import NameSanitizer

        # Extract enum values from metadata
        enum_values = [value for _, value in enum_metadata.values]

        # Infer type from first value
        first_value = enum_values[0] if enum_values else None
        enum_type = "integer" if isinstance(first_value, int) else "string"

        # Create the schema with generation metadata set
        schema = IRSchema(
            name=enum_metadata.name,
            type=enum_type,
            enum=enum_values,
            description=enum_metadata.description,
        )

        # Set generation_name and module_stem to prevent name collisions
        schema.generation_name = enum_metadata.name
        schema.final_module_stem = NameSanitizer.sanitize_module_name(enum_metadata.name)

        return schema

    def load_ir(self, naming_strategy: NamingStrategy = NamingStrategy.OPERATION_ID) -> IRSpec:
        """Transform the spec into an IRSpec object.

        Contracts:
            Postconditions:
                - Returns a fully populated IRSpec object
                - All schemas are properly processed and named
                - All operations are properly parsed and linked to schemas
                - Operation IDs follow the specified naming strategy
        """
        # First validate the spec
        self.validate()

        # Build schemas and create context
        context = build_schemas(self.raw_schemas, self.raw_components)

        # Parse operations
        operations = parse_operations(
            self.paths,
            self.raw_parameters,
            self.raw_responses,
            self.raw_request_bodies,
            context,
            naming_strategy=naming_strategy,
        )

        # Identify discriminator properties BEFORE inline enum extraction
        # This ensures we don't extract enums for properties that will be part of unified enums
        pre_collector = DiscriminatorEnumCollector(context.parsed_schemas)
        discriminator_properties = pre_collector.identify_discriminator_properties()

        # Extract inline enums and add them to the schemas map
        # Skip discriminator properties - they will be part of unified enums
        schemas_dict = extract_inline_enums(context.parsed_schemas, discriminator_properties)

        # Collect unified discriminator enums from discriminated unions
        discriminator_collector = DiscriminatorEnumCollector(schemas_dict)
        unified_enums = discriminator_collector.collect_unified_enums()

        # Add unified enums to schemas dict
        for enum_name, enum_metadata in unified_enums.items():
            unified_enum_schema = self._create_unified_enum_schema(enum_metadata)
            schemas_dict[enum_name] = unified_enum_schema
            logger.debug(f"Added unified discriminator enum '{enum_name}' to schemas")

        # Emit collected warnings after all parsing is done
        for warning_msg in context.collected_warnings:
            warnings.warn(warning_msg, UserWarning)

        # Create and return the IR spec
        ir_spec = IRSpec(
            title=self.title,
            version=self.version,
            description=self.description,
            schemas=schemas_dict,
            operations=operations,
            servers=self.servers,
            discriminator_skip_list=discriminator_collector.variant_enum_skip_list,
        )

        # Post-condition check
        if ir_spec.schemas != schemas_dict:
            raise RuntimeError("Schemas mismatch in IRSpec")
        if ir_spec.operations != operations:
            raise RuntimeError("Operations mismatch in IRSpec")

        return ir_spec


def load_ir_from_spec(
    spec: Mapping[str, Any],
    naming_strategy: NamingStrategy = NamingStrategy.OPERATION_ID,
) -> IRSpec:
    """Orchestrate the transformation of a spec dict into IRSpec.

    This is a convenience function that creates a SpecLoader and calls load_ir().

    Contracts:
        Preconditions:
            - spec is a valid OpenAPI spec mapping
        Postconditions:
            - Returns a fully populated IRSpec object
    """
    if not isinstance(spec, Mapping):
        raise ValueError("spec must be a Mapping")

    loader = SpecLoader(spec)
    return loader.load_ir(naming_strategy=naming_strategy)
