"""Test handling of duplicate operation IDs."""

import os
from pathlib import Path

from pyopenapi_gen import IROperation, IRParameter, IRRequestBody, IRResponse, IRSchema, IRSpec
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.emitters.endpoints_emitter import EndpointsEmitter


def test_deduplicate_operation_ids(tmp_path: Path) -> None:
    """Test the deduplication of operation IDs with the same sanitized name."""
    # Create two operations with IDs that would result in the same sanitized method name
    op1 = IROperation(
        operation_id="get_feedback",
        method="GET",
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
        method="GET",
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
    emitter = EndpointsEmitter()
    emitter.emit(spec, str(out_dir))
    
    # Check that the generated file exists
    client_file: Path = out_dir / "endpoints" / "feedback.py"
    assert client_file.exists()
    
    # Read the content and verify both methods exist with unique names
    content = client_file.read_text()
    assert "async def get_feedback" in content
    assert "async def get_feedback_2" in content  # Second method should have a suffix