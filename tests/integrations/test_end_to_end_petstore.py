import json
import os
import subprocess
from pathlib import Path

from pyopenapi_gen.generator.client_generator import ClientGenerator

# Minimal Petstore-like spec for integration test
MIN_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Demo API", "version": "1.0.0"},
    "paths": {
        "/pets": {
            "get": {
                "operationId": "list_pets",
                "summary": "List pets",
                "responses": {"200": {"description": "OK"}},
            }
        }
    },
}


def test_petstore_integration_with_tag(tmp_path: Path) -> None:
    """
    Scenario:
        Generate client for a minimal spec with a tag and verify output files.
    Expected Outcome:
        pets.py endpoint is generated and contains the list_pets method.
    """
    # Arrange
    spec = json.loads(json.dumps(MIN_SPEC))
    spec["paths"]["/pets"]["get"]["tags"] = ["pets"]
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec))

    project_root = tmp_path
    output_package = "petstore_client"
    out_dir = project_root / Path(*output_package.split("."))  # client files go here

    generator = ClientGenerator()

    # Act
    generator.generate(
        spec_path=str(spec_file),
        project_root=project_root,
        output_package=output_package,
        force=True,
        no_postprocess=True,
    )

    # Assert
    # Check core files (assuming default core location: <output_package>.core)
    resolved_core_package_fqn = output_package + ".core"
    core_dir = project_root / Path(*resolved_core_package_fqn.split("."))  # Corrected
    assert (core_dir / "config.py").exists(), "config.py not generated in core"
    # Check client package files
    assert (out_dir / "client.py").exists(), "client.py not generated"
    pets_file = out_dir / "endpoints" / "pets.py"
    assert pets_file.exists(), "pets.py endpoint not generated"
    content = pets_file.read_text()
    assert "async def list_pets" in content, "list_pets method missing in generated code"

    # Run mypy on the generated code to ensure type correctness
    env = os.environ.copy()
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))  # Adjusted path to src
    # PYTHONPATH needs the *parent* of the output_package and core_package directories
    # In this setup, project_root serves as this parent.
    env["PYTHONPATH"] = os.pathsep.join([str(project_root.resolve()), src_dir, env.get("PYTHONPATH", "")])
    # Tell mypy to check the main generated package. Mypy will find sub-packages (like .core) automatically.
    packages_to_check = [output_package.split(".")[0]]
    mypy_result = subprocess.run(
        ["mypy"] + packages_to_check, capture_output=True, text=True, env=env, cwd=project_root
    )
    assert mypy_result.returncode == 0, f"mypy errors:\n{mypy_result.stdout}\n{mypy_result.stderr}"


def test_petstore_client__without_tags__generates_default_endpoint_class(tmp_path: Path) -> None:
    """
    Scenario:
        ClientGenerator processes a petstore API spec without any tags
        specified for operations.

    Expected Outcome:
        The generator should create a default.py endpoint class containing
        all untagged operations grouped together.
    """
    # Arrange
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(MIN_SPEC))

    project_root = tmp_path
    output_package = "petstore_client"
    out_dir = project_root / Path(*output_package.split("."))  # client files go here

    generator = ClientGenerator()

    # Act
    generator.generate(
        spec_path=str(spec_file),
        project_root=project_root,
        output_package=output_package,
        force=True,
        no_postprocess=True,
    )

    # Assert
    # Check core files (assuming default core location: <output_package>.core)
    resolved_core_package_fqn = output_package + ".core"
    core_dir = project_root / Path(*resolved_core_package_fqn.split("."))  # Corrected
    assert (core_dir / "config.py").exists(), "config.py not generated in core"
    # Check client package files
    assert (out_dir / "client.py").exists(), "client.py not generated"
    default_file = out_dir / "endpoints" / "default.py"
    assert default_file.exists(), "default.py endpoint not generated"
    content = default_file.read_text()
    assert "async def list_pets" in content, "list_pets method missing in generated code"

    # +++ Print generated file content for debugging +++
    print(f"\n--- Content of {default_file} ---\n")
    print(content)
    print("\n--- End Content ---\n")
    # +++ End Print +++

    # Run mypy on the generated code to ensure type correctness
    env = os.environ.copy()
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))  # Adjusted path to src
    env["PYTHONPATH"] = os.pathsep.join([str(project_root.resolve()), src_dir, env.get("PYTHONPATH", "")])
    # Tell mypy to check the main generated package. Mypy will find sub-packages (like .core) automatically.
    packages_to_check = [output_package.split(".")[0]]
    mypy_result = subprocess.run(
        ["mypy"] + packages_to_check, capture_output=True, text=True, env=env, cwd=project_root
    )
    assert mypy_result.returncode == 0, f"mypy errors:\n{mypy_result.stdout}\n{mypy_result.stderr}"
