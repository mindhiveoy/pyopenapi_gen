"""Tests for enum handling in the schema resolver."""

from unittest.mock import Mock
import pytest
from pyopenapi_gen import IRSchema
from pyopenapi_gen.types.resolvers.schema_resolver import OpenAPISchemaResolver
from pyopenapi_gen.types.contracts.types import ResolvedType


class TestSchemaResolverEnums:
    """Test enum resolution in OpenAPISchemaResolver."""

    def test_resolve_string__top_level_enum_with_generation_name__returns_enum_type(self) -> None:
        """
        Scenario:
            A string schema with enum values and generation_name set (top-level enum).
        Expected Outcome:
            Returns the enum type name instead of plain string, no warning logged.
        """
        # Arrange
        ref_resolver = Mock()
        ref_resolver.schemas = {}
        resolver = OpenAPISchemaResolver(ref_resolver)
        
        enum_schema = IRSchema(
            name="UserRole",
            type="string",
            enum=["user", "admin", "system"],
            description="User role"
        )
        enum_schema.generation_name = "UserRole"
        enum_schema._is_top_level_enum = True
        
        context = Mock()
        context.add_import = Mock()
        
        # Act
        result = resolver._resolve_string(enum_schema, context, required=True)
        
        # Assert
        assert isinstance(result, ResolvedType)
        assert result.python_type == "UserRole"
        assert result.is_optional is False

    def test_resolve_string__top_level_enum_marked_but_no_generation_name__uses_name(self) -> None:
        """
        Scenario:
            A string schema marked as top-level enum but without generation_name.
        Expected Outcome:
            Falls back to using the schema name.
        """
        # Arrange
        ref_resolver = Mock()
        ref_resolver.schemas = {}
        resolver = OpenAPISchemaResolver(ref_resolver)
        
        enum_schema = IRSchema(
            name="TenantStatus",
            type="string",
            enum=["active", "inactive", "suspended"],
            description="Tenant status"
        )
        # Only marked as top-level, no generation_name
        enum_schema._is_top_level_enum = True
        
        context = Mock()
        context.add_import = Mock()
        
        # Act
        result = resolver._resolve_string(enum_schema, context, required=False)
        
        # Assert
        assert isinstance(result, ResolvedType)
        assert result.python_type == "TenantStatus"
        assert result.is_optional is True

    def test_resolve_string__inline_enum_without_promotion__returns_str_with_warning(self, caplog) -> None:
        """
        Scenario:
            A string schema with enum values but not promoted (no generation_name or marking).
        Expected Outcome:
            Returns plain str type and logs a warning.
        """
        # Arrange
        import logging
        
        ref_resolver = Mock()
        ref_resolver.schemas = {}
        resolver = OpenAPISchemaResolver(ref_resolver)
        
        enum_schema = IRSchema(
            name="SomeProperty",
            type="string",
            enum=["option1", "option2", "option3"],
            description="Some options"
        )
        # Not marked as top-level, no generation_name
        
        context = Mock()
        context.add_import = Mock()
        
        # Act - capture log warnings
        with caplog.at_level(logging.WARNING):
            result = resolver._resolve_string(enum_schema, context, required=True)
        
        # Assert
        assert isinstance(result, ResolvedType)
        assert result.python_type == "str"  # Falls back to str
        assert result.is_optional is False
        # Check that warning was logged
        assert len(caplog.records) > 0
        assert "Found inline enum" in caplog.text
        assert "SomeProperty" in caplog.text

    def test_resolve_string__unnamed_inline_enum__returns_str_with_warning(self) -> None:
        """
        Scenario:
            An unnamed string schema with enum values (truly inline).
        Expected Outcome:
            Returns plain str type and logs warning mentioning "unnamed".
        """
        # Arrange
        ref_resolver = Mock()
        ref_resolver.schemas = {}
        resolver = OpenAPISchemaResolver(ref_resolver)
        
        enum_schema = IRSchema(
            name=None,  # Unnamed
            type="string",
            enum=["red", "green", "blue"],
            description="Color options"
        )
        
        context = Mock()
        context.add_import = Mock()
        
        # Act
        result = resolver._resolve_string(enum_schema, context, required=True)
        
        # Assert
        assert isinstance(result, ResolvedType)
        assert result.python_type == "str"
        assert result.is_optional is False

    def test_resolve_string__regular_string_no_enum__returns_str(self) -> None:
        """
        Scenario:
            A regular string schema without enum values.
        Expected Outcome:
            Returns plain str type, no warnings.
        """
        # Arrange
        ref_resolver = Mock()
        ref_resolver.schemas = {}
        resolver = OpenAPISchemaResolver(ref_resolver)
        
        string_schema = IRSchema(
            name="Username",
            type="string",
            description="User's username"
        )
        
        context = Mock()
        context.add_import = Mock()
        
        # Act
        result = resolver._resolve_string(string_schema, context, required=True)
        
        # Assert
        assert isinstance(result, ResolvedType)
        assert result.python_type == "str"
        assert result.is_optional is False

    def test_resolve_string__string_with_format__returns_formatted_type(self) -> None:
        """
        Scenario:
            A string schema with format (e.g., date-time).
        Expected Outcome:
            Returns the appropriate formatted type.
        """
        # Arrange
        ref_resolver = Mock()
        ref_resolver.schemas = {}
        resolver = OpenAPISchemaResolver(ref_resolver)
        
        datetime_schema = IRSchema(
            name="CreatedAt",
            type="string",
            format="date-time",
            description="Creation timestamp"
        )
        
        context = Mock()
        context.add_import = Mock()
        
        # Act
        result = resolver._resolve_string(datetime_schema, context, required=True)
        
        # Assert
        assert isinstance(result, ResolvedType)
        assert result.python_type == "datetime"
        assert result.is_optional is False
        # Check that datetime import was added
        context.add_import.assert_called_with("datetime", "datetime")

    def test_resolve_schema__top_level_enum_via_main_path__handled_by_named_schema(self) -> None:
        """
        Scenario:
            A top-level enum schema resolved through the main resolve_schema method.
        Expected Outcome:
            Should be handled by _resolve_named_schema if it has generation_name.
        """
        # Arrange
        ref_resolver = Mock()
        ref_resolver.schemas = {}
        resolver = OpenAPISchemaResolver(ref_resolver)
        
        enum_schema = IRSchema(
            name="JobStatus",
            type="string",
            enum=["pending", "running", "completed", "failed"],
            description="Job status"
        )
        enum_schema.generation_name = "JobStatus"
        enum_schema.final_module_stem = "job_status"
        enum_schema._is_top_level_enum = True
        
        context = Mock()
        context.add_import = Mock()
        context.render_context = Mock()
        context.render_context.current_file = "endpoints/jobs.py"
        context.render_context.calculate_relative_path_for_internal_module = Mock(
            return_value="../models/job_status"
        )
        
        # Act
        result = resolver.resolve_schema(enum_schema, context, required=True)
        
        # Assert
        assert isinstance(result, ResolvedType)
        assert result.python_type == "JobStatus"
        assert result.is_optional is False
        # Should have added import
        context.add_import.assert_called_once()
        import_call_args = context.add_import.call_args[0]
        assert "job_status" in import_call_args[0]  # Import path contains module
        assert import_call_args[1] == "JobStatus"  # Import name