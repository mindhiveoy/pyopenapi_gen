"""End-to-end test for dataclass serialization in generated clients.

Scenario: Test actual code generation for endpoints with dataclass body parameters
to ensure the DataclassSerializer is properly integrated.

Expected Outcome: Generated endpoint methods include DataclassSerializer calls
and proper imports for seamless dataclass handling.
"""

from unittest.mock import MagicMock

import pytest
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.ir import IROperation, IRRequestBody, IRSchema
from pyopenapi_gen.visit.endpoint.generators.endpoint_method_generator import EndpointMethodGenerator


class TestDataclassSerializationEndToEnd:
    """Test end-to-end dataclass serialization in generated endpoint methods."""

    def test_generate_endpoint_with_json_body__includes_serializer__complete_method(self) -> None:
        """
        Scenario: Generate complete endpoint method with JSON body parameter
        Expected Outcome: Generated code includes DataclassSerializer import and usage
        """
        # Arrange
        operation = IROperation(
            operation_id="create_user",
            summary="Create a new user",
            description="Creates a new user with the provided data.",
            method=HTTPMethod.POST,
            path="/users",
            tags=["users"],
            parameters=[],
            request_body=IRRequestBody(
                description="User data",
                content={
                    "application/json": IRSchema(type="CreateUserRequest", description="User creation data")
                },
                required=True,
            ),
            responses=[],
        )
        
        # Mock render context
        context = MagicMock(spec=RenderContext)
        context.core_package_name = "test_core"
        context.add_import = MagicMock()
        context.add_typing_imports_for_type = MagicMock()
        
        # Create generator
        generator = EndpointMethodGenerator()

        # Act
        generated_code = generator.generate(operation, context)

        # Assert
        # Check that the generated code includes DataclassSerializer
        assert "DataclassSerializer.serialize" in generated_code
        
        # Check that the import was added
        context.add_import.assert_any_call("test_core.utils", "DataclassSerializer")
        
        # Check that the generated code structure is correct
        assert "async def create_user" in generated_code
        assert "json_body:" in generated_code
        assert "= DataclassSerializer.serialize(body)" in generated_code
        
        # Verify the JSON body assignment pattern
        lines = generated_code.split('\n')
        json_body_lines = [line for line in lines if "json_body:" in line and "DataclassSerializer" in line]
        assert len(json_body_lines) == 1, f"Expected exactly one json_body assignment, got: {json_body_lines}"
        
        # Verify the pattern matches our expected format
        json_body_line = json_body_lines[0].strip()
        assert "DataclassSerializer.serialize(body)" in json_body_line

    def test_generate_endpoint_without_body__no_serializer__clean_method(self) -> None:
        """
        Scenario: Generate endpoint method without body parameter (GET request)
        Expected Outcome: Generated code does not include DataclassSerializer
        """
        # Arrange
        operation = IROperation(
            operation_id="get_users",
            summary="Get all users",
            description="Retrieves a list of all users.",
            method=HTTPMethod.GET,
            path="/users",
            tags=["users"],
            parameters=[],
            request_body=None,
            responses=[],
        )
        
        # Mock render context
        context = MagicMock(spec=RenderContext)
        context.core_package_name = "test_core"
        context.add_import = MagicMock()
        context.add_typing_imports_for_type = MagicMock()
        
        # Create generator
        generator = EndpointMethodGenerator()

        # Act
        generated_code = generator.generate(operation, context)

        # Assert
        # Check that the generated code does NOT include DataclassSerializer
        assert "DataclassSerializer" not in generated_code
        
        # Check that the import was NOT added
        import_calls = context.add_import.call_args_list
        serializer_imports = [
            call for call in import_calls 
            if len(call[0]) >= 2 and "DataclassSerializer" in str(call[0][1])
        ]
        assert len(serializer_imports) == 0, "DataclassSerializer should not be imported for bodyless requests"
        
        # Check basic structure
        assert "async def get_users" in generated_code
        assert "json_body" not in generated_code

    def test_generated_code_formatting__preserves_style__clean_output(self) -> None:
        """
        Scenario: Verify that generated code with DataclassSerializer maintains proper formatting
        Expected Outcome: Generated code is properly formatted with correct indentation and structure
        """
        # Arrange
        operation = IROperation(
            operation_id="update_user",
            summary="Update a user",
            description="Updates an existing user with new data.",
            method=HTTPMethod.PUT,
            path="/users/{user_id}",
            tags=["users"],
            parameters=[],
            request_body=IRRequestBody(
                description="Updated user data",
                content={
                    "application/json": IRSchema(type="UpdateUserRequest", description="User update data")
                },
                required=True,
            ),
            responses=[],
        )
        
        context = MagicMock(spec=RenderContext)
        context.core_package_name = "test_core"
        context.add_import = MagicMock()
        context.add_typing_imports_for_type = MagicMock()
        
        generator = EndpointMethodGenerator()

        # Act
        generated_code = generator.generate(operation, context)

        # Assert
        # Check that the code is properly formatted
        lines = generated_code.split('\n')
        
        # Find the json_body assignment line
        json_body_lines = [line for line in lines if "json_body:" in line and "DataclassSerializer" in line]
        assert len(json_body_lines) == 1
        
        json_body_line = json_body_lines[0]
        
        # Check proper indentation (should have some leading whitespace)
        assert json_body_line.startswith('    '), f"Expected indentation, got: '{json_body_line}'"
        
        # Check the pattern is correct
        assert "= DataclassSerializer.serialize(body)" in json_body_line
        
        # Verify no trailing whitespace issues
        assert not json_body_line.endswith(' '), f"Unexpected trailing whitespace: '{json_body_line}'"