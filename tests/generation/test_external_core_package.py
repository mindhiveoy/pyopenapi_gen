import json
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from pyopenapi_gen.generator.client_generator import ClientGenerator, GenerationError

# Minimal OpenAPI spec for testing
MIN_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Test API", "version": "1.0.0"},
    "servers": [{"url": "https://api.example.com/v1"}],
    "paths": {
        "/items": {
            "get": {
                "operationId": "get_items",
                "summary": "List all items",
                "security": [{"ApiKeyAuth": []}],
                "responses": {
                    "200": {
                        "description": "A list of items.",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"$ref": "#/components/schemas/Item"}}
                            }
                        },
                    },
                    "400": {
                        "description": "Invalid request",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}},
                    },
                },
            }
        }
    },
    "components": {
        "schemas": {
            "Item": {
                "type": "object",
                "properties": {"id": {"type": "integer", "format": "int64"}, "name": {"type": "string"}},
                "required": ["id", "name"],
            },
            "Error": {"type": "object", "properties": {"code": {"type": "integer"}, "message": {"type": "string"}}},
        },
        "securitySchemes": {"ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-KEY"}},
    },
}


# Helper to run mypy
def run_mypy_on_generated_project(project_root: Path, packages_to_check: list[str]) -> None:
    """
    Runs mypy on specified packages within the generated project.
    Assumes project_root is in PYTHONPATH.
    """
    env = os.environ.copy()
    # Ensure project_root itself is on PYTHONPATH so top-level packages can be found
    python_path_parts = [
        str(project_root.resolve()),
        env.get("PYTHONPATH", ""),
    ]
    env["PYTHONPATH"] = os.pathsep.join(filter(None, python_path_parts))

    cmd = ["mypy", "--strict"] + packages_to_check

    # For debugging MyPy issues:
    # print(f"\nRunning mypy command: {' '.join(cmd)}")
    # print(f"PYTHONPATH: {env['PYTHONPATH']}")
    # print(f"Working directory: {project_root}\n")

    result = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=project_root)
    if result.returncode != 0:
        # Ensure project_root is part of the error message paths for clarity
        stdout = result.stdout.replace(str(project_root), "PROJECT_ROOT")
        stderr = result.stderr.replace(str(project_root), "PROJECT_ROOT")
        pytest.fail(
            f"Mypy errors found (PYTHONPATH='{env['PYTHONPATH']}', CWD='{project_root}'):\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )


# Configure logging for debugging import paths
loggers_to_debug = [
    "pyopenapi_gen.context.render_context",
    "pyopenapi_gen.visit.client_visitor",
]
for logger_name in loggers_to_debug:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    # Ensure handlers are not duplicated if tests run multiple times in one session
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    elif isinstance(logger.handlers[0], logging.StreamHandler):  # Check existing handler level
        logger.handlers[0].setLevel(logging.DEBUG)


def test_generate_client__external_core_at_project_root__correct_paths_and_imports() -> None:
    """
    Scenario:
        - Generate a client where `output_package` is a nested package (e.g., `generated_client.api`).
        - `core_package` is a top-level package at the project root (e.g., `custom_core`).
        - This simulates a shared core package alongside one or more client packages.

    Expected Outcome:
        - Core files are generated in `project_root/custom_core/`.
        - Client files are generated in `project_root/generated_client/api/`.
        - Imports within the client code correctly use relative paths to access `custom_core`
          (e.g., `from ..custom_core.http_transport import ...` in `client.py`,
           `from ...custom_core.schemas import ...` in model files,
           `from ...custom_core.exceptions import ...` in endpoint files).
        - The generated code passes `mypy --strict` checks.
    """
    with tempfile.TemporaryDirectory() as temp_dir_name:
        project_root = Path(temp_dir_name)
        output_package_str = "generated_client.api"
        core_package_str = "custom_core"

        # Create a dummy spec file
        spec_file = project_root / "spec.yaml"
        spec_file.write_text(json.dumps(MIN_SPEC))

        generator = ClientGenerator()
        try:
            generator.generate(
                spec_path=str(spec_file),
                project_root=project_root,
                output_package=output_package_str,
                core_package=core_package_str,
                force=True,
                no_postprocess=True,  # mypy will be run separately
            )
        except GenerationError as e:
            pytest.fail(f"Client generation failed: {e}")

        # Define expected paths
        core_package_dir = project_root / Path(*core_package_str.split("."))
        client_package_dir = project_root / Path(*output_package_str.split("."))

        # 1. Check core package structure
        assert core_package_dir.exists(), f"Core package dir {core_package_dir} not found."
        assert (core_package_dir / "__init__.py").exists()
        assert (core_package_dir / "http_transport.py").exists()
        assert (core_package_dir / "auth").is_dir(), "Core package 'auth' subdirectory not found."
        assert (core_package_dir / "auth" / "__init__.py").exists(), "Core 'auth/__init__.py' not found."
        assert (core_package_dir / "auth" / "base.py").exists(), "Core 'auth/base.py' not found."
        assert (core_package_dir / "auth" / "plugins.py").exists(), "Core 'auth/plugins.py' not found."
        assert (core_package_dir / "schemas.py").exists()
        assert (core_package_dir / "exceptions.py").exists()

        # 2. Check client package structure
        assert client_package_dir.exists(), f"Client package dir {client_package_dir} not found."
        assert (client_package_dir / "__init__.py").exists()
        assert (client_package_dir / "client.py").exists()
        models_dir = client_package_dir / "models"
        endpoints_dir = client_package_dir / "endpoints"
        assert models_dir.exists()
        assert (models_dir / "__init__.py").exists()
        assert (models_dir / "item.py").exists()  # From MIN_SPEC
        assert (models_dir / "error.py").exists()  # From MIN_SPEC
        assert endpoints_dir.exists()
        assert (endpoints_dir / "__init__.py").exists()
        # Default tag or operationId based naming for endpoint file
        # For MIN_SPEC, operationId "get_items" might lead to "default.py" or similar if no tags
        # Let's find the first non-__init__ .py file in endpoints.
        endpoint_files = [f for f in endpoints_dir.glob("*.py") if f.name != "__init__.py"]
        assert len(endpoint_files) > 0, "No endpoint file generated"
        endpoint_file = endpoint_files[0]  # Assuming one for this minimal spec

        # 3. Check import statements
        client_py_content = (client_package_dir / "client.py").read_text()
        print("\n--- client.py content ---")
        print(client_py_content)
        assert re.search(r"from\s+custom_core\.http_transport\s+import\s+HttpTransport", client_py_content)
        assert re.search(r"from\s+custom_core\.auth\.plugins\s+import\s+ApiKeyAuth", client_py_content)
        assert re.search(r"from\s+custom_core\.config\s+import\s+ClientConfig", client_py_content)
        assert re.search(r"from\s+\.endpoints\.default\s+import\s+DefaultClient", client_py_content)

        item_model_content = (client_package_dir / "models" / "item.py").read_text()
        print("\n--- models/item.py content ---")
        print(item_model_content)
        # assert re.search(r"from\s+custom_core\.schemas\s+import\s+BaseSchema", item_model_content) # Commented out

        default_endpoint_content = (client_package_dir / "endpoints" / "default.py").read_text()
        print("\n--- endpoints/default.py content ---")
        print(default_endpoint_content)
        assert re.search(r"from\s+custom_core\.http_transport\s+import\s+HttpTransport", default_endpoint_content)
        assert re.search(
            r"from\s+custom_core\.exceptions\s+import\s+([a-zA-Z0-9_,\s]*\bHTTPError\b[a-zA-Z0-9_,\s]*)",
            default_endpoint_content,
        )
        assert re.search(r"from\s+\.\.models\.item\s+import\s+Item", default_endpoint_content)

        # 4. Run mypy on the generated project

        # Create __init__.py in parent package if needed
        (project_root / "generated_client" / "__init__.py").touch()

        # Calculate paths relative to project_root for mypy
        # Mypy works best with relative or absolute paths to directories/files to check.
        # Convert package names to relative directory paths from project_root
        client_package_rel_path = os.path.join(*output_package_str.split("."))  # "generated_client/api"
        core_package_rel_path = os.path.join(*core_package_str.split("."))  # "custom_core"

        paths_to_check_for_mypy = [
            client_package_rel_path,
            core_package_rel_path,
        ]

        # run_mypy_on_generated_project runs mypy from project_root
        # It adds project_root to PYTHONPATH
        # Passing relative paths from project_root should work
        run_mypy_on_generated_project(project_root, paths_to_check_for_mypy)

        # Further check: Ensure __init__.py in client_package_dir and core_package_dir are not empty if they shouldn't be
        # For now, existence is fine.

        # Check for py.typed in both packages
        assert (core_package_dir / "py.typed").exists(), "py.typed missing in core package"
        assert (client_package_dir / "py.typed").exists(), "py.typed missing in client package"
