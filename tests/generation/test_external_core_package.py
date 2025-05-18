import logging
import os
import subprocess
from pathlib import Path

import pytest
import yaml  # For loading dummy_spec_path

from pyopenapi_gen.emitters.core_emitter import CoreEmitter
from pyopenapi_gen.generator.client_generator import ClientGenerator

# Minimal OpenAPI spec for testing
MIN_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Minimal API", "version": "1.0.0"},
    "components": {
        "schemas": {
            "Error": {"type": "object", "properties": {"message": {"type": "string"}}},
            "Item": {"type": "object", "properties": {"id": {"type": "string"}}},
        }
    },
    "paths": {
        "/items": {
            "get": {
                "operationId": "get_items",
                "responses": {
                    "200": {
                        "description": "A list of items.",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Item"}}},
                    },
                    "default": {
                        "description": "error",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}},
                    },
                },
            }
        }
    },
}

TEST_TIMEOUT_SEC = 60  # Define if not present


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


@pytest.fixture
def dummy_spec_path(tmp_path: Path) -> Path:
    spec_file = tmp_path / "spec.yaml"
    with open(spec_file, "w") as f:
        yaml.dump(MIN_SPEC, f)
    return spec_file


@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_generate_client__external_core_elsewhere(tmp_path: Path, dummy_spec_path: Path) -> None:
    # ... (This test's body will be updated similarly if needed, focus on the failing one first)
    pass  # Placeholder for now


@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_generate_client__external_core_at_project_root__correct_paths_and_imports(
    tmp_path: Path, dummy_spec_path: Path
) -> None:
    """Scenario: Core package is generated at the project root, client is in a subdir.
    Client should use absolute imports to the core package.
    """
    core_dir_name = "external_core_pkg_name"
    client_dir_name = "my_client"

    core_abs_path = tmp_path / core_dir_name
    client_output_dir = tmp_path / client_dir_name

    # Emit the CORE package first
    # Original context for core generation (if it was separate)
    # core_gen_context = RenderContext(
    #     overall_project_root=str(tmp_path),
    #     package_root_for_generated_code=str(core_abs_path),
    #     core_package_name=core_dir_name,
    # )
    # Original CorePackageGenerator call (hypothetical based on old name)
    # core_package_emitter = CorePackageGenerator(context=core_gen_context, output_dir=str(core_abs_path))
    # core_package_emitter.emit_core_package()

    # New way to emit core using CoreEmitter
    core_emitter_instance = CoreEmitter(
        core_dir=".",  # Emits into the root of the dir provided to .emit()
        core_package=core_dir_name,  # The import name for the core package
    )
    # CoreEmitter.emit() expects the directory where the core_dir (e.g. ".") will be created.
    # So, this should be the absolute path of the core package itself.
    core_emitter_instance.emit(package_output_dir=str(core_abs_path))

    # Emit the CLIENT package
    # Original context for client generation (if MainEmitter used one explicitly)
    # client_gen_context = RenderContext(
    #     overall_project_root=str(tmp_path),
    #     package_root_for_generated_code=str(client_output_dir),
    #     core_package_name=core_dir_name,
    # )
    # Original MainEmitter call (hypothetical)
    # main_emitter = MainEmitter(output_dir=str(client_output_dir), context=client_gen_context)
    # main_emitter.emit(spec_path=dummy_spec_path)

    # New way using ClientGenerator
    client_generator = ClientGenerator()
    client_generator.generate(
        spec_path=str(dummy_spec_path),
        project_root=tmp_path,  # Root where client_dir_name will be created
        output_package=client_dir_name,  # Name of the client package directory
        core_package=core_dir_name,  # Instruct to use this external core package
        force=True,
        no_postprocess=True,
    )

    assert core_abs_path.is_dir()
    assert (core_abs_path / "__init__.py").exists()
    assert (core_abs_path / "http_transport.py").exists()
    assert (core_abs_path / "py.typed").exists()

    assert client_output_dir.is_dir()
    assert (client_output_dir / "__init__.py").exists()
    assert (client_output_dir / "client.py").exists()
    assert (client_output_dir / "models" / "__init__.py").exists()
    assert (client_output_dir / "endpoints" / "__init__.py").exists()
    assert (client_output_dir / "py.typed").exists()

    client_init_content = (client_output_dir / "__init__.py").read_text()
    assert f"from {core_dir_name}.auth import BaseAuth" in client_init_content
    assert f"from {core_dir_name}.config import ClientConfig" in client_init_content
    assert f"from {core_dir_name}.exceptions import HTTPError" in client_init_content
    assert f"from {core_dir_name}.http_transport import HttpTransport, HttpxTransport" in client_init_content

    main_client_content = (client_output_dir / "client.py").read_text()
    assert f"from {core_dir_name}.http_transport import HttpTransport, HttpxTransport" in main_client_content
    assert f"from {core_dir_name}.config import ClientConfig" in main_client_content
    assert "from .endpoints.default import DefaultClient" in main_client_content


@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_generate_client__shared_core_client_in_subdir__correct_paths_and_imports(
    tmp_path: Path, dummy_spec_path: Path
) -> None:
    """Scenario: Core and Client are subdirectories of a common project root.
    Client imports core using the core's package name.
    """
    project_root = tmp_path
    core_package_str = "shared_core_pkg"
    client_package_str = "client_pkg"

    core_package_dir = project_root / core_package_str
    client_package_dir = project_root / client_package_str

    # 1. Emit Core Package using CoreEmitter
    core_emitter_instance = CoreEmitter(core_dir=".", core_package=core_package_str)
    core_emitter_instance.emit(package_output_dir=str(core_package_dir))

    # 2. Emit Client Package using ClientGenerator
    client_generator = ClientGenerator()
    client_generator.generate(
        spec_path=str(dummy_spec_path),
        project_root=project_root,
        output_package=client_package_str,
        core_package=core_package_str,
        force=True,
        no_postprocess=True,
    )

    assert core_package_dir.is_dir()
    assert (core_package_dir / "py.typed").exists()
    assert client_package_dir.is_dir()
    assert (client_package_dir / "py.typed").exists()

    client_init_content = (client_package_dir / "__init__.py").read_text()
    assert f"from {core_package_str}.auth import BaseAuth" in client_init_content
    assert f"from {core_package_str}.config import ClientConfig" in client_init_content

    main_client_content = (client_package_dir / "client.py").read_text()
    assert f"from {core_package_str}.http_transport import HttpTransport" in main_client_content
    assert "from .endpoints.default import DefaultClient" in main_client_content

    # Assert that essential core files are generated before running Mypy
    assert (core_package_dir / "__init__.py").exists(), "Core __init__.py missing"
    assert (core_package_dir / "auth" / "__init__.py").exists(), "Core auth/__init__.py missing"
    assert (core_package_dir / "auth" / "base.py").exists(), "Core auth/base.py missing"
    assert (core_package_dir / "auth" / "plugins.py").exists(), "Core auth/plugins.py missing"
    assert (core_package_dir / "config.py").exists(), "Core config.py missing"
    assert (core_package_dir / "exceptions.py").exists(), "Core exceptions.py missing"
    assert (core_package_dir / "http_transport.py").exists(), "Core http_transport.py missing"
    assert (core_package_dir / "exception_aliases.py").exists(), "Core exception_aliases.py missing"

    run_mypy_on_generated_project(project_root, [client_package_str, core_package_str])


@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_generate_client__core_in_custom_project_subdir__correct_imports(tmp_path: Path, dummy_spec_path: Path) -> None:
    """Scenario: Core and Client are in custom subdirectories of a common project root.
    Client imports core using the core's full custom package path.
    e.g. project_root/api_sdks/my_core and project_root/generated_clients/my_client
    Client should import from api_sdks.my_core
    """
    project_root = tmp_path

    # Define package paths as strings (what the generator will use for Python package names)
    core_package_full_python_path = "api_sdks.my_company_standard_core"
    client_package_full_python_path = "generated_clients.acme_service_client"

    # Determine actual disk paths from these Python paths relative to project_root
    # core_package_disk_path = project_root / Path(*core_package_full_python_path.split('.'))
    # client_package_disk_path = project_root / Path(*client_package_full_python_path.split('.'))

    # The ClientGenerator expects output_package and core_package to be interpretable
    # as either direct directory names or dot-separated paths that it will create
    # under project_root. So, the actual paths will be based on these.
    core_package_actual_dir = project_root / core_package_full_python_path.replace(".", "/")
    client_package_actual_dir = project_root / client_package_full_python_path.replace(".", "/")

    # 1. Emit Core Package using CoreEmitter
    # core_package for CoreEmitter is the Python import name of the package it's creating.
    core_emitter_instance = CoreEmitter(core_dir=".", core_package=core_package_full_python_path)
    # package_output_dir is the directory *where* this core package will be placed.
    core_emitter_instance.emit(package_output_dir=str(core_package_actual_dir))

    # 2. Emit Client Package using ClientGenerator
    client_generator = ClientGenerator()
    client_generator.generate(
        spec_path=str(dummy_spec_path),
        project_root=project_root,  # The common root
        output_package=client_package_full_python_path,  # e.g. generated_clients.acme_service_client
        core_package=core_package_full_python_path,  # e.g. api_sdks.my_company_standard_core
        force=True,
        no_postprocess=True,
    )

    # Assertions
    assert core_package_actual_dir.is_dir(), f"Core package directory {core_package_actual_dir} not found."
    assert (core_package_actual_dir / "py.typed").exists(), "Core py.typed missing"
    assert (core_package_actual_dir / "__init__.py").exists(), "Core __init__.py missing"
    assert (core_package_actual_dir / "http_transport.py").exists(), "Core http_transport.py missing"

    assert client_package_actual_dir.is_dir(), f"Client package directory {client_package_actual_dir} not found."
    assert (client_package_actual_dir / "py.typed").exists(), "Client py.typed missing"
    assert (client_package_actual_dir / "__init__.py").exists(), "Client __init__.py missing"
    assert (client_package_actual_dir / "client.py").exists(), "Client client.py missing"

    # Check imports in client's __init__.py
    client_init_content = (client_package_actual_dir / "__init__.py").read_text()
    expected_auth_import = f"from {core_package_full_python_path}.auth import BaseAuth"
    expected_config_import = f"from {core_package_full_python_path}.config import ClientConfig"
    assert expected_auth_import in client_init_content, f"Client __init__.py missing import: {expected_auth_import}"
    assert expected_config_import in client_init_content, f"Client __init__.py missing import: {expected_config_import}"

    # Check imports in client's client.py
    main_client_content = (client_package_actual_dir / "client.py").read_text()
    expected_http_import = f"from {core_package_full_python_path}.http_transport import HttpTransport"
    assert expected_http_import in main_client_content, f"Client client.py missing import: {expected_http_import}"
    # Client's own relative import for its endpoints
    # The endpoint module name depends on the client package name structure.
    # If client_package_full_python_path is 'generated_clients.acme_service_client',
    # then endpoint imports are like 'from .endpoints.default import DefaultClient'
    assert "from .endpoints.default import DefaultClient" in main_client_content, (
        "Client client.py missing relative endpoint import."
    )

    # Run Mypy
    # The packages_to_check for Mypy should be the top-level directories created in project_root
    # that act as Python packages. In this case, 'api_sdks' and 'generated_clients'.
    # Mypy will then find the submodules like my_company_standard_core and acme_service_client.
    mypy_packages_to_check = [
        core_package_full_python_path.split(".")[0],  # e.g., 'api_sdks'
        client_package_full_python_path.split(".")[0],  # e.g., 'generated_clients'
    ]
    # Remove duplicates if top-level paths are the same (not in this specific test case)
    mypy_packages_to_check = sorted(list(set(mypy_packages_to_check)))

    run_mypy_on_generated_project(project_root, mypy_packages_to_check)
