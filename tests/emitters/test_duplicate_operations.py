"""Test handling of duplicate operation IDs."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pyopenapi_gen import IROperation, IRResponse, IRSchema, IRSpec
from pyopenapi_gen.context.file_manager import FileManager
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.emitters.endpoints_emitter import EndpointsEmitter
from pyopenapi_gen.http_types import HTTPMethod


@pytest.fixture
def mock_render_context(tmp_path: Path) -> MagicMock:
    ctx = MagicMock(spec=RenderContext)
    ctx.parsed_schemas = {}

    # Configure file_manager to actually write files for .exists() checks
    actual_fm = FileManager()
    ctx.file_manager = MagicMock(spec=FileManager)
    ctx.file_manager.write_file.side_effect = lambda path, content, **kwargs: actual_fm.write_file(
        path, content, **kwargs
    )
    ctx.file_manager.ensure_dir.side_effect = actual_fm.ensure_dir

    ctx.import_collector = MagicMock()
    ctx.render_imports.return_value = "# Mocked imports\nfrom typing import Any"
    # Configure package_root_for_generated_code and overall_project_root as they might be used
    ctx.package_root_for_generated_code = str(tmp_path / "out")
    ctx.overall_project_root = str(tmp_path)
    ctx.core_package_name = "test_client.core"
    return ctx


def test_endpoints_emitter__duplicate_operation_ids__generates_unique_method_names(
    tmp_path: Path, mock_render_context: MagicMock
) -> None:
    """
    Scenario:
        EndpointsEmitter processes operations with IDs that would result in the same
        sanitized method name (e.g., "get_feedback" and "getFeedback").

    Expected Outcome:
        The emitter should generate unique method names by adding suffixes
        (e.g., "get_feedback" and "get_feedback_2").
    """
    # Create two operations with IDs that would result in the same sanitized method name
    op1 = IROperation(
        operation_id="get_feedback",
        method=HTTPMethod.GET,
        path="/feedback/{feedback_id}",
        parameters=[],
        responses=[
            IRResponse(
                status_code="200",
                description="Success",
                content={"application/json": IRSchema(name="FeedbackResponse", type="object")},
            )
        ],
        summary="Get specific feedback",
        description="Get feedback by ID",
        tags=["Feedback"],
    )

    op2 = IROperation(
        operation_id="getFeedback",  # Different casing, but same sanitized name
        method=HTTPMethod.GET,
        path="/feedback",
        parameters=[],
        responses=[
            IRResponse(
                status_code="200",
                description="Success",
                content={"application/json": IRSchema(name="FeedbackListResponse", type="object")},
            )
        ],
        summary="List all feedback",
        description="List all feedback",
        tags=["Feedback"],
    )

    # Create spec with both operations
    spec = IRSpec(
        title="Test API",
        version="1.0.0",
        schemas={},
        operations=[op1, op2],
        servers=[],
    )

    # Generate client code
    out_dir: Path = tmp_path / "out"
    # Ensure the mock_render_context has the correct parsed_schemas if needed by EndpointVisitor
    # For this specific test, EndpointVisitor might not be deeply called if emit focuses on module/class names only.
    # However, it's safer to provide it if EndpointVisitor is initialized within EndpointsEmitter.emit
    mock_render_context.parsed_schemas = spec.schemas

    emitter = EndpointsEmitter(context=mock_render_context)
    emitter.emit(spec.operations, str(out_dir))

    # Check that the generated file exists
    client_file: Path = out_dir / "endpoints" / "feedback.py"
    assert client_file.exists()

    # Read the content and verify both methods exist with unique names
    content = client_file.read_text()
    assert "async def get_feedback" in content
    assert "async def get_feedback_2" in content  # Second method should have a suffix
