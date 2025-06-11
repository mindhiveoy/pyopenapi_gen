"""Tests to verify that the response handler generator produces clean match-case statements.

Scenario: Test that the refactored response handler generates modern Python match-case
syntax instead of verbose if-elif-else chains.

Expected Outcome: Generated code uses match-case for cleaner, more readable response handling.
"""

from unittest.mock import MagicMock

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.ir import IROperation, IRResponse, IRSchema
from pyopenapi_gen.types.strategies.response_strategy import ResponseStrategy
from pyopenapi_gen.visit.endpoint.generators.response_handler_generator import EndpointResponseHandlerGenerator


class TestMatchCaseResponseGeneration:
    """Test that response handlers generate match-case statements."""

    def test_generate_multiple_status_codes__uses_match_case__clean_syntax(self) -> None:
        """
        Scenario: Generate response handling for multiple status codes
        Expected Outcome: Uses match-case syntax instead of if-elif-else chains
        """
        # Arrange
        success_schema = IRSchema(type="object", name="User")
        error_schema = IRSchema(type="object", name="ErrorResponse")

        operation = IROperation(
            operation_id="get_user",
            summary="Get user by ID",
            description="Retrieves a user by their ID",
            method=HTTPMethod.GET,
            path="/users/{user_id}",
            tags=["users"],
            parameters=[],
            request_body=None,
            responses=[
                IRResponse(status_code="200", description="Success", content={"application/json": success_schema}),
                IRResponse(status_code="400", description="Bad Request", content={"application/json": error_schema}),
                IRResponse(status_code="401", description="Unauthorized", content={}),
                IRResponse(status_code="404", description="Not Found", content={}),
                IRResponse(status_code="500", description="Internal Server Error", content={}),
            ],
        )

        context = MagicMock(spec=RenderContext)
        context.core_package_name = "test_core"
        context.add_import = MagicMock()
        context.add_typing_imports_for_type = MagicMock()

        writer = CodeWriter()
        generator = EndpointResponseHandlerGenerator()

        # Create a ResponseStrategy for the 200 response
        strategy = ResponseStrategy(
            return_type="User",
            response_schema=success_schema,
            is_streaming=False,
            response_ir=operation.responses[0],  # 200 response
        )

        # Act
        generator.generate_response_handling(writer, operation, context, strategy)

        # Assert
        generated_code = writer.get_code()

        # Should use match statement
        assert "match response.status_code:" in generated_code

        # Should have individual case statements for each status code
        assert "case 200:" in generated_code
        assert "case 400:" in generated_code
        assert "case 401:" in generated_code
        assert "case 404:" in generated_code
        assert "case 500:" in generated_code

        # Should have fallback case
        assert "case _:" in generated_code

        # Should NOT use if-elif-else patterns
        assert "if response.status_code ==" not in generated_code
        assert "elif response.status_code ==" not in generated_code

        # Should have proper error raising
        assert "raise Error400(response=response)" in generated_code
        assert "raise Error401(response=response)" in generated_code
        assert "raise Error404(response=response)" in generated_code
        assert "raise Error500(response=response)" in generated_code

        # Should have HTTPError for unhandled cases
        assert 'raise HTTPError(response=response, message="Unhandled status code"' in generated_code

    def test_generated_code_structure__matches_desired_format__readable_output(self) -> None:
        """
        Scenario: Verify the exact structure of generated match-case code
        Expected Outcome: Generated code follows the clean pattern shown in the user's example
        """
        # Arrange
        schema = IRSchema(type="object", name="Chat")

        operation = IROperation(
            operation_id="create_chat",
            summary="Create chat",
            description="Creates a new chat",
            method=HTTPMethod.POST,
            path="/chats",
            tags=["chats"],
            parameters=[],
            request_body=None,
            responses=[
                IRResponse(status_code="201", description="Created", content={"application/json": schema}),
                IRResponse(status_code="400", description="Bad Request", content={}),
                IRResponse(status_code="401", description="Unauthorized", content={}),
                IRResponse(status_code="403", description="Forbidden", content={}),
                IRResponse(status_code="404", description="Not Found", content={}),
                IRResponse(status_code="500", description="Server Error", content={}),
            ],
        )

        context = MagicMock(spec=RenderContext)
        context.core_package_name = "test_core"
        context.add_import = MagicMock()
        context.add_typing_imports_for_type = MagicMock()

        writer = CodeWriter()
        generator = EndpointResponseHandlerGenerator()

        # Create a ResponseStrategy for the 201 response
        strategy = ResponseStrategy(
            return_type="Chat",
            response_schema=schema,
            is_streaming=False,
            response_ir=operation.responses[0],  # 201 response
        )

        # Act
        generator.generate_response_handling(writer, operation, context, strategy)

        # Assert
        generated_code = writer.get_code()
        lines = generated_code.split("\n")

        # Find the match statement
        match_line_idx = None
        for i, line in enumerate(lines):
            if "match response.status_code:" in line:
                match_line_idx = i
                break

        assert match_line_idx is not None, "Should contain match statement"

        # Verify structure after match statement
        remaining_lines = lines[match_line_idx:]
        match_content = "\n".join(remaining_lines)

        # Should follow the pattern:
        # match response.status_code:
        #     case 201:
        #         # success handling
        #     case 400:
        #         raise Error400(response=response)
        #     case 401:
        #         raise Error401(response=response)
        #     etc.

        assert "case 201:" in match_content
        assert "case 400:" in match_content
        assert "case 401:" in match_content
        assert "case 403:" in match_content
        assert "case 404:" in match_content
        assert "case 500:" in match_content
        assert "case _:" in match_content  # catch-all

        # Verify no unwrapping code appears (since no data wrapper expected)
        assert 'raw_data = response.json().get("data")' not in match_content

        # Should have clean return for success case (now uses BaseSchema)
        assert "return Chat.from_dict(response.json())" in match_content

    def test_default_response_handling__uses_conditional_case__handles_catch_all(self) -> None:
        """
        Scenario: Test handling of 'default' responses with match-case
        Expected Outcome: Uses conditional case pattern for default responses
        """
        # Arrange
        operation = IROperation(
            operation_id="get_data",
            summary="Get data",
            description="Get some data",
            method=HTTPMethod.GET,
            path="/data",
            tags=["data"],
            parameters=[],
            request_body=None,
            responses=[
                IRResponse(
                    status_code="200",
                    description="OK",
                    content={"application/json": IRSchema(type="object", name="Data")},
                ),
                IRResponse(status_code="default", description="Error", content={}),
            ],
        )

        context = MagicMock(spec=RenderContext)
        context.core_package_name = "test_core"
        context.add_import = MagicMock()
        context.add_typing_imports_for_type = MagicMock()

        writer = CodeWriter()
        generator = EndpointResponseHandlerGenerator()

        # Create a ResponseStrategy for the 200 response
        data_schema = IRSchema(type="object", name="Data")
        strategy = ResponseStrategy(
            return_type="Data",
            response_schema=data_schema,
            is_streaming=False,
            response_ir=operation.responses[0],  # 200 response
        )

        # Act
        generator.generate_response_handling(writer, operation, context, strategy)

        # Assert
        generated_code = writer.get_code()

        # Should use match statement
        assert "match response.status_code:" in generated_code
        assert "case 200:" in generated_code

        # Should handle default case appropriately
        assert "case _:" in generated_code  # Default case without content becomes catch-all

        # Should not use if-elif patterns
        assert "if response.status_code ==" not in generated_code
        assert "elif response.status_code ==" not in generated_code
