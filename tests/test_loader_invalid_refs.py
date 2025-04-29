import pytest
import warnings

from pyopenapi_gen.core.loader import (
    load_ir_from_spec,
    validate_spec as _real_validate_spec,
)
from pyopenapi_gen import IRSchema

"""
tests/test_loader_invalid_refs.py

These tests verify that the loader:
1. Continues on spec validation errors by catching and warning.
2. Handles unresolved $ref in response content by falling back to a default IRSchema.
"""


def test_loader_continues_on_validate_spec_error(monkeypatch):
    """
    Scenario: validate_spec raises ValueError during spec validation.
    Expected Outcome:
        - A UserWarning 'OpenAPI spec validation error: TestError' is emitted.
        - load_ir_from_spec returns an IRSpec with operations parsed normally.
    """
    # Monkeypatch validate_spec to always raise
    import pyopenapi_gen.loader as loader

    monkeypatch.setattr(
        loader,
        "validate_spec",
        lambda spec: (_ for _ in ()).throw(ValueError("TestError")),
    )
    # Minimal valid spec
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "operationId": "getTest",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {"schema": {"type": "object"}}
                            },
                        }
                    },
                }
            }
        },
    }
    # Expect a UserWarning for validation error but no exception
    with pytest.warns(UserWarning, match="OpenAPI spec validation error: TestError"):
        ir = load_ir_from_spec(spec)
    # IRSpec should be returned with operations
    assert ir.operations, "Expected operations to be parsed even after validation error"
    op = ir.operations[0]
    assert op.operation_id == "getTest"
    # Response content schema should be parsed
    resp = op.responses[0]
    assert resp.status_code == "200"
    assert "application/json" in resp.content
    schema = resp.content["application/json"]
    assert isinstance(schema, IRSchema)


def test_loader_handles_unresolved_ref_in_response_content(monkeypatch):
    """
    Scenario: A response uses an unresolved $ref for content.
    Expected Outcome:
        - load_ir_from_spec does not raise.
        - The content schema is an IRSchema instance with name=None.
    """
    # Monkeypatch validate_spec to None to skip real validation
    import pyopenapi_gen.loader as loader

    monkeypatch.setattr(loader, "validate_spec", None)
    # Spec with unresolved $ref inside response content
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "Ref Test", "version": "1.0.0"},
        "paths": {
            "/ref": {
                "get": {
                    "operationId": "getRef",
                    "responses": {
                        "204": {
                            "description": "No Content",
                            "content": {
                                "application/json": {
                                    "$ref": "#/components/responses/NoContentError"
                                }
                            },
                        }
                    },
                }
            }
        },
    }
    # No warnings expected from validation
    ir = load_ir_from_spec(spec)
    assert ir.operations, "Expected operations parsed even with unresolved $ref"
    op = ir.operations[0]
    assert op.operation_id == "getRef"
    resp = op.responses[0]
    assert resp.status_code == "204"
    # Unresolved $ref should produce a default IRSchema (name=None)
    assert "application/json" in resp.content
    schema = resp.content["application/json"]
    assert isinstance(schema, IRSchema)
    assert schema.name is None
