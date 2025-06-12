"""Tests for EndpointResponseHandlerGenerator with ResponseStrategy pattern."""

from unittest.mock import MagicMock

import pytest

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.ir import IROperation, IRResponse, IRSchema
from pyopenapi_gen.types.strategies.response_strategy import ResponseStrategy
from pyopenapi_gen.visit.endpoint.generators.response_handler_generator import EndpointResponseHandlerGenerator


class TestEndpointResponseHandlerGeneratorWithStrategy:
    """Test the response handler generator with the new ResponseStrategy pattern."""

    @pytest.fixture
    def render_context_mock(self):
        """Mock render context."""
        context = MagicMock(spec=RenderContext)
        context.import_collector = MagicMock()
        context.import_collector._current_file_module_dot_path = "some.dummy.path"
        context.name_sanitizer = MagicMock()
        context.core_package_name = "test_client.core"
        return context

    @pytest.fixture
    def code_writer_mock(self):
        """Mock code writer."""
        return MagicMock(spec=CodeWriter)

    @pytest.fixture
    def generator(self):
        """Response handler generator instance."""
        return EndpointResponseHandlerGenerator()

    def test_generate_response_handling__direct_model_response__generates_baseschema_call(
        self, generator, code_writer_mock, render_context_mock
    ) -> None:
        """
        Scenario: Direct model response without unwrapping
        Expected Outcome: Generates BaseSchema.from_dict call for the model
        """
        # Arrange
        success_schema = IRSchema(type="object", name="User")
        operation = IROperation(
            operation_id="get_user",
            method=HTTPMethod.GET,
            path="/users/{id}",
            responses=[
                IRResponse(
                    status_code="200",
                    description="User response",
                    content={"application/json": success_schema},
                )
            ],
            summary="get user",
            description="get user",
        )

        strategy = ResponseStrategy(
            return_type="User", response_schema=success_schema, is_streaming=False, response_ir=operation.responses[0]
        )

        render_context_mock.name_sanitizer.sanitize_class_name.return_value = "User"

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        assert "match response.status_code:" in written_code
        assert "case 200:" in written_code
        assert any(
            c[0][0].strip() == "return User.from_dict(response.json())"
            for c in code_writer_mock.write_line.call_args_list
        )

    def test_generate_response_handling__wrapper_schema_response__uses_schema_as_is(
        self, generator, code_writer_mock, render_context_mock
    ) -> None:
        """
        Scenario: Response with wrapper schema containing data field
        Expected Outcome: Uses the wrapper schema as-is, no unwrapping (matches OpenAPI spec exactly)
        """
        # Arrange
        user_schema = IRSchema(type="object", name="User")
        wrapper_schema = IRSchema(type="object", name="UserResponse", properties={"data": user_schema})

        operation = IROperation(
            operation_id="get_user_wrapped",
            method=HTTPMethod.GET,
            path="/users/{id}",
            responses=[
                IRResponse(
                    status_code="200",
                    description="Wrapped user response",
                    content={"application/json": wrapper_schema},
                )
            ],
            summary="get user wrapped",
            description="get user wrapped",
        )

        strategy = ResponseStrategy(
            return_type="UserResponse",
            response_schema=wrapper_schema,
            is_streaming=False,
            response_ir=operation.responses[0],
        )

        render_context_mock.name_sanitizer.sanitize_class_name.return_value = "UserResponse"

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        assert "match response.status_code:" in written_code
        assert "case 200:" in written_code
        # Should use the wrapper schema as-is (no unwrapping)
        assert "return UserResponse.from_dict(response.json())" in written_code
        # Should NOT contain unwrapping logic
        assert "raw_data = response.json().get('data')" not in written_code

    def test_generate_response_handling__none_return_type__generates_return_none(
        self, generator, code_writer_mock, render_context_mock
    ) -> None:
        """
        Scenario: Operation returns None (e.g., DELETE with 204)
        Expected Outcome: Generates simple return None
        """
        # Arrange
        operation = IROperation(
            operation_id="delete_user",
            method=HTTPMethod.DELETE,
            path="/users/{id}",
            responses=[IRResponse(status_code="204", description="No Content", content={})],
            summary="delete user",
            description="delete user",
        )

        strategy = ResponseStrategy(
            return_type="None", response_schema=None, is_streaming=False, response_ir=operation.responses[0]
        )

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        assert "match response.status_code:" in written_code
        assert "case 204:" in written_code
        assert any(c[0][0].strip() == "return None" for c in code_writer_mock.write_line.call_args_list)

    def test_generate_response_handling__streaming_response__generates_async_generator(
        self, generator, code_writer_mock, render_context_mock
    ) -> None:
        """
        Scenario: Streaming response that yields data
        Expected Outcome: Generates async generator with yield statements
        """
        # Arrange
        operation = IROperation(
            operation_id="stream_events",
            method=HTTPMethod.GET,
            path="/events/stream",
            responses=[
                IRResponse(
                    status_code="200",
                    description="Event stream",
                    content={"text/event-stream": IRSchema(type="object")},
                    stream=True,
                )
            ],
            summary="stream events",
            description="stream events",
        )

        strategy = ResponseStrategy(
            return_type="AsyncIterator[Dict[str, Any]]",
            response_schema=IRSchema(type="object"),
            is_streaming=True,
            response_ir=operation.responses[0],
        )

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        assert "match response.status_code:" in written_code
        assert "case 200:" in written_code
        assert "async for" in written_code
        assert "yield" in written_code

    def test_generate_response_handling__binary_streaming__generates_bytes_iterator(
        self, generator, code_writer_mock, render_context_mock
    ) -> None:
        """
        Scenario: Binary streaming response
        Expected Outcome: Generates async iterator yielding bytes
        """
        # Arrange
        operation = IROperation(
            operation_id="download_file",
            method=HTTPMethod.GET,
            path="/files/{id}/download",
            responses=[
                IRResponse(
                    status_code="200",
                    description="File download",
                    content={"application/octet-stream": IRSchema(type="string", format="binary")},
                    stream=True,
                )
            ],
            summary="download file",
            description="download file",
        )

        strategy = ResponseStrategy(
            return_type="AsyncIterator[bytes]",
            response_schema=IRSchema(type="string", format="binary"),
            is_streaming=True,
            response_ir=operation.responses[0],
        )

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        assert "match response.status_code:" in written_code
        assert "case 200:" in written_code
        assert "iter_bytes" in written_code
        assert "yield chunk" in written_code

    def test_generate_response_handling__error_responses__generates_exception_raises(
        self, generator, code_writer_mock, render_context_mock
    ) -> None:
        """
        Scenario: Operation with error responses (404, 500)
        Expected Outcome: Generates specific error handling with exception raises
        """
        # Arrange
        operation = IROperation(
            operation_id="get_user_with_errors",
            method=HTTPMethod.GET,
            path="/users/{id}",
            responses=[
                IRResponse(
                    status_code="200",
                    description="Success",
                    content={"application/json": IRSchema(type="object", name="User")},
                ),
                IRResponse(status_code="404", description="Not Found", content={}),
                IRResponse(status_code="500", description="Server Error", content={}),
            ],
            summary="get user with errors",
            description="get user with errors",
        )

        strategy = ResponseStrategy(
            return_type="User",
            response_schema=IRSchema(type="object", name="User"),
            is_streaming=False,
            response_ir=operation.responses[0],  # Primary success response
        )

        render_context_mock.name_sanitizer.sanitize_class_name.return_value = "User"

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        assert "match response.status_code:" in written_code
        assert "case 200:" in written_code
        assert "case 404:" in written_code
        assert "case 500:" in written_code
        assert "raise Error404" in written_code
        assert "raise Error500" in written_code

    def test_generate_response_handling__union_return_type__generates_fallback_parsing(
        self, generator, code_writer_mock, render_context_mock
    ) -> None:
        """
        Scenario: Union return type that could be multiple models
        Expected Outcome: Generates try/except logic for fallback parsing
        """
        # Arrange
        operation = IROperation(
            operation_id="get_polymorphic_data",
            method=HTTPMethod.GET,
            path="/data",
            responses=[
                IRResponse(
                    status_code="200",
                    description="Polymorphic data",
                    content={"application/json": IRSchema(type="object")},
                )
            ],
            summary="get polymorphic data",
            description="get polymorphic data",
        )

        strategy = ResponseStrategy(
            return_type="Union[ModelA, ModelB]",
            response_schema=IRSchema(type="object"),
            is_streaming=False,
            response_ir=operation.responses[0],
        )

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        assert "match response.status_code:" in written_code
        assert "case 200:" in written_code
        assert "try:" in written_code
        assert "except Exception:" in written_code
        # Should attempt to parse as both types
        assert "ModelA.from_dict" in written_code
        assert "ModelB.from_dict" in written_code

    def test_generate_response_handling__list_return_type__handles_list_deserialization(
        self, generator, code_writer_mock, render_context_mock
    ) -> None:
        """
        Scenario: List return type needing item-by-item deserialization
        Expected Outcome: Generates list comprehension with BaseSchema deserialization
        """
        # Arrange
        operation = IROperation(
            operation_id="list_users",
            method=HTTPMethod.GET,
            path="/users",
            responses=[
                IRResponse(
                    status_code="200",
                    description="User list",
                    content={"application/json": IRSchema(type="array")},
                )
            ],
            summary="list users",
            description="list users",
        )

        strategy = ResponseStrategy(
            return_type="List[User]",
            response_schema=IRSchema(type="array"),
            is_streaming=False,
            response_ir=operation.responses[0],
        )

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        assert "match response.status_code:" in written_code
        assert "case 200:" in written_code
        # Should handle list deserialization
        assert "[User.from_dict(item) for item in response.json()]" in written_code

    def test_generate_response_handling__multiple_success_responses__handles_all_success_codes(
        self, generator, code_writer_mock, render_context_mock
    ) -> None:
        """
        Scenario: Multiple success responses (200, 201) with different types
        Expected Outcome: Generates separate case blocks for each success response
        """
        # Arrange
        schema_a = IRSchema(type="object", name="ModelA")
        schema_a.generation_name = "ModelA"
        schema_b = IRSchema(type="object", name="ModelB")
        schema_b.generation_name = "ModelB"

        operation = IROperation(
            operation_id="create_or_update",
            method=HTTPMethod.POST,
            path="/items",
            responses=[
                IRResponse(
                    status_code="200",
                    description="Updated",
                    content={"application/json": schema_a},
                ),
                IRResponse(
                    status_code="201",
                    description="Created",
                    content={"application/json": schema_b},
                ),
            ],
            summary="create or update",
            description="create or update",
        )

        # For this test, we'll use the primary success response (200)
        strategy = ResponseStrategy(
            return_type="ModelA", response_schema=schema_a, is_streaming=False, response_ir=operation.responses[0]
        )

        render_context_mock.name_sanitizer.sanitize_class_name.side_effect = lambda name: name

        # Provide schemas to the generator for this test
        generator.schemas = {"ModelA": schema_a, "ModelB": schema_b}

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        assert "match response.status_code:" in written_code
        assert "case 200:" in written_code
        assert "case 201:" in written_code
        assert "ModelA.from_dict" in written_code
        assert "ModelB.from_dict" in written_code
