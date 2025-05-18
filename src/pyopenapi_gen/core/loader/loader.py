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

from pyopenapi_gen import IRSpec
from pyopenapi_gen.core.loader.operations import parse_operations
from pyopenapi_gen.core.loader.schemas import build_schemas, extract_inline_enums

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
                warnings_list.append(warning_msg)
                warnings.warn(warning_msg, UserWarning)

        return warnings_list

    def load_ir(self) -> IRSpec:
        """Transform the spec into an IRSpec object.

        Contracts:
            Postconditions:
                - Returns a fully populated IRSpec object
                - All schemas are properly processed and named
                - All operations are properly parsed and linked to schemas
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
        )

        # Extract inline enums and add them to the schemas map
        schemas_dict = extract_inline_enums(context.parsed_schemas)

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
        )

        # Post-condition check
        assert ir_spec.schemas == schemas_dict, "Schemas mismatch in IRSpec"
        assert ir_spec.operations == operations, "Operations mismatch in IRSpec"

        return ir_spec


def load_ir_from_spec(spec: Mapping[str, Any]) -> IRSpec:
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
    return loader.load_ir()
