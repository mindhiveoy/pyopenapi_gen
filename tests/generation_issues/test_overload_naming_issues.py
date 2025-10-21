"""
Integration tests for overload method naming and file handling issues.

These tests verify that:
1. Methods with camelCase operationIds are converted to snake_case
2. File uploads don't use incorrect DataclassSerializer.serialize()
3. Multi-content-type operations generate correct code
"""

import json
import tempfile
from pathlib import Path

import pytest

from pyopenapi_gen.generator.client_generator import ClientGenerator


@pytest.fixture
def minimal_spec_with_camelcase_operations() -> dict:
    """Minimal OpenAPI spec with camelCase operation IDs and multi-content types."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/documents/{id}": {
                "put": {
                    "operationId": "updateDocument",  # camelCase
                    "summary": "Update a document",
                    "tags": ["documents"],
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"title": {"type": "string"}},
                                }
                            },
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"file": {"type": "string", "format": "binary"}},
                                }
                            },
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"id": {"type": "string"}},
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/documents": {
                "post": {
                    "operationId": "createDocument",  # camelCase
                    "summary": "Create a document",
                    "tags": ["documents"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"title": {"type": "string"}},
                                }
                            },
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"file": {"type": "string", "format": "binary"}},
                                }
                            },
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"id": {"type": "string"}},
                                    }
                                }
                            },
                        }
                    },
                }
            },
        },
    }


class TestOverloadNamingIntegration:
    """Integration tests for camelCase to snake_case conversion."""

    def test_generate_client__camelcase_operations__converts_to_snake_case(
        self, minimal_spec_with_camelcase_operations: dict
    ) -> None:
        """
        Scenario: Generate client from spec with camelCase operationIds
        Expected Outcome: Generated methods should be snake_case
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "spec.json"
            with open(spec_path, "w") as f:
                json.dump(minimal_spec_with_camelcase_operations, f)

            output_path = Path(tmpdir) / "output"
            output_path.mkdir()

            generator = ClientGenerator()

            # Act
            generated_files = generator.generate(
                spec_path=str(spec_path),
                project_root=output_path,
                output_package="testapi",
                force=True,
                no_postprocess=True,  # Skip formatting for faster test
            )

            # Assert
            # Find the generated endpoint file (exclude __init__.py)
            endpoint_files = [
                f for f in generated_files if "endpoints" in str(f) and not str(f).endswith("__init__.py")
            ]
            assert len(endpoint_files) > 0, "No endpoint files generated"

            # Collect all endpoint code
            all_code = ""
            for endpoint_file in endpoint_files:
                with open(endpoint_file, "r") as f:
                    all_code += f.read()

            # Check method names are snake_case
            assert "async def update_document(" in all_code, "updateDocument should be update_document"
            assert "async def create_document(" in all_code, "createDocument should be create_document"

            # Check they're NOT camelCase
            assert "async def updateDocument(" not in all_code, "Method name should not be camelCase updateDocument"
            assert "async def createDocument(" not in all_code, "Method name should not be camelCase createDocument"


class TestFileHandlingIntegration:
    """Integration tests for file upload handling."""

    def test_generate_client__multipart_files__no_serialization(
        self, minimal_spec_with_camelcase_operations: dict
    ) -> None:
        """
        Scenario: Generate client with multipart/form-data operations
        Expected Outcome: Files should be passed directly, not serialized
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = Path(tmpdir) / "spec.json"
            with open(spec_path, "w") as f:
                json.dump(minimal_spec_with_camelcase_operations, f)

            output_path = Path(tmpdir) / "output"
            output_path.mkdir()

            generator = ClientGenerator()

            # Act
            generated_files = generator.generate(
                spec_path=str(spec_path),
                project_root=output_path,
                output_package="testapi",
                force=True,
                no_postprocess=True,
            )

            # Assert
            endpoint_files = [f for f in generated_files if "endpoints" in str(f)]
            assert len(endpoint_files) > 0

            for endpoint_file in endpoint_files:
                with open(endpoint_file, "r") as f:
                    code = f.read()

                # Files should be passed directly
                if "multipart/form-data" in code:
                    # Should NOT serialize files
                    assert (
                        "files_data = DataclassSerializer.serialize(files)" not in code
                    ), "Files should not be serialized"

                    # Should pass files directly
                    assert "files=files," in code or "files = files" in code, "Files should be passed directly"
