"""Tests for GET endpoint return type inference."""

import unittest

from pyopenapi_gen import HTTPMethod, IROperation, IRResponse, IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.helpers.endpoint_utils import _infer_type_from_path, get_return_type


def test_infer_type_from_path() -> None:
    """Test _infer_type_from_path helper function."""
    # Create test schemas
    feedback_schema = IRSchema(name="Feedback", type="object")
    feedback_response_schema = IRSchema(name="FeedbackResponse", type="object")
    feedback_list_schema = IRSchema(name="FeedbackListResponse", type="object")
    user_schema = IRSchema(name="User", type="object")

    # Create schemas dictionary
    schemas = {
        "Feedback": feedback_schema,
        "FeedbackResponse": feedback_response_schema,
        "FeedbackListResponse": feedback_list_schema,
        "User": user_schema,
    }

    # Test inferring type from various paths

    # Test with direct resource name match
    inferred_schema = _infer_type_from_path("/tenants/{tenant_id}/feedback", schemas)
    assert inferred_schema is not None
    assert inferred_schema.name == "Feedback"

    # Test with response suffix
    inferred_schema = _infer_type_from_path("/tenants/{tenant_id}/agents/{agent_id}/feedbacks", schemas)
    assert inferred_schema is not None
    assert inferred_schema.name in ["Feedback", "FeedbackResponse"]

    # Test with list response (plural endpoint)
    inferred_schema = _infer_type_from_path("/tenants/{tenant_id}/feedbacks", schemas)
    assert inferred_schema is not None
    assert inferred_schema.name in ["Feedback", "FeedbackResponse", "FeedbackListResponse"]

    # Test with non-existent resource
    inferred_schema = _infer_type_from_path("/tenants/{tenant_id}/nonexistent", schemas)
    assert inferred_schema is None


def test_get_endpoint_infers_response_type() -> None:
    """Test return type inference for GET endpoint with no defined response schema."""
    # Create test schemas
    feedback_schema = IRSchema(name="Feedback", type="object")
    feedback_response_schema = IRSchema(name="FeedbackResponse", type="object")

    # Create schemas dictionary
    schemas = {
        "Feedback": feedback_schema,
        "FeedbackResponse": feedback_response_schema,
    }
    # Ensure generation_name and final_module_stem are set for schemas
    for schema in schemas.values():
        if schema.name:
            schema.generation_name = NameSanitizer.sanitize_class_name(schema.name)
            schema.final_module_stem = NameSanitizer.sanitize_module_name(schema.name)

    # Create context
    context = RenderContext(
        overall_project_root="/tmp",
        package_root_for_generated_code="/tmp/test_api",
        core_package_name="test_api.core",
    )

    # Create operation with GET method and no defined response
    operation = IROperation(
        operation_id="get_feedback",
        method=HTTPMethod.GET,
        path="/tenants/{tenant_id}/agents/{agent_id}/chats/{chat_id}/messages/{message_id}/feedback",
        parameters=[],
        responses=[],  # No response defined
        summary="Get feedback for a message",
        description="Retrieves feedback for a specific message",
    )

    # Get return type
    return_type, needs_unwrap = get_return_type(operation, context, schemas)

    # Assert return type is inferred from path
    assert return_type in ["Feedback", "FeedbackResponse"]
    assert needs_unwrap is False


def test_get_endpoint_with_defined_response_type() -> None:
    """Test that inference doesn't override defined response schemas."""
    # Create test schemas
    feedback_schema = IRSchema(name="Feedback", type="object")
    custom_response_schema = IRSchema(name="CustomResponse", type="object")

    # Create schemas dictionary
    schemas = {
        "Feedback": feedback_schema,
        "CustomResponse": custom_response_schema,
    }
    # Ensure generation_name and final_module_stem are set for schemas
    for schema in schemas.values():
        if schema.name:
            schema.generation_name = NameSanitizer.sanitize_class_name(schema.name)
            schema.final_module_stem = NameSanitizer.sanitize_module_name(schema.name)

    # Create context
    context = RenderContext(
        overall_project_root="/tmp",
        package_root_for_generated_code="/tmp/test_api",
        core_package_name="test_api.core",
    )

    # Create operation with GET method and a defined response
    operation = IROperation(
        operation_id="get_feedback",
        method=HTTPMethod.GET,
        path="/tenants/{tenant_id}/feedback",
        parameters=[],
        responses=[
            IRResponse(status_code="200", description="Success", content={"application/json": custom_response_schema})
        ],  # With a defined response
        summary="Get feedback",
        description="Retrieves feedback",
    )

    # Get return type
    return_type, needs_unwrap = get_return_type(operation, context, schemas)

    # Assert the defined response type is used, not the inferred one
    assert return_type == "CustomResponse"
    assert needs_unwrap is False


if __name__ == "__main__":
    unittest.main()
