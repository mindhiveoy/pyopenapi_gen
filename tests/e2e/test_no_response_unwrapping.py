"""E2E test to verify no automatic response unwrapping happens."""

import tempfile
from pathlib import Path

import pytest

from pyopenapi_gen import generate_client


def test_response_with_data_field__no_automatic_unwrapping() -> None:
    """
    Scenario: API response schema has a "data" field as part of its structure
    Expected Outcome: Generated code uses response.json() directly without unwrapping ["data"]

    This is a regression test for a bug where ANY response schema with a "data" property
    would automatically get unwrapped with response.json()["data"], even when "data" was
    just a normal field in the response structure.

    The correct behavior is to use response.json() and let cattrs handle deserialization
    based on the full schema structure.
    """
    # Arrange
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/vector-databases": {
                "get": {
                    "operationId": "list_vector_databases",
                    "summary": "List vector databases",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/VectorDatabaseListResponse"}
                                }
                            },
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "VectorDatabaseListResponse": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/VectorDatabase"},
                        },
                        "meta": {
                            "type": "object",
                            "properties": {"total": {"type": "integer"}},
                        },
                    },
                    "required": ["data"],
                },
                "VectorDatabase": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                    },
                    "required": ["id", "name", "type"],
                },
            }
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        spec_file = project_root / "spec.json"

        # Write spec to file
        import json

        spec_file.write_text(json.dumps(spec))

        # Act
        generate_client(
            spec_path=str(spec_file),
            project_root=str(project_root),
            output_package="test_client",
            force=True,
            no_postprocess=True,
        )

        # Assert
        # Check the generated endpoint file
        endpoint_file = project_root / "test_client" / "endpoints" / "default.py"
        assert endpoint_file.exists(), "Endpoint file should be generated"

        endpoint_content = endpoint_file.read_text()

        # NEW BEHAVIOR: No automatic unwrapping
        # Even though VectorDatabaseListResponse has a "data" field, we use full response.json()
        assert "return structure_from_dict(response.json(), VectorDatabaseListResponse)" in endpoint_content, (
            "Should use response.json() directly without unwrapping"
        )

        # Verify NO unwrapping happens
        assert 'response.json()["data"]' not in endpoint_content, (
            "Should NOT automatically unwrap data field - this was the bug we're fixing"
        )

        # Additional check: The response schema should be imported correctly
        assert "from ..models.vector_database_list_response import VectorDatabaseListResponse" in endpoint_content


def test_simple_response_without_data_field__uses_response_json() -> None:
    """
    Scenario: API response schema does NOT have a "data" field
    Expected Outcome: Generated code uses response.json() directly (no change from before)

    This test ensures our fix doesn't break the normal case where responses
    don't have a "data" field.
    """
    # Arrange
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users/{userId}": {
                "get": {
                    "operationId": "get_user",
                    "summary": "Get user by ID",
                    "parameters": [
                        {"name": "userId", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/User"}}},
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                    },
                    "required": ["id", "name", "email"],
                }
            }
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        spec_file = project_root / "spec.json"

        # Write spec to file
        import json

        spec_file.write_text(json.dumps(spec))

        # Act
        generate_client(
            spec_path=str(spec_file),
            project_root=str(project_root),
            output_package="test_client",
            force=True,
            no_postprocess=True,
        )

        # Assert
        endpoint_file = project_root / "test_client" / "endpoints" / "default.py"
        assert endpoint_file.exists(), "Endpoint file should be generated"

        endpoint_content = endpoint_file.read_text()

        # Should use response.json() directly
        assert "return structure_from_dict(response.json(), User)" in endpoint_content, (
            "Should use response.json() directly for simple schemas"
        )

        # Verify NO unwrapping
        assert 'response.json()["data"]' not in endpoint_content, "Should NOT unwrap data field"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
