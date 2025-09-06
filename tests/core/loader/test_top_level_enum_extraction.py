"""Tests for top-level enum schema extraction and promotion."""

import pytest
from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.loader.schemas.extractor import extract_inline_enums


class TestTopLevelEnumExtraction:
    """Test extraction and promotion of top-level enum schemas."""

    def test_extract_inline_enums__top_level_string_enum__sets_generation_name(self) -> None:
        """
        Scenario:
            A top-level schema is defined as an enum (like UserRole, TenantStatus in OpenAPI).
        Expected Outcome:
            The schema gets generation_name set and is marked as a top-level enum.
        """
        # Arrange
        user_role_schema = IRSchema(
            name="UserRole",
            type="string",
            enum=["user", "admin", "system"],
            description="User role enumeration"
        )
        schemas = {"UserRole": user_role_schema}
        
        # Act
        result = extract_inline_enums(schemas)
        
        # Assert
        assert "UserRole" in result
        user_role = result["UserRole"]
        # Check that generation_name was set
        assert hasattr(user_role, 'generation_name')
        assert user_role.generation_name == "UserRole"
        # Check that it was marked as top-level enum
        assert hasattr(user_role, '_is_top_level_enum')
        assert user_role._is_top_level_enum is True
        # Enum values should remain
        assert user_role.enum == ["user", "admin", "system"]
        assert user_role.type == "string"

    def test_extract_inline_enums__top_level_integer_enum__sets_generation_name(self) -> None:
        """
        Scenario:
            A top-level schema is defined as an integer enum.
        Expected Outcome:
            The schema gets generation_name set and is marked as a top-level enum.
        """
        # Arrange
        priority_schema = IRSchema(
            name="Priority",
            type="integer",
            enum=[1, 2, 3, 4, 5],
            description="Priority levels"
        )
        schemas = {"Priority": priority_schema}
        
        # Act
        result = extract_inline_enums(schemas)
        
        # Assert
        assert "Priority" in result
        priority = result["Priority"]
        assert hasattr(priority, 'generation_name')
        assert priority.generation_name == "Priority"
        assert hasattr(priority, '_is_top_level_enum')
        assert priority._is_top_level_enum is True
        assert priority.enum == [1, 2, 3, 4, 5]
        assert priority.type == "integer"

    def test_extract_inline_enums__top_level_enum_with_existing_generation_name__preserves_it(self) -> None:
        """
        Scenario:
            A top-level enum schema already has generation_name set (e.g., from emitter).
        Expected Outcome:
            The existing generation_name is preserved.
        """
        # Arrange
        status_schema = IRSchema(
            name="Status",
            type="string",
            enum=["active", "inactive", "pending"],
            description="Status enumeration"
        )
        # Simulate emitter already setting generation_name
        status_schema.generation_name = "StatusEnum"
        schemas = {"Status": status_schema}
        
        # Act
        result = extract_inline_enums(schemas)
        
        # Assert
        assert "Status" in result
        status = result["Status"]
        # Should preserve the existing generation_name
        assert status.generation_name == "StatusEnum"
        assert hasattr(status, '_is_top_level_enum')
        assert status._is_top_level_enum is True

    def test_extract_inline_enums__mixed_top_level_and_inline_enums__processes_both(self) -> None:
        """
        Scenario:
            Mix of top-level enum schemas and schemas with inline enum properties.
        Expected Outcome:
            Top-level enums get generation_name set, inline enums are extracted.
        """
        # Arrange
        # Top-level enum
        role_schema = IRSchema(
            name="Role",
            type="string",
            enum=["viewer", "editor", "owner"],
            description="Access role"
        )
        
        # Schema with inline enum property
        inline_enum_property = IRSchema(
            name=None,
            type="string",
            enum=["draft", "published", "archived"],
            description="Document status"
        )
        document_schema = IRSchema(
            name="Document",
            type="object",
            properties={"status": inline_enum_property}
        )
        
        schemas = {
            "Role": role_schema,
            "Document": document_schema
        }
        
        # Act
        result = extract_inline_enums(schemas)
        
        # Assert
        # Top-level enum should be marked
        assert "Role" in result
        role = result["Role"]
        assert hasattr(role, 'generation_name')
        assert role.generation_name == "Role"
        assert hasattr(role, '_is_top_level_enum')
        assert role._is_top_level_enum is True
        
        # Inline enum should be extracted
        assert "DocumentStatusEnum" in result
        extracted_enum = result["DocumentStatusEnum"]
        assert extracted_enum.enum == ["draft", "published", "archived"]
        assert extracted_enum.generation_name == "DocumentStatusEnum"
        
        # Document property should reference the extracted enum
        document = result["Document"]
        assert document.properties["status"].name == "DocumentStatusEnum"
        assert document.properties["status"].type == "DocumentStatusEnum"
        assert document.properties["status"].enum is None

    def test_extract_inline_enums__object_type_with_enum__not_marked_as_enum(self) -> None:
        """
        Scenario:
            A schema with type="object" that somehow has enum values (invalid).
        Expected Outcome:
            Not marked as a top-level enum since it's not a valid enum type.
        """
        # Arrange
        invalid_schema = IRSchema(
            name="InvalidEnum",
            type="object",
            enum=["should", "not", "work"],  # Invalid: objects shouldn't have enum
            properties={}
        )
        schemas = {"InvalidEnum": invalid_schema}
        
        # Act
        result = extract_inline_enums(schemas)
        
        # Assert
        assert "InvalidEnum" in result
        invalid = result["InvalidEnum"]
        # Should NOT be marked as top-level enum
        assert not hasattr(invalid, '_is_top_level_enum') or not invalid._is_top_level_enum
        # generation_name might not be set
        if hasattr(invalid, 'generation_name'):
            # Even if set, it shouldn't be treated as enum
            assert invalid.type == "object"

    def test_extract_inline_enums__number_type_enum__sets_generation_name(self) -> None:
        """
        Scenario:
            A top-level schema is defined as a number (float) enum.
        Expected Outcome:
            The schema gets generation_name set and is marked as a top-level enum.
        """
        # Arrange
        rating_schema = IRSchema(
            name="Rating",
            type="number",
            enum=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
            description="Rating values"
        )
        schemas = {"Rating": rating_schema}
        
        # Act
        result = extract_inline_enums(schemas)
        
        # Assert
        assert "Rating" in result
        rating = result["Rating"]
        assert hasattr(rating, 'generation_name')
        assert rating.generation_name == "Rating"
        assert hasattr(rating, '_is_top_level_enum')
        assert rating._is_top_level_enum is True
        assert rating.type == "number"