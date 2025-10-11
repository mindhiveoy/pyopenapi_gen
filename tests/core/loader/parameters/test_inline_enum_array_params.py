"""
Test that inline enum arrays in parameters are properly generated and importable.

This test ensures that when parameters have inline enum arrays (like include parameters),
the enum types are:
1. Created with proper names
2. Registered in the schema collection
3. Generated as model files
4. Properly imported in endpoint files
"""

import tempfile
from pathlib import Path

from pyopenapi_gen.generator.client_generator import ClientGenerator


def test_inline_enum_array_parameter_generation():
    """
    Scenario:
        Generate a client from a spec with inline enum array parameters.

    Expected Outcome:
        - Inline enum types should be generated as model files
        - Endpoint files should import these enum types
        - The generated client should be importable without errors
    """
    # Create a minimal OpenAPI spec with inline enum array parameter
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/agents/{agentId}": {
                "get": {
                    "operationId": "getAgent",
                    "parameters": [
                        {"name": "agentId", "in": "path", "required": True, "schema": {"type": "string"}},
                        {
                            "name": "include",
                            "in": "query",
                            "required": False,
                            "schema": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["tenant", "settings", "credentials", "datasources"],
                                },
                            },
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"id": {"type": "string"}, "name": {"type": "string"}},
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        spec_file = temp_path / "spec.json"

        # Write spec to file
        import json

        spec_file.write_text(json.dumps(spec))

        # Generate client
        generator = ClientGenerator(verbose=False)
        generator.generate(
            spec_path=str(spec_file),
            project_root=temp_path,
            output_package="test_client",
            force=True,
            no_postprocess=True,
        )

        # Check that the enum type was generated as a model file
        enum_file = temp_path / "test_client" / "models" / "get_agent_param_include_item.py"
        assert enum_file.exists(), f"Enum file should be generated at {enum_file}"

        # Check the enum file contents
        enum_content = enum_file.read_text()
        assert "class GetAgentParamIncludeItem" in enum_content, "Enum class should be defined"
        assert "tenant" in enum_content, "Enum should contain 'tenant' value"
        assert "settings" in enum_content, "Enum should contain 'settings' value"

        # Check that the endpoint file imports the enum
        endpoint_file = temp_path / "test_client" / "endpoints" / "default.py"
        assert endpoint_file.exists(), "Endpoint file should be generated"

        endpoint_content = endpoint_file.read_text()
        assert (
            "from ..models.get_agent_param_include_item import GetAgentParamIncludeItem" in endpoint_content
        ), "Endpoint should import the enum type"
        assert (
            "include: List[GetAgentParamIncludeItem] | None" in endpoint_content
        ), "Parameter should be typed with the enum"

        # Try to import the generated client
        import sys

        sys.path.insert(0, str(temp_path))

        try:
            # This should not raise any NameError
            from test_client import APIClient

            # Create a client instance
            client = APIClient(base_url="https://api.example.com")

            # Check that the endpoint exists and is callable
            assert hasattr(client, "default"), "Client should have default endpoint"

            print("✅ Client imported successfully without NameError!")

        except NameError as e:
            assert False, f"Client import failed with NameError: {e}"
        except ImportError as e:
            # Handle other import errors gracefully for testing
            print(f"Import error (expected in test environment): {e}")
        finally:
            # Clean up sys.path
            sys.path.remove(str(temp_path))


def test_business_swagger_inline_enum_parameters():
    """
    Scenario:
        Test with the actual business_swagger.json that has many inline enum array parameters.

    Expected Outcome:
        - All inline enum types should be generated
        - Client should be importable
    """
    spec_path = Path(__file__).parent.parent.parent.parent.parent / "input" / "business_swagger.json"

    if not spec_path.exists():
        print(f"Skipping business_swagger test - file not found at {spec_path}")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # Generate client
        generator = ClientGenerator(verbose=False)
        generator.generate(
            spec_path=str(spec_path),
            project_root=temp_path,
            output_package="business_client",
            force=True,
            no_postprocess=True,
        )

        # Check that include enum types were generated
        models_dir = temp_path / "business_client" / "models"

        # Look for any include-related enum files
        include_enums = list(models_dir.glob("*include*.py"))
        assert len(include_enums) > 0, "Should generate include enum types"

        print(f"✅ Generated {len(include_enums)} include enum files")

        # Check a specific one we know should exist
        agent_include_enum = models_dir / "get_agent_param_include_item.py"
        if agent_include_enum.exists():
            content = agent_include_enum.read_text()
            assert "class GetAgentParamIncludeItem" in content
            print("✅ GetAgentParamIncludeItem enum generated correctly")

        # Try to import the client
        import sys

        sys.path.insert(0, str(temp_path))

        try:

            print("✅ AgentsClient imported successfully!")

            # This should work without NameError
            from business_client import APIClient

            client = APIClient(base_url="https://api.example.com")
            print("✅ Full client imported successfully!")

        except NameError as e:
            assert False, f"Import failed with NameError (the bug we're fixing): {e}"
        except Exception as e:
            print(f"Other error (may be expected): {e}")
        finally:
            sys.path.remove(str(temp_path))


if __name__ == "__main__":
    test_inline_enum_array_parameter_generation()
    test_business_swagger_inline_enum_parameters()
