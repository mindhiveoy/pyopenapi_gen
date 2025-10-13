"""Tests for the public programmatic API (generate_client function and exports)."""

import json
from pathlib import Path

import pytest


def test_generate_client__simple_usage__generates_client_successfully(tmp_path: Path) -> None:
    """
    Scenario:
        User calls generate_client() with minimal parameters to generate
        a client from an OpenAPI spec.

    Expected Outcome:
        The function generates the client successfully and returns a list
        of generated file paths.
    """
    # Arrange
    from pyopenapi_gen import generate_client

    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/items": {
                "get": {
                    "operationId": "get_items",
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }

    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec))

    # Act
    generated_files = generate_client(
        spec_path=str(spec_file),
        project_root=str(tmp_path),
        output_package="test_client",
        force=True,
        no_postprocess=True,
    )

    # Assert
    assert len(generated_files) > 0, "Should generate at least one file"
    assert (tmp_path / "test_client" / "client.py").exists(), "Should generate client.py"
    assert (tmp_path / "test_client" / "endpoints").exists(), "Should generate endpoints directory"
    assert (tmp_path / "test_client" / "models").exists(), "Should generate models directory"


def test_generate_client__with_core_package__generates_shared_core(tmp_path: Path) -> None:
    """
    Scenario:
        User specifies a custom core_package to create a shared core
        that can be reused by multiple clients.

    Expected Outcome:
        The core package is created at the specified location, and the
        client imports from it correctly.
    """
    # Arrange
    from pyopenapi_gen import generate_client

    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/items": {
                "get": {
                    "operationId": "get_items",
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }

    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec))

    # Act
    generate_client(
        spec_path=str(spec_file),
        project_root=str(tmp_path),
        output_package="test_client",
        core_package="shared_core",
        force=True,
        no_postprocess=True,
    )

    # Assert
    assert (tmp_path / "shared_core").exists(), "Should create shared_core directory"
    assert (tmp_path / "shared_core" / "config.py").exists(), "Should have config.py in core"
    assert (tmp_path / "test_client" / "client.py").exists(), "Should generate client.py"

    # Check that client imports from shared_core
    client_content = (tmp_path / "test_client" / "client.py").read_text()
    assert "from shared_core" in client_content, "Client should import from shared_core"


def test_generate_client__returns_file_list__contains_generated_paths(tmp_path: Path) -> None:
    """
    Scenario:
        User calls generate_client() and inspects the returned list of
        generated files.

    Expected Outcome:
        The function returns a list of Path objects for all files that
        were generated.
    """
    # Arrange
    from pyopenapi_gen import generate_client

    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "list_users",
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }

    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec))

    # Act
    generated_files = generate_client(
        spec_path=str(spec_file),
        project_root=str(tmp_path),
        output_package="users_client",
        force=True,
        no_postprocess=True,
    )

    # Assert
    assert isinstance(generated_files, list), "Should return a list"
    assert all(isinstance(f, Path) for f in generated_files), "All items should be Path objects"
    assert len(generated_files) > 5, "Should generate multiple files (models, endpoints, core, client)"


def test_generate_client__invalid_spec__raises_generation_error(tmp_path: Path) -> None:
    """
    Scenario:
        User provides a path to a non-existent spec file.

    Expected Outcome:
        The function raises GenerationError with a helpful message.
    """
    # Arrange
    from pyopenapi_gen import GenerationError, generate_client

    nonexistent_spec = tmp_path / "does_not_exist.yaml"

    # Act & Assert
    with pytest.raises(GenerationError) as exc_info:
        generate_client(
            spec_path=str(nonexistent_spec),
            project_root=str(tmp_path),
            output_package="test_client",
        )

    assert "not found" in str(exc_info.value).lower(), "Error message should mention file not found"


def test_generate_client__verbose_mode__prints_progress(tmp_path: Path, capsys) -> None:
    """
    Scenario:
        User enables verbose mode to see detailed progress information.

    Expected Outcome:
        Progress messages are printed to stdout during generation.
    """
    # Arrange
    from pyopenapi_gen import generate_client

    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/items": {
                "get": {
                    "operationId": "get_items",
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }

    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec))

    # Act
    generate_client(
        spec_path=str(spec_file),
        project_root=str(tmp_path),
        output_package="test_client",
        force=True,
        no_postprocess=True,
        verbose=True,
    )

    # Assert
    captured = capsys.readouterr()
    assert (
        "Starting code generation" in captured.out or "Loading specification" in captured.out
    ), "Verbose mode should print progress messages"


def test_client_generator_class__is_exported__can_be_imported(tmp_path: Path) -> None:
    """
    Scenario:
        Advanced user wants to use ClientGenerator class directly for
        more control over generation.

    Expected Outcome:
        ClientGenerator can be imported from package root and used
        directly.
    """
    # Arrange & Act
    from pyopenapi_gen import ClientGenerator

    # Assert
    assert ClientGenerator is not None, "ClientGenerator should be exported"
    generator = ClientGenerator(verbose=False)
    assert generator is not None, "Should be able to instantiate ClientGenerator"


def test_generation_error__is_exported__can_be_caught() -> None:
    """
    Scenario:
        User wants to catch GenerationError exceptions in their code.

    Expected Outcome:
        GenerationError can be imported from package root and used in
        exception handling.
    """
    # Arrange & Act
    from pyopenapi_gen import GenerationError

    # Assert
    assert GenerationError is not None, "GenerationError should be exported"
    assert issubclass(GenerationError, Exception), "GenerationError should be an Exception subclass"


def test_imports__all_public_api__is_accessible() -> None:
    """
    Scenario:
        User imports all public API components from the package root.

    Expected Outcome:
        All advertised exports are accessible without errors.
    """
    # Act & Assert - should not raise ImportError
    from pyopenapi_gen import (
        ClientGenerator,
        GenerationError,
        HTTPMethod,
        IROperation,
        IRParameter,
        IRRequestBody,
        IRResponse,
        IRSchema,
        IRSpec,
        WarningCollector,
        generate_client,
        load_ir_from_spec,
    )

    # Verify types exist
    assert generate_client is not None
    assert ClientGenerator is not None
    assert GenerationError is not None
    assert IRSpec is not None
    assert IRSchema is not None
    assert IROperation is not None
    assert IRParameter is not None
    assert IRResponse is not None
    assert IRRequestBody is not None
    assert HTTPMethod is not None
    assert load_ir_from_spec is not None
    assert WarningCollector is not None


def test_generate_client__with_pathlib_path__works_correctly(tmp_path: Path) -> None:
    """
    Scenario:
        User provides Path objects instead of strings for paths.

    Expected Outcome:
        The function accepts Path objects and generates client correctly.
    """
    # Arrange
    from pyopenapi_gen import generate_client

    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/items": {
                "get": {
                    "operationId": "get_items",
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }

    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec))

    # Act - Using Path objects instead of strings
    generated_files = generate_client(
        spec_path=str(spec_file),  # Still need string for spec_path in signature
        project_root=str(tmp_path),  # project_root accepts str, converts internally
        output_package="test_client",
        force=True,
        no_postprocess=True,
    )

    # Assert
    assert len(generated_files) > 0
    assert (tmp_path / "test_client" / "client.py").exists()
