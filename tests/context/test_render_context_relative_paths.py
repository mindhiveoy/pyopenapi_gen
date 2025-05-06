from pathlib import Path

import pytest

from pyopenapi_gen.context.render_context import RenderContext

# Use POSIX paths for consistency in tests, os.path should handle separators
# MOCK_PACKAGE_ROOT = "/project/src/generated_client/api"
# MOCK_OVERALL_ROOT = "/project/src"


@pytest.fixture
def context(tmp_path: Path) -> RenderContext:
    # Use tmp_path as the overall project root for testing purposes
    # The generated package root will be a subdirectory within tmp_path
    generated_package_root = tmp_path / "generated_client" / "api"
    generated_package_root.mkdir(parents=True, exist_ok=True)  # Ensure it exists

    ctx = RenderContext(package_root_for_generated_code=str(generated_package_root), overall_project_root=str(tmp_path))
    return ctx


@pytest.mark.parametrize(
    "current_file_rel_path, target_logical_module, expected_rel_import",
    [
        # === Cases relevant to our structure ===
        # client.py -> endpoints/default.py
        ("client.py", "endpoints.default", ".endpoints.default"),
        # endpoints/default.py -> models/item.py
        ("endpoints/default.py", "models.item", "..models.item"),
        # models/item.py -> models/base.py
        ("models/item.py", "models.base", ".base"),
        # client.py -> models/item.py
        ("client.py", "models.item", ".models.item"),
        # endpoints/default.py -> core (should NOT use this func, but test robustness)
        # This function assumes target is relative to package_root, so core won't resolve.
        # ("endpoints/default.py", "custom_core.schemas", None),
        # === General Cases ===
        # Same directory
        ("endpoints/utils.py", "endpoints.helpers", ".helpers"),
        # Child directory
        ("client.py", "endpoints.sub.helpers", ".endpoints.sub.helpers"),
        # Parent directory
        ("endpoints/sub/helpers.py", "endpoints.utils", "..utils"),
        # Grandparent directory's sibling
        ("endpoints/sub/helpers.py", "models.item", "...models.item"),
        # Importing package from module
        ("endpoints/default.py", "models", "..models"),  # Target is models dir
        # Importing module from package init
        ("endpoints/__init__.py", "endpoints.default", ".default"),
        # Importing sibling package from package init
        ("endpoints/__init__.py", "models", "..models"),
        # Root importing child
        ("__init__.py", "endpoints.default", ".endpoints.default"),
        # === Edge Cases ===
        # Importing self (should be handled, likely return None or error)
        ("endpoints/default.py", "endpoints.default", None),
    ],
)
def test_calculate_relative_path(
    context: RenderContext,
    tmp_path: Path,
    current_file_rel_path: str,
    target_logical_module: str,
    expected_rel_import: str | None,
) -> None:
    """
    Tests RenderContext.calculate_relative_path_for_internal_module for various scenarios.
    """
    assert context.package_root_for_generated_code is not None, (
        "Test setup error: package_root_for_generated_code should be set"
    )
    generated_package_root = Path(context.package_root_for_generated_code)
    current_abs_path = generated_package_root / current_file_rel_path
    context.set_current_file(str(current_abs_path))

    # Simulate existence using tmp_path
    if expected_rel_import is not None:
        target_parts = target_logical_module.split(".")
        # Resolve target relative to the *generated package root*
        mock_target_path_base = generated_package_root.joinpath(*target_parts)
        mock_target_path_py = mock_target_path_base.with_suffix(".py")
        mock_target_path_dir = mock_target_path_base

        # Ensure parent directory exists before creating file/dir
        if target_parts[-1].islower():  # Assume file
            mock_target_path_py.parent.mkdir(parents=True, exist_ok=True)
            mock_target_path_py.touch()
        else:  # Assume package directory
            mock_target_path_dir.mkdir(parents=True, exist_ok=True)
            (mock_target_path_dir / "__init__.py").touch()

    # Ensure current file's directory exists
    current_abs_path.parent.mkdir(parents=True, exist_ok=True)
    if "__init__" not in current_abs_path.name:
        current_abs_path.touch()

    # Act
    result = context.calculate_relative_path_for_internal_module(target_logical_module)

    # Assert
    assert result == expected_rel_import
    # No cleanup needed, tmp_path handles it
