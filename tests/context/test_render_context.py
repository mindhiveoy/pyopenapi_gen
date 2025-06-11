from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pyopenapi_gen.context.file_manager import FileManager
from pyopenapi_gen.context.import_collector import ImportCollector
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.code_writer import CodeWriter


@pytest.fixture
def mock_file_manager() -> MagicMock:
    return MagicMock(spec=FileManager)


@pytest.fixture
def base_render_context(tmp_path: Path, mock_file_manager: MagicMock) -> RenderContext:
    # Default setup: project_root is tmp_path, generated code is in 'out' subdir.
    project_root = tmp_path
    gen_pkg_root = project_root / "out"
    gen_pkg_root.mkdir(parents=True, exist_ok=True)

    # Create a dummy core dir if needed for some tests, though RenderContext itself
    # doesn't interact with it beyond knowing its name.
    # (gen_pkg_root / "core").mkdir(exist_ok=True)

    return RenderContext(
        file_manager=mock_file_manager,
        core_package_name="out.core",  # Assuming core is part of the generated 'out' package
        package_root_for_generated_code=str(gen_pkg_root),
        overall_project_root=str(project_root),
    )


class TestRenderContextGetCurrentModuleDotPath:
    def test_get_current_module_dot_path__model_in_subdir(
        self, base_render_context: RenderContext, tmp_path: Path
    ) -> None:
        """
        Scenario: current_file is project_root/out/models/schema_name.py
                  package_root_for_generated_code is project_root/out
                  overall_project_root is project_root
        Expected: out.models.schema_name
        """
        # Arrange
        current_file = tmp_path / "out" / "models" / "schema_name.py"
        (tmp_path / "out" / "models").mkdir(parents=True, exist_ok=True)
        current_file.touch()
        base_render_context.set_current_file(str(current_file))

        # Act
        module_path = base_render_context.get_current_module_dot_path()

        # Assert
        assert module_path == "out.models.schema_name"

    def test_get_current_module_dot_path__init_in_subdir(
        self, base_render_context: RenderContext, tmp_path: Path
    ) -> None:
        """
        Scenario: current_file is project_root/out/models/__init__.py
        Expected: out.models
        """
        # Arrange
        current_file = tmp_path / "out" / "models" / "__init__.py"
        (tmp_path / "out" / "models").mkdir(parents=True, exist_ok=True)
        current_file.touch()
        base_render_context.set_current_file(str(current_file))

        # Act
        module_path = base_render_context.get_current_module_dot_path()

        # Assert
        assert module_path == "out.models"

    def test_get_current_module_dot_path__init_at_pkg_root(
        self, base_render_context: RenderContext, tmp_path: Path
    ) -> None:
        """
        Scenario: current_file is project_root/out/__init__.py
        Expected: out
        """
        # Arrange
        current_file = tmp_path / "out" / "__init__.py"
        current_file.touch()  # out dir already exists from fixture
        base_render_context.set_current_file(str(current_file))

        # Act
        module_path = base_render_context.get_current_module_dot_path()

        # Assert
        assert module_path == "out"

    def test_get_current_module_dot_path__file_at_pkg_root(
        self, base_render_context: RenderContext, tmp_path: Path
    ) -> None:
        """
        Scenario: current_file is project_root/out/client.py
        Expected: out.client
        """
        # Arrange
        current_file = tmp_path / "out" / "client.py"
        current_file.touch()
        base_render_context.set_current_file(str(current_file))

        # Act
        module_path = base_render_context.get_current_module_dot_path()

        # Assert
        assert module_path == "out.client"

    def test_get_current_module_dot_path__no_current_file(self, base_render_context: RenderContext) -> None:
        """Scenario: current_file not set. Expected: None"""
        base_render_context.current_file = None
        assert base_render_context.get_current_module_dot_path() is None

    def test_get_current_module_dot_path__pkg_root_is_none_but_overall_root_is_set(
        self, base_render_context: RenderContext, tmp_path: Path
    ) -> None:
        """
        Scenario: package_root_for_generated_code is None, but overall_project_root is set.
        Expected: Module path should be derived from overall_project_root.
        """
        base_render_context.package_root_for_generated_code = None
        current_file = tmp_path / "out" / "models" / "a.py"  # Needs a current file to attempt
        current_file.parent.mkdir(parents=True, exist_ok=True)
        current_file.touch()
        base_render_context.set_current_file(str(current_file))
        # current_file is tmp_path/out/models/a.py, overall_project_root is tmp_path (from fixture)
        # So, relative path is "out/models/a.py" -> "out.models.a"
        assert base_render_context.get_current_module_dot_path() == "out.models.a"

    def test_get_current_module_dot_path__file_not_under_pkg_root(
        self, base_render_context: RenderContext, tmp_path: Path
    ) -> None:
        """
        Scenario: current_file is outside package_root_for_generated_code, but under overall_project_root.
                  e.g. overall_project_root = /proj, pkg_root_gen = /proj/out, current_file = /proj/src/tool.py
        Expected: src.tool (derived from overall_project_root)
        """
        # Arrange
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        current_file_outside = src_dir / "tool.py"
        current_file_outside.touch()
        base_render_context.set_current_file(str(current_file_outside))

        # Act
        module_path = base_render_context.get_current_module_dot_path()

        # Assert
        assert module_path == "src.tool"


class TestRenderContextCalculateRelativePath:
    # Helper to set up context for these specific tests
    def _setup_context_for_rel_path(self, context: RenderContext, current_file_rel_path: str, tmp_path: Path) -> None:
        assert (
            context.package_root_for_generated_code is not None
        ), "package_root_for_generated_code cannot be None for this test setup"
        gen_pkg_root_path = Path(context.package_root_for_generated_code)
        current_file_abs = gen_pkg_root_path / current_file_rel_path
        current_file_abs.parent.mkdir(parents=True, exist_ok=True)
        current_file_abs.touch()  # Ensure file exists for os.path.abspath consistency
        context.set_current_file(str(current_file_abs))

        # Also ensure target module base dir exists for os.path.isdir checks in calc method
        # (models, endpoints etc.)
        (gen_pkg_root_path / "models").mkdir(exist_ok=True)
        (gen_pkg_root_path / "endpoints").mkdir(exist_ok=True)
        (gen_pkg_root_path / "core").mkdir(exist_ok=True)

    @pytest.mark.parametrize(
        "current_file_rel, target_logical, expected_rel_path",
        [
            ("models/a.py", "models.b", ".b"),
            ("models/a.py", "models.sub.c", ".sub.c"),
            ("endpoints/a.py", "models.b", "..models.b"),
            ("main_client.py", "models.b", ".models.b"),  # file at pkg root
            ("models/sub/a.py", "models.b", "..b"),
            ("models/sub/a.py", "endpoints.b", "...endpoints.b"),
            ("core/http.py", "core.auth", ".auth"),  # Sibling in core
        ],
    )
    def test_calculate_relative_path__various_scenarios(
        self,
        base_render_context: RenderContext,
        tmp_path: Path,
        current_file_rel: str,
        target_logical: str,
        expected_rel_path: str,
    ) -> None:
        self._setup_context_for_rel_path(base_render_context, current_file_rel, tmp_path)
        assert base_render_context.package_root_for_generated_code is not None  # For type checker
        target_parts = target_logical.split(".")
        potential_target_path = (
            Path(base_render_context.package_root_for_generated_code)
            / Path(*target_parts[:-1])
            / (target_parts[-1] + ".py")
        )
        potential_target_dir_path = Path(base_render_context.package_root_for_generated_code) / Path(*target_parts)

        if not potential_target_path.parent.exists():  # ensure parent dir for file exists
            potential_target_path.parent.mkdir(parents=True, exist_ok=True)

        # Heuristic: if it ends in common module names like 'py' or involves typical paths, touch it
        # This is to satisfy the os.path.isfile check in the method.
        # A more robust test might mock os.path.isfile/isdir.
        if "." not in target_parts[-1]:  # if last part is likely a module name
            potential_target_path.touch()

        result = base_render_context.calculate_relative_path_for_internal_module(target_logical)
        assert result == expected_rel_path

    def test_calculate_relative_path__self_import(self, base_render_context: RenderContext, tmp_path: Path) -> None:
        self._setup_context_for_rel_path(base_render_context, "models/a.py", tmp_path)
        # Target is the same as current_file (effectively)
        result = base_render_context.calculate_relative_path_for_internal_module("models.a")
        assert result is None

    def test_calculate_relative_path__no_current_file(self, base_render_context: RenderContext) -> None:
        base_render_context.current_file = None
        result = base_render_context.calculate_relative_path_for_internal_module("models.a")
        assert result is None

    def test_calculate_relative_path__no_pkg_root(self, base_render_context: RenderContext, tmp_path: Path) -> None:
        base_render_context.package_root_for_generated_code = None
        # Need to set a current file for the method to proceed up to the check
        # but we don't need to use Path() on the None package_root itself for this test setup.
        current_file_abs = tmp_path / "some_file.py"
        current_file_abs.touch()

        result = base_render_context.calculate_relative_path_for_internal_module("models.a")
        assert result is None


class TestRenderContextAddImport:
    def test_add_import__core_module(self, base_render_context: RenderContext) -> None:
        """Core imports should be absolute using context.core_package_name."""
        base_render_context.core_package_name = "out.core"  # Explicitly set for clarity
        base_render_context.add_import("out.core.http", "HttpClient")

        collector: ImportCollector = base_render_context.import_collector
        assert collector.imports == {"out.core.http": {"HttpClient"}}
        assert not collector.relative_imports

    def test_add_import__core_module_is_different_package(self, tmp_path: Path, mock_file_manager: MagicMock) -> None:
        """Core imports from an external core package."""
        project_root = tmp_path
        client_gen_root = project_root / "my_client"
        client_gen_root.mkdir()

        # Core package is elsewhere, e.g. 'shared_lib.core_pkg'
        # RenderContext needs overall_project_root to make sense of this if it were
        # to try to find its path, but for add_import, it just uses the string.
        context = RenderContext(
            file_manager=mock_file_manager,
            core_package_name="shared_lib.core_pkg",
            package_root_for_generated_code=str(client_gen_root),
            overall_project_root=str(project_root),
        )
        context.set_current_file(str(client_gen_root / "endpoints.py"))
        context.add_import("shared_lib.core_pkg.auth", "AuthUtil")

        collector: ImportCollector = context.import_collector
        assert collector.imports == {"shared_lib.core_pkg.auth": {"AuthUtil"}}
        assert not collector.relative_imports

    def test_add_import__stdlib_module(self, base_render_context: RenderContext) -> None:
        """Stdlib imports should be absolute."""
        base_render_context.add_import("typing", "List")
        base_render_context.add_import("os.path", "join")

        collector: ImportCollector = base_render_context.import_collector
        assert collector.imports == {"typing": {"List"}, "os.path": {"join"}}
        assert not collector.relative_imports

    def test_add_import__known_third_party(self, base_render_context: RenderContext) -> None:
        """Known third-party imports should be absolute."""
        base_render_context.add_import("httpx", "AsyncClient")

        collector: ImportCollector = base_render_context.import_collector
        assert collector.imports == {"httpx": {"AsyncClient"}}
        assert not collector.relative_imports

    def test_add_import__internal_made_relative_by_default(
        self, base_render_context: RenderContext, tmp_path: Path
    ) -> None:
        """
        Current: /tmp_proj/pkg/endpoints/user_endpoints.py
        Target:  pkg.models.user -> should be from ..models.user import User (relative by default for internal modules)
        Pkg root: /tmp_proj/pkg
        Project root: /tmp_proj
        """
        pkg_dir = tmp_path / "pkg"
        endpoints_dir = pkg_dir / "endpoints"
        models_dir = pkg_dir / "models"
        endpoints_dir.mkdir(parents=True, exist_ok=True)
        models_dir.mkdir(parents=True, exist_ok=True)

        current_file = endpoints_dir / "user_endpoints.py"
        current_file.touch()

        # The file that would be imported from
        target_model_file = models_dir / "user.py"
        target_model_file.touch()  # Create the target file

        # Use a fresh context configured for this specific test structure (default use_absolute_imports=True)
        context = RenderContext(
            package_root_for_generated_code=str(pkg_dir),
            overall_project_root=str(tmp_path),
            # core_package_name can be default or e.g. "pkg.core" if relevant for other assertions
        )
        context.set_current_file(str(current_file))

        # Act
        # logical_module "pkg.models.user" matches how ClientVisitor constructs it.
        # get_current_package_name_for_generated_code() for 'context' will be "pkg".
        context.add_import("pkg.models.user", "User")

        # Assert - Now expecting relative imports for internal modules
        collector: ImportCollector = context.import_collector
        assert not collector.imports, f"Expected no absolute imports for internal modules, got: {collector.imports}"
        assert collector.relative_imports == {
            "..models.user": {"User"}
        }, f"Expected relative imports, got: {collector.relative_imports}"

        code_writer = CodeWriter()
        code_writer.write_line(context.render_imports())
        expected_import_str = "from ..models.user import User"
        assert (
            code_writer.get_code() == expected_import_str
        ), f"Actual: '{code_writer.get_code()}', Expected: '{expected_import_str}'"
        assert context.import_collector.has_import("..models.user", "User")

    def test_add_import__internal_same_dir_uses_relative_by_default(
        self, base_render_context: RenderContext, tmp_path: Path
    ) -> None:
        """
        Current: /tmp_proj/pkg/models/main_model.py
        Target:  pkg.models.sibling_model -> should be from .sibling_model import SiblingModel (relative for same dir)
        Pkg root: /tmp_proj/pkg
        Project root: /tmp_proj
        """
        pkg_dir = tmp_path / "pkg"
        models_dir = pkg_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        current_file = models_dir / "main_model.py"
        current_file.touch()

        # The file that would be imported from
        target_sibling_model_file = models_dir / "sibling_model.py"
        target_sibling_model_file.touch()  # Ensure the target file exists

        # Use a fresh context configured for this specific test structure
        context = RenderContext(
            package_root_for_generated_code=str(pkg_dir),
            overall_project_root=str(tmp_path),
        )
        context.set_current_file(str(current_file))

        # Act
        context.add_import("pkg.models.sibling_model", "SiblingModel")

        # Assert - Now expecting relative imports for same directory
        collector: ImportCollector = context.import_collector
        assert not collector.imports, f"Expected no absolute imports for same-dir modules, got: {collector.imports}"
        assert collector.relative_imports == {
            ".sibling_model": {"SiblingModel"}
        }, f"Expected relative imports, got: {collector.relative_imports}"

        code_writer = CodeWriter()
        code_writer.write_line(context.render_imports())
        expected_import_str = "from .sibling_model import SiblingModel"
        assert (
            code_writer.get_code() == expected_import_str
        ), f"Actual: '{code_writer.get_code()}', Expected: '{expected_import_str}'"
        assert context.import_collector.has_import(".sibling_model", "SiblingModel")

    def test_add_import__self_import_is_skipped(self, base_render_context: RenderContext, tmp_path: Path) -> None:
        """Self-imports should be skipped."""
        current_file_rel = "models/user.py"
        target_logical = "out.models.user"  # Importing self

        assert base_render_context.package_root_for_generated_code is not None
        gen_pkg_root_path = Path(base_render_context.package_root_for_generated_code)
        current_file_abs = gen_pkg_root_path / current_file_rel
        current_file_abs.parent.mkdir(parents=True, exist_ok=True)
        current_file_abs.touch()
        base_render_context.set_current_file(str(current_file_abs))

        base_render_context.add_import(target_logical, "User")

        collector: ImportCollector = base_render_context.import_collector
        assert not collector.imports
        assert not collector.relative_imports  # Also ensure no relative imports added

    def test_add_import__fallback_to_absolute_if_not_core_stdlib_internal(
        self, base_render_context: RenderContext
    ) -> None:
        """Non-core, non-stdlib, non-resolvable-internal should be absolute."""
        # Current file is set, but target_logical doesn't map to a path calculate_relative_path understands easily
        # or is truly external and not in KNOWN_THIRD_PARTY
        assert base_render_context.package_root_for_generated_code is not None  # Guard for Path()
        base_render_context.set_current_file(str(Path(base_render_context.package_root_for_generated_code) / "a.py"))

        base_render_context.add_import("some_other_library.api", "Client")

        collector: ImportCollector = base_render_context.import_collector
        assert collector.imports == {"some_other_library.api": {"Client"}}
        assert not collector.relative_imports

    def test_add_typing_imports_for_type__various_types(self, base_render_context: RenderContext) -> None:
        """Test add_typing_imports_for_type method for common typing constructs."""
        type_str1 = "Optional[List[Dict[str, Any]]]"
        type_str2 = "Union[int, str, None, datetime.datetime, datetime.date]"
        type_str3 = "Tuple[str, ...]"
        type_str4 = "Callable[[int], str]"

        base_render_context.add_typing_imports_for_type(type_str1)
        base_render_context.add_typing_imports_for_type(
            type_str2
        )  # datetime.datetime will add 'datetime' from 'datetime'
        # datetime.date will add 'date' from 'datetime'
        base_render_context.add_typing_imports_for_type(type_str3)
        base_render_context.add_typing_imports_for_type(type_str4)

        collector: ImportCollector = base_render_context.import_collector

        expected_typing_imports = {"Optional", "List", "Dict", "Any", "Union", "Tuple", "Callable"}
        assert collector.imports.get("typing") == expected_typing_imports

        # Check for datetime imports
        assert "datetime" in collector.imports
        assert "datetime" in collector.imports["datetime"]  # from datetime import datetime
        assert "date" in collector.imports["datetime"]  # from datetime import date

    def test_add_plain_import(self, base_render_context: RenderContext) -> None:
        base_render_context.add_plain_import("json")
        base_render_context.add_plain_import("os")
        collector: ImportCollector = base_render_context.import_collector
        assert collector.plain_imports == {"json", "os"}

    # TODO: Add tests for conditional imports via add_conditional_import and render_imports
