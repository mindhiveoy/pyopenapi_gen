"""
Tests for RenderContext.get_core_import_path() method.

Tests verify that the centralized function correctly calculates
relative import paths to the core package from different file locations.
"""

import tempfile
from pathlib import Path

from pyopenapi_gen.context.render_context import RenderContext


def test_get_core_import_path__from_models__calculates_correct_depth():
    """
    Scenario: Calculate import path from models/user.py to core/schemas

    Expected Outcome: Returns "...core.schemas" (3 dots = up 2 levels)
    """
    # Arrange
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        businessapi_root = project_root / "businessapi"
        core_root = project_root / "core"

        # Create directory structure
        (businessapi_root / "models").mkdir(parents=True)
        core_root.mkdir(parents=True)

        context = RenderContext(
            core_package_name="core",
            package_root_for_generated_code=str(businessapi_root),
            overall_project_root=str(project_root),
        )
        context.set_current_file(str(businessapi_root / "models" / "user.py"))

        # Act
        result = context.get_core_import_path("schemas")

        # Assert
        assert result == "...core.schemas", f"Expected '...core.schemas', got '{result}'"


def test_get_core_import_path__from_client__calculates_correct_depth():
    """
    Scenario: Calculate import path from client.py to core/http_transport

    Expected Outcome: Returns "..core.http_transport" (2 dots = up 1 level)
    """
    # Arrange
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        businessapi_root = project_root / "businessapi"
        core_root = project_root / "core"

        # Create directory structure
        businessapi_root.mkdir(parents=True)
        core_root.mkdir(parents=True)

        context = RenderContext(
            core_package_name="core",
            package_root_for_generated_code=str(businessapi_root),
            overall_project_root=str(project_root),
        )
        context.set_current_file(str(businessapi_root / "client.py"))

        # Act
        result = context.get_core_import_path("http_transport")

        # Assert
        assert result == "..core.http_transport", f"Expected '..core.http_transport', got '{result}'"


def test_get_core_import_path__from_endpoints__calculates_correct_depth():
    """
    Scenario: Calculate import path from endpoints/auth.py to core/exceptions

    Expected Outcome: Returns "...core.exceptions" (3 dots = up 2 levels)
    """
    # Arrange
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        businessapi_root = project_root / "businessapi"
        core_root = project_root / "core"

        # Create directory structure
        (businessapi_root / "endpoints").mkdir(parents=True)
        core_root.mkdir(parents=True)

        context = RenderContext(
            core_package_name="core",
            package_root_for_generated_code=str(businessapi_root),
            overall_project_root=str(project_root),
        )
        context.set_current_file(str(businessapi_root / "endpoints" / "auth.py"))

        # Act
        result = context.get_core_import_path("exceptions")

        # Assert
        assert result == "...core.exceptions", f"Expected '...core.exceptions', got '{result}'"


def test_get_core_import_path__external_package__uses_absolute_import():
    """
    Scenario: External core package with dots in name

    Expected Outcome: Returns absolute import path "api_sdks.my_core.schemas"
    """
    # Arrange
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        businessapi_root = project_root / "businessapi"

        # Create directory structure
        (businessapi_root / "models").mkdir(parents=True)

        context = RenderContext(
            core_package_name="api_sdks.my_core",
            package_root_for_generated_code=str(businessapi_root),
            overall_project_root=str(project_root),
        )
        context.set_current_file(str(businessapi_root / "models" / "user.py"))

        # Act
        result = context.get_core_import_path("schemas")

        # Assert
        assert result == "api_sdks.my_core.schemas", f"Expected 'api_sdks.my_core.schemas', got '{result}'"


def test_get_core_import_path__already_relative__preserves_relative():
    """
    Scenario: Core package name is already a relative import

    Expected Outcome: Returns relative import with submodule appended
    """
    # Arrange
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        businessapi_root = project_root / "businessapi"

        # Create directory structure
        (businessapi_root / "models").mkdir(parents=True)

        context = RenderContext(
            core_package_name="..custom_core",
            package_root_for_generated_code=str(businessapi_root),
            overall_project_root=str(project_root),
        )
        context.set_current_file(str(businessapi_root / "models" / "user.py"))

        # Act
        result = context.get_core_import_path("schemas")

        # Assert
        assert result == "..custom_core.schemas", f"Expected '..custom_core.schemas', got '{result}'"


def test_get_core_import_path__nested_submodule__handles_dots():
    """
    Scenario: Submodule contains dots (e.g., auth.plugins)

    Expected Outcome: Correctly handles nested submodule path
    """
    # Arrange
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        businessapi_root = project_root / "businessapi"
        core_root = project_root / "core"

        # Create directory structure
        businessapi_root.mkdir(parents=True)
        core_root.mkdir(parents=True)

        context = RenderContext(
            core_package_name="core",
            package_root_for_generated_code=str(businessapi_root),
            overall_project_root=str(project_root),
        )
        context.set_current_file(str(businessapi_root / "client.py"))

        # Act
        result = context.get_core_import_path("auth.plugins")

        # Assert
        assert result == "..core.auth.plugins", f"Expected '..core.auth.plugins', got '{result}'"


def test_get_core_import_path__context_not_set__falls_back_to_absolute():
    """
    Scenario: Context not fully initialized (no current_file set)

    Expected Outcome: Falls back to absolute import as safety measure
    """
    # Arrange
    context = RenderContext(
        core_package_name="core",
        package_root_for_generated_code=None,
        overall_project_root=None,
    )
    # Don't set current_file

    # Act
    result = context.get_core_import_path("schemas")

    # Assert
    # Should fall back to absolute import when context not fully set
    assert result == "core.schemas", f"Expected 'core.schemas' (fallback), got '{result}'"
