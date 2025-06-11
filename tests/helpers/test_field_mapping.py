"""
Unit tests for field mapping utilities.

Scenario: Test the FieldMapper utility class for handling field name conversions
between API conventions and Python conventions.

Expected Outcome: All mapping functions work correctly and handle edge cases.
"""

from pyopenapi_gen.helpers.field_mapping import FieldMapper


class TestFieldMapper:
    """Test the FieldMapper utility class."""

    def test_camel_to_snake__basic_conversion__converts_correctly(self):
        """
        Scenario: Convert basic camelCase strings to snake_case.
        Expected Outcome: Conversion follows standard conventions.
        """
        # Arrange & Act & Assert
        assert FieldMapper.camel_to_snake("firstName") == "first_name"
        assert FieldMapper.camel_to_snake("lastName") == "last_name"
        assert FieldMapper.camel_to_snake("emailAddress") == "email_address"

    def test_camel_to_snake__acronyms__handles_correctly(self):
        """
        Scenario: Convert camelCase with acronyms to snake_case.
        Expected Outcome: Acronyms are handled properly.
        """
        # Arrange & Act & Assert
        assert FieldMapper.camel_to_snake("userID") == "user_id"
        assert FieldMapper.camel_to_snake("XMLParser") == "xml_parser"
        assert FieldMapper.camel_to_snake("HTTPSUrl") == "https_url"

    def test_camel_to_snake__single_word__unchanged(self):
        """
        Scenario: Convert single word strings.
        Expected Outcome: Single words remain unchanged.
        """
        # Arrange & Act & Assert
        assert FieldMapper.camel_to_snake("name") == "name"
        assert FieldMapper.camel_to_snake("id") == "id"
        assert FieldMapper.camel_to_snake("status") == "status"

    def test_camel_to_snake__already_snake_case__unchanged(self):
        """
        Scenario: Convert strings already in snake_case.
        Expected Outcome: No change needed.
        """
        # Arrange & Act & Assert
        assert FieldMapper.camel_to_snake("first_name") == "first_name"
        assert FieldMapper.camel_to_snake("user_id") == "user_id"

    def test_requires_mapping__different_names__returns_true(self):
        """
        Scenario: Check if mapping is required when names differ.
        Expected Outcome: Returns True when names are different.
        """
        # Arrange & Act & Assert
        assert FieldMapper.requires_mapping("firstName", "first_name") is True
        assert FieldMapper.requires_mapping("id", "id_") is True
        assert FieldMapper.requires_mapping("class", "class_") is True

    def test_requires_mapping__same_names__returns_false(self):
        """
        Scenario: Check if mapping is required when names are the same.
        Expected Outcome: Returns False when names are identical.
        """
        # Arrange & Act & Assert
        assert FieldMapper.requires_mapping("name", "name") is False
        assert FieldMapper.requires_mapping("status", "status") is False

    def test_generate_field_mappings__mixed_fields__creates_correct_mappings(self):
        """
        Scenario: Generate mappings for a mix of fields requiring and not requiring mapping.
        Expected Outcome: Only fields that need mapping are included.
        """
        # Arrange
        properties = {
            "firstName": {"type": "string"},
            "lastName": {"type": "string"},
            "name": {"type": "string"},
            "id": {"type": "string"},
            "status": {"type": "string"},
        }
        sanitized_names = {
            "firstName": "first_name",
            "lastName": "last_name",
            "name": "name",
            "id": "id_",
            "status": "status",
        }

        # Act
        mappings = FieldMapper.generate_field_mappings(properties, sanitized_names)

        # Assert
        expected_mappings = {"firstName": "first_name", "lastName": "last_name", "id": "id_"}
        assert mappings == expected_mappings

    def test_generate_field_mappings__no_mappings_needed__returns_empty(self):
        """
        Scenario: Generate mappings when no fields require mapping.
        Expected Outcome: Returns empty dictionary.
        """
        # Arrange
        properties = {"name": {"type": "string"}, "status": {"type": "string"}}
        sanitized_names = {"name": "name", "status": "status"}

        # Act
        mappings = FieldMapper.generate_field_mappings(properties, sanitized_names)

        # Assert
        assert mappings == {}

    def test_has_any_mappings__with_mappings__returns_true(self):
        """
        Scenario: Check if any mappings are needed when some fields require mapping.
        Expected Outcome: Returns True.
        """
        # Arrange
        properties = {"firstName": {"type": "string"}, "name": {"type": "string"}}
        sanitized_names = {"firstName": "first_name", "name": "name"}

        # Act & Assert
        assert FieldMapper.has_any_mappings(properties, sanitized_names) is True

    def test_has_any_mappings__no_mappings__returns_false(self):
        """
        Scenario: Check if any mappings are needed when no fields require mapping.
        Expected Outcome: Returns False.
        """
        # Arrange
        properties = {"name": {"type": "string"}, "status": {"type": "string"}}
        sanitized_names = {"name": "name", "status": "status"}

        # Act & Assert
        assert FieldMapper.has_any_mappings(properties, sanitized_names) is False

    def test_generate_field_mappings__empty_inputs__returns_empty(self):
        """
        Scenario: Generate mappings with empty inputs.
        Expected Outcome: Returns empty dictionary.
        """
        # Arrange & Act
        mappings = FieldMapper.generate_field_mappings({}, {})

        # Assert
        assert mappings == {}
