"""
Field mapping utilities for converting between OpenAPI field names and Python field names.

This module provides utilities for handling field name conversions when generating
dataclasses with JSON serialization support using dataclass-wizard.
"""

import re
from typing import Any, Dict


class FieldMapper:
    """
    Utility class for handling field name mapping between API and Python conventions.

    This class helps generate appropriate field mappings for JSONWizard's
    key_transform_with_load configuration.
    """

    @staticmethod
    def camel_to_snake(name: str) -> str:
        """
        Convert camelCase to snake_case.

        Args:
            name: The camelCase string to convert

        Returns:
            The snake_case equivalent

        Examples:
            - "firstName" -> "first_name"
            - "userID" -> "user_id"
            - "XMLParser" -> "xml_parser"
        """
        # Handle acronyms and consecutive capitals
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    @staticmethod
    def requires_mapping(api_field: str, python_field: str) -> bool:
        """
        Check if a field name mapping is required.

        Args:
            api_field: The original API field name
            python_field: The Python field name (potentially sanitized)

        Returns:
            True if mapping is required, False otherwise
        """
        # Mapping required if names differ
        return api_field != python_field

    @staticmethod
    def generate_field_mappings(properties: Dict[str, Any], sanitized_names: Dict[str, str]) -> Dict[str, str]:
        """
        Generate field mappings for JSONWizard configuration.

        Args:
            properties: Dictionary of property names from the schema
            sanitized_names: Dictionary mapping original names to sanitized Python names

        Returns:
            Dictionary of mappings for JSONWizard's key_transform_with_load
        """
        mappings = {}

        for original_name in properties.keys():
            python_name = sanitized_names.get(original_name, original_name)

            if FieldMapper.requires_mapping(original_name, python_name):
                mappings[original_name] = python_name

        return mappings

    @staticmethod
    def has_any_mappings(properties: Dict[str, Any], sanitized_names: Dict[str, str]) -> bool:
        """
        Check if any field mappings are needed for the given properties.

        Args:
            properties: Dictionary of property names from the schema
            sanitized_names: Dictionary mapping original names to sanitized Python names

        Returns:
            True if any mappings are needed, False otherwise
        """
        return bool(FieldMapper.generate_field_mappings(properties, sanitized_names))
