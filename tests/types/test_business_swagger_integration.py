"""Integration test with business swagger to validate type resolution fixes."""

from unittest.mock import Mock

import pytest

from pyopenapi_gen import IROperation, IRResponse, IRSchema
from pyopenapi_gen.types.services.type_service import UnifiedTypeService


class TestBusinessSwaggerIntegration:
    """Test type resolution with business swagger scenarios."""

    @pytest.fixture
    def mock_context(self):
        """Mock render context that properly returns expected relative paths."""
        mock_render_context = Mock()
        mock_render_context.current_file = "/project/endpoints/some_endpoint.py"
        # Don't set a default return_value - let each test configure it
        mock_render_context.calculate_relative_path_for_internal_module = Mock()
        mock_render_context.add_import = Mock()

        context = Mock()
        context.render_context = mock_render_context
        context.add_import = Mock()
        context.add_conditional_import = Mock()

        return context

    def test_message_batch_response_type_resolution(self, mock_context) -> None:
        """
        Scenario: Resolving MessageBatchResponse with List[Message] data property
        Expected Outcome: Returns MessageBatchResponse and unwraps to List[Message]
        """

        # Configure mock to return expected relative paths
        def mock_relative_path(target):
            if target == "models.message":
                return "..models.message"
            elif target == "models.message_batch_response":
                return "..models.message_batch_response"
            return f"..models.{target.split('.')[-1]}"

        mock_context.render_context.calculate_relative_path_for_internal_module.side_effect = mock_relative_path

        # Arrange - Create schemas matching business swagger
        message_schema = IRSchema(name="Message", type="object", generation_name="Message", final_module_stem="message")

        message_batch_response_schema = IRSchema(
            name="MessageBatchResponse",
            type="object",
            properties={"data": IRSchema(type="array", items=message_schema)},
            generation_name="MessageBatchResponse",
            final_module_stem="message_batch_response",
        )

        schemas = {"Message": message_schema, "MessageBatchResponse": message_batch_response_schema}

        # Create response that references MessageBatchResponse
        response = IRResponse(
            status_code="200", description="Success", content={"application/json": message_batch_response_schema}
        )

        # Create operation (addMessages)
        operation = IROperation(
            operation_id="addMessages",
            method="POST",
            path="/messages/batch",
            summary="Add multiple messages",
            description="Add multiple messages to chat",
            responses=[response],
        )

        # Act
        type_service = UnifiedTypeService(schemas)
        result = type_service.resolve_operation_response_type(operation, mock_context.render_context)

        # Assert
        # Should unwrap to List[Message] not MessageBatchResponse
        assert result == "List[Message]"
        mock_context.render_context.add_import.assert_any_call("typing", "List")
        mock_context.render_context.add_import.assert_any_call("..models.message", "Message")

    def test_message_response_type_resolution(self, mock_context) -> None:
        """
        Scenario: Resolving MessageResponse with Message data property
        Expected Outcome: Returns MessageResponse and unwraps to Message
        """

        # Configure mock to return expected relative paths
        def mock_relative_path(target):
            if target == "models.message":
                return "..models.message"
            elif target == "models.message_response":
                return "..models.message_response"
            return f"..models.{target.split('.')[-1]}"

        mock_context.render_context.calculate_relative_path_for_internal_module.side_effect = mock_relative_path

        # Arrange - Create schemas matching business swagger
        message_schema = IRSchema(name="Message", type="object", generation_name="Message", final_module_stem="message")

        message_response_schema = IRSchema(
            name="MessageResponse",
            type="object",
            properties={"data": message_schema},
            generation_name="MessageResponse",
            final_module_stem="message_response",
        )

        schemas = {"Message": message_schema, "MessageResponse": message_response_schema}

        # Create response that references MessageResponse
        response = IRResponse(
            status_code="201", description="Created", content={"application/json": message_response_schema}
        )

        # Create operation (addMessage)
        operation = IROperation(
            operation_id="addMessage",
            method="POST",
            path="/messages",
            summary="Add a message",
            description="Add a message to chat",
            responses=[response],
        )

        # Act
        type_service = UnifiedTypeService(schemas)
        result = type_service.resolve_operation_response_type(operation, mock_context.render_context)

        # Assert
        # Should unwrap to Message not MessageResponse
        assert result == "Message"
        mock_context.render_context.add_import.assert_any_call("..models.message", "Message")

    def test_schema_reference_resolution(self, mock_context) -> None:
        """
        Scenario: Resolving schema with $ref to another schema
        Expected Outcome: Correctly resolves to target schema
        """

        # Configure mock to return expected relative paths
        def mock_relative_path(target):
            if target == "models.user":
                return "..models.user"
            return f"..models.{target.split('.')[-1]}"

        mock_context.render_context.calculate_relative_path_for_internal_module.side_effect = mock_relative_path

        # Arrange
        user_schema = IRSchema(name="User", type="object", generation_name="User", final_module_stem="user")

        # Schema that references User
        ref_schema = IRSchema(name="User")  # This acts as a reference

        schemas = {"User": user_schema}

        # Act
        type_service = UnifiedTypeService(schemas)
        result = type_service.resolve_schema_type(ref_schema, mock_context.render_context)

        # Assert
        assert result == "User"
        mock_context.render_context.add_import.assert_any_call("..models.user", "User")
