"""
Collector for unifying discriminator enums in discriminated unions.

This module provides functionality to detect discriminated unions and collect
their discriminator property values into unified enum schemas, reducing code
bloat from multiple single-value enum classes.
"""

import logging
from dataclasses import dataclass
from typing import Any

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.utils import NameSanitizer

logger = logging.getLogger(__name__)


@dataclass
class UnifiedDiscriminatorEnum:
    """
    Metadata for a unified discriminator enum.

    Represents a single enum that combines all discriminator values from
    variants in a discriminated union.
    """

    name: str
    """Unified enum class name (e.g., 'NodeTypeEnum')"""

    property_name: str
    """Discriminator property name (e.g., 'type')"""

    union_schema_name: str
    """Name of the union schema (e.g., 'Node')"""

    values: list[tuple[str, Any]]
    """List of (member_name, value) tuples for enum members"""

    variant_enum_names: set[str]
    """Names of individual variant enums to skip generation"""

    description: str | None = None
    """Description for the unified enum"""


class DiscriminatorEnumCollector:
    """
    Collects and unifies discriminator enums from union variants.

    This class identifies discriminated unions in OpenAPI schemas and creates
    unified enum schemas that combine all discriminator values, eliminating
    the need for multiple single-value enum classes.

    Contracts:
        Post-conditions:
            - Discriminated unions result in unified enum schemas
            - Variant enum names are tracked in skip list
            - Non-discriminated schemas are unaffected
    """

    def __init__(self, schemas: dict[str, IRSchema]):
        """
        Initialise collector with all schemas.

        Args:
            schemas: Complete schema dictionary from parsing

        Contracts:
            Pre-conditions:
                - schemas is not None (can be empty dict)
            Post-conditions:
                - self.schemas is set
                - self.unified_enums is initialised as empty dict
                - self.variant_enum_skip_list is initialised as empty set
        """
        if schemas is None:
            raise ValueError("Schemas dictionary cannot be None")

        self.schemas = schemas
        self.unified_enums: dict[str, UnifiedDiscriminatorEnum] = {}
        self.variant_enum_skip_list: set[str] = set()

    def identify_discriminator_properties(self) -> set[tuple[str, str]]:
        """
        Identify discriminator properties before enum extraction.

        Returns a set of (variant_schema_name, property_name) tuples for properties
        that are discriminators in discriminated unions. These properties should NOT
        have their enums extracted inline as they will be part of unified enums.

        Returns:
            Set of (schema_name, property_name) tuples identifying discriminator properties

        Contracts:
            Post-conditions:
                - Returns set of discriminator property identifiers
                - Non-discriminated unions are ignored
        """
        discriminator_properties: set[tuple[str, str]] = set()

        for schema in self.schemas.values():
            if not self._is_discriminated_union(schema):
                continue

            discriminator = schema.discriminator
            if not discriminator or not discriminator.property_name:
                continue

            property_name = discriminator.property_name
            variants = schema.one_of or schema.any_of or []

            # Mark the discriminator property in all variants
            for variant in variants:
                variant_schema = self._resolve_variant_schema(variant)
                if not variant_schema:
                    continue

                # Add variant schema + property name to skip set
                if hasattr(variant_schema, "name") and variant_schema.name:
                    discriminator_properties.add((variant_schema.name, property_name))

        logger.debug(
            f"DiscriminatorEnumCollector: Identified {len(discriminator_properties)} "
            f"discriminator properties to skip during inline enum extraction."
        )

        return discriminator_properties

    def collect_unified_enums(self) -> dict[str, UnifiedDiscriminatorEnum]:
        """
        Find all discriminated unions and create unified enums.

        Iterates through all schemas, identifies discriminated unions,
        and creates unified enum metadata for each one.

        Returns:
            Dictionary mapping unified enum names to their metadata

        Contracts:
            Post-conditions:
                - Returns dict of unified enum metadata
                - self.variant_enum_skip_list is populated with variant enum names
                - Non-discriminated unions are not processed
        """
        # Use list() to create snapshot since we may modify schemas dict during iteration
        for schema_name, schema in list(self.schemas.items()):
            if self._is_discriminated_union(schema):
                try:
                    self._process_discriminated_union(schema)
                except Exception as e:
                    logger.warning(f"Failed to process discriminated union '{schema_name}': {e}. Skipping.")
                    continue

        logger.debug(
            f"DiscriminatorEnumCollector: Created {len(self.unified_enums)} unified enums, "
            f"marked {len(self.variant_enum_skip_list)} variant enums for skipping."
        )

        return self.unified_enums

    def should_skip_enum(self, enum_name: str) -> bool:
        """
        Check if an enum should be skipped (is variant enum).

        Args:
            enum_name: Name of enum to check

        Returns:
            True if enum is a variant enum and should not be generated

        Contracts:
            Pre-conditions:
                - enum_name is not None
        """
        if enum_name is None:
            return False
        return enum_name in self.variant_enum_skip_list

    def _is_discriminated_union(self, schema: IRSchema) -> bool:
        """
        Check if schema is a discriminated union.

        Args:
            schema: Schema to check

        Returns:
            True if schema has discriminator and oneOf/anyOf

        Contracts:
            Pre-conditions:
                - schema is not None
        """
        if schema is None:
            return False

        return bool(schema.discriminator and schema.discriminator.property_name and (schema.one_of or schema.any_of))

    def _process_discriminated_union(self, union_schema: IRSchema) -> None:
        """
        Process a single discriminated union.

        Steps:
        1. Get discriminator property name
        2. Iterate through variant schemas
        3. Collect discriminator values from each variant
        4. Create unified enum
        5. Mark variant enums for skipping

        Args:
            union_schema: The discriminated union schema

        Contracts:
            Pre-conditions:
                - union_schema has discriminator
                - union_schema has oneOf or anyOf
            Post-conditions:
                - Unified enum added to self.unified_enums (if values collected)
                - Variant enum names added to self.variant_enum_skip_list
        """
        discriminator = union_schema.discriminator
        if not discriminator or not discriminator.property_name:
            return

        property_name = discriminator.property_name
        variants = union_schema.one_of or union_schema.any_of or []

        if not variants:
            logger.debug(f"DiscriminatorEnumCollector: Union '{union_schema.name}' has no variants. Skipping.")
            return

        # Build reverse mapping from variant schema names to discriminator values
        # This helps when property enums have been unified and we can't get the value from the property
        discriminator_value_by_variant: dict[str, str] = {}
        if discriminator.mapping:
            for disc_value, variant_ref in discriminator.mapping.items():
                variant_name = variant_ref.split("/")[-1]  # Extract schema name from $ref
                discriminator_value_by_variant[variant_name] = disc_value

        # Collect values
        enum_values: list[tuple[str, Any]] = []
        variant_enum_names: set[str] = set()

        for variant in variants:
            variant_schema = self._resolve_variant_schema(variant)
            if not variant_schema:
                continue

            # Get discriminator property from variant
            if not hasattr(variant_schema, "properties") or not variant_schema.properties:
                continue

            disc_property = variant_schema.properties.get(property_name)
            if not disc_property:
                logger.debug(
                    f"DiscriminatorEnumCollector: Variant '{variant_schema.name}' "
                    f"missing discriminator property '{property_name}'. Skipping variant."
                )
                continue

            # Resolve enum values - either inline or via reference
            resolved_enum_values: list[Any] | None = None
            resolved_enum_name: str | None = None

            # Check for inline enum values first
            if hasattr(disc_property, "enum") and disc_property.enum:
                resolved_enum_values = disc_property.enum
                if hasattr(disc_property, "name") and disc_property.name:
                    resolved_enum_name = disc_property.name
            # If no inline enum, check if property references an enum schema
            elif hasattr(disc_property, "_refers_to_schema") and disc_property._refers_to_schema is not None:
                referred_schema = disc_property._refers_to_schema
                if hasattr(referred_schema, "enum") and referred_schema.enum:
                    resolved_enum_values = referred_schema.enum
                    if hasattr(referred_schema, "name") and referred_schema.name:
                        resolved_enum_name = referred_schema.name
                    logger.debug(
                        f"DiscriminatorEnumCollector: Resolved enum values for discriminator property '{property_name}' "
                        f"in variant '{variant_schema.name}' via _refers_to_schema to '{referred_schema.name}'."
                    )
            # If still no resolved enum, try looking up by property name in schemas dict
            elif hasattr(disc_property, "name") and disc_property.name and disc_property.name in self.schemas:
                referred_schema = self.schemas[disc_property.name]
                if hasattr(referred_schema, "enum") and referred_schema.enum:
                    resolved_enum_values = referred_schema.enum
                    resolved_enum_name = referred_schema.name
                    logger.debug(
                        f"DiscriminatorEnumCollector: Resolved enum values for discriminator property '{property_name}' "
                        f"in variant '{variant_schema.name}' by looking up property name '{disc_property.name}' in schemas."
                    )

            # If still no resolved enum, use the discriminator mapping as fallback
            # This handles cases where the property enum was already unified by another discriminated union
            if not resolved_enum_values and variant_schema.name in discriminator_value_by_variant:
                disc_value = discriminator_value_by_variant[variant_schema.name]
                resolved_enum_values = [disc_value]
                logger.debug(
                    f"DiscriminatorEnumCollector: Resolved enum value for discriminator property '{property_name}' "
                    f"in variant '{variant_schema.name}' from discriminator mapping: '{disc_value}'."
                )

            # If still no enum values found, skip variant
            if not resolved_enum_values:
                logger.debug(
                    f"DiscriminatorEnumCollector: Discriminator property '{property_name}' "
                    f"in variant '{variant_schema.name}' has no enum values (inline or referenced). Skipping variant."
                )
                continue

            # Collect enum values
            for value in resolved_enum_values:
                member_name = self._generate_member_name(value)
                enum_values.append((member_name, value))

            # Track variant enum name for skipping
            if resolved_enum_name:
                variant_enum_names.add(resolved_enum_name)

        if not enum_values:
            logger.debug(
                f"DiscriminatorEnumCollector: No enum values collected for union '{union_schema.name}'. Skipping."
            )
            return

        # Create unified enum
        unified_name = self._generate_unified_enum_name(union_schema.name or "Union", property_name)

        unified_enum = UnifiedDiscriminatorEnum(
            name=unified_name,
            property_name=property_name,
            union_schema_name=union_schema.name or "Union",
            values=enum_values,
            variant_enum_names=variant_enum_names,
            description=f"Discriminator enum for {union_schema.name} union types." if union_schema.name else None,
        )

        self.unified_enums[unified_name] = unified_enum

        # Update variant schemas to reference the unified enum
        for variant in variants:
            variant_schema = self._resolve_variant_schema(variant)
            if not variant_schema or not hasattr(variant_schema, "properties"):
                continue

            disc_property = variant_schema.properties.get(property_name)
            if disc_property:
                # Track old generation_name so we can remove the schema
                old_generation_name = disc_property.generation_name
                if old_generation_name and old_generation_name in self.schemas:
                    # Remove the property schema from schemas dict
                    # It was registered during parsing but isn't needed
                    del self.schemas[old_generation_name]
                    variant_enum_names.add(old_generation_name)
                    logger.debug(
                        f"DiscriminatorEnumCollector: Removed property schema '{old_generation_name}' "
                        f"from variant '{variant_schema.name}' (will use unified enum '{unified_name}')"
                    )

                # Update the property to reference the unified enum
                disc_property.name = unified_name
                # Also update generation_name to match
                disc_property.generation_name = unified_name
                # Also update final_module_stem to match the unified enum's module
                # This ensures imports use the correct module path (e.g., tool_config_type_enum
                # instead of canvas_document_tool_config_type_enum)
                disc_property.final_module_stem = NameSanitizer.sanitize_module_name(unified_name)
                # Clear the enum values since they're now in the unified enum
                if hasattr(disc_property, "enum"):
                    disc_property.enum = None

        # Update the skip list one more time after removing schemas
        self.variant_enum_skip_list.update(variant_enum_names)

        logger.debug(
            f"DiscriminatorEnumCollector: Created unified enum '{unified_name}' "
            f"with {len(enum_values)} values for union '{union_schema.name}'. "
            f"Updated {len(variants)} variant schemas to reference it."
        )

    def _resolve_variant_schema(self, variant: IRSchema) -> IRSchema | None:
        """
        Resolve variant to actual schema (handle $ref).

        Args:
            variant: Variant schema (may be a reference)

        Returns:
            Resolved schema or None if not found

        Contracts:
            Pre-conditions:
                - variant is not None
        """
        if variant is None:
            return None

        # If variant has a name and it's in schemas, resolve it
        if hasattr(variant, "name") and variant.name and variant.name in self.schemas:
            return self.schemas[variant.name]

        # Otherwise return the variant itself (might be inline)
        return variant

    def _generate_unified_enum_name(self, union_name: str, property_name: str) -> str:
        """
        Generate name for unified enum.

        Pattern: {UnionName}{PropertyName}Enum
        Example: Node + type → NodeTypeEnum

        Args:
            union_name: Name of the union schema
            property_name: Name of the discriminator property

        Returns:
            Sanitised unified enum name

        Contracts:
            Pre-conditions:
                - union_name is not empty
                - property_name is not empty
            Post-conditions:
                - Returns valid Python identifier
                - Follows naming pattern
        """
        if not union_name or not property_name:
            raise ValueError("union_name and property_name cannot be empty")

        # Capitalise property name (first character only)
        prop_capitalized = (
            property_name[0].upper() + property_name[1:] if len(property_name) > 1 else property_name.upper()
        )

        # Remove "Enum" suffix from union name if present
        if union_name.endswith("Enum"):
            union_name = union_name[:-4]

        unified_name = f"{union_name}{prop_capitalized}Enum"
        return NameSanitizer.sanitize_class_name(unified_name)

    def _generate_member_name(self, value: Any) -> str:
        """
        Generate enum member name from value.

        Converts value to uppercase and replaces hyphens and spaces with underscores.

        Args:
            value: Enum value

        Returns:
            Valid Python identifier for enum member

        Contracts:
            Post-conditions:
                - Returns non-empty string
                - Returns valid Python identifier (uppercase)
        """
        # Convert to string and apply basic transformations
        member_name = str(value).upper().replace("-", "_").replace(" ", "_")

        # Note: For full compatibility with EnumGenerator naming logic,
        # we could import and reuse its methods. For now, this basic
        # implementation handles most common cases.
        # If needed, we can enhance this to match EnumGenerator exactly.

        return member_name
