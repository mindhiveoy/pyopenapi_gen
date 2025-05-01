import sys

from pyopenapi_gen.core.utils import (
    Formatter,
    ImportCollector,
    KwargsBuilder,
    NameSanitizer,
    ParamSubstitutor,
)
from pytest import MonkeyPatch


def test_sanitize_module_name() -> None:
    # Basic conversions
    assert NameSanitizer.sanitize_module_name("Vector Databases") == "vector_databases"
    assert NameSanitizer.sanitize_module_name("  My-API.Client!! ") == "my_api_client"
    # Leading digits and keywords
    assert NameSanitizer.sanitize_module_name("123Test") == "_123_test"
    assert NameSanitizer.sanitize_module_name("class") == "class_"


def test_sanitize_class_name() -> None:
    # PascalCase conversion
    assert NameSanitizer.sanitize_class_name("vector databases") == "VectorDatabases"
    assert NameSanitizer.sanitize_class_name("my-api_client") == "MyApiClient"
    # Leading digits and keywords
    assert NameSanitizer.sanitize_class_name("123test") == "_123test"
    assert NameSanitizer.sanitize_class_name("class") == "Class_"


def test_sanitize_filename() -> None:
    assert NameSanitizer.sanitize_filename("Test Name") == "test_name.py"
    assert NameSanitizer.sanitize_filename("AnotherExample", suffix=".py") == "another_example.py"


def test_param_substitutor_render_path() -> None:
    template = "/users/{userId}/items/{itemId}"
    values = {"userId": 42, "itemId": "abc"}
    assert ParamSubstitutor.render_path(template, values) == "/users/42/items/abc"
    # Missing values should leave placeholder intact
    assert ParamSubstitutor.render_path("/test/{foo}", {}) == "/test/{foo}"


def test_kwargs_builder() -> None:
    # Only params
    builder = KwargsBuilder().with_params(a=1, b=None, c="x")
    assert builder.build() == {"params": {"a": 1, "c": "x"}}

    # Only json
    builder = KwargsBuilder().with_json({"k": "v"})
    assert builder.build() == {"json": {"k": "v"}}

    # Chaining params then json
    builder = KwargsBuilder().with_params(x=0).with_json({"foo": "bar"})
    assert builder.build() == {"params": {"x": 0}, "json": {"foo": "bar"}}


def test_formatter__valid_python_code__returns_formatted_code() -> None:
    """
    Scenario:
        Format a valid Python code string using Formatter when Black is available.
    Expected Outcome:
        The returned code is valid Python and contains the function definition.
    """
    # Arrange
    code = "def foo():\n    return  1\n"
    formatter = Formatter()

    # Act
    formatted = formatter.format(code)

    # Assert
    # The formatted code should contain the function definition and be valid Python
    assert "def foo()" in formatted
    # Try compiling to ensure it's valid Python
    compile(formatted, "<string>", "exec")


def test_formatter__black_not_installed__returns_original_code(monkeypatch: MonkeyPatch) -> None:
    """
    Scenario:
        Format code when Black is not installed (simulate by monkeypatching Formatter internals).
    Expected Outcome:
        The original code is returned unchanged.
    """
    # Arrange
    code = "def foo():\n    return 1\n"
    formatter = Formatter()
    monkeypatch.setattr(formatter, "_format_str", None)
    monkeypatch.setattr(formatter, "_file_mode", None)

    # Act
    formatted = formatter.format(code)

    # Assert
    assert formatted == code


def test_formatter__black_raises_exception__returns_original_code(monkeypatch: MonkeyPatch) -> None:
    """
    Scenario:
        Format code when Black raises an exception (simulate by monkeypatching _format_str).
    Expected Outcome:
        The original code is returned unchanged.
    """
    # Arrange
    code = "def foo():\n    return 1\n"
    formatter = Formatter()

    def raise_exc(*_args: object, **_kwargs: object) -> None:
        raise Exception("Black error")

    monkeypatch.setattr(formatter, "_format_str", raise_exc)
    # _file_mode must not be None for this branch
    if formatter._file_mode is None:

        class Dummy:
            pass

        formatter._file_mode = Dummy()

    # Act
    formatted = formatter.format(code)

    # Assert
    assert formatted == code


def test_import_collector__import_as_module__produces_import_statement() -> None:
    """
    Scenario:
        Add an import where the name is the same as the module (e.g., 'os', 'os').
        This should produce an 'import os' statement.
    Expected Outcome:
        The import statement list contains 'import os'.
    """
    # Arrange
    collector = ImportCollector()
    collector.add_import("os", "os")
    # Act
    stmts = collector.get_import_statements()
    # Assert
    assert "import os" in stmts


def test_sanitize_class_name__keyword__appends_underscore() -> None:
    """
    Scenario:
        Sanitize a class name that is a Python keyword (e.g., 'class').
    Expected Outcome:
        The result is the capitalized keyword with an underscore appended (e.g., 'Class_').
    """
    # Arrange/Act
    result = NameSanitizer.sanitize_class_name("class")
    # Assert
    assert result == "Class_"


def test_formatter__importerror_branch__returns_original_code(monkeypatch: MonkeyPatch) -> None:
    """
    Scenario:
        Simulate ImportError in Formatter's __init__ (Black not installed).
    Expected Outcome:
        Formatter.format returns the original code unchanged.
    """
    # Arrange
    # Patch sys.modules to simulate ImportError for 'black'
    original_black = sys.modules.get("black")
    if "black" in sys.modules:
        del sys.modules["black"]
    try:
        # Re-import Formatter to trigger ImportError
        import importlib

        utils_mod = importlib.import_module("pyopenapi_gen.utils")
        FormatterReloaded = utils_mod.Formatter
        formatter = FormatterReloaded()
        code = "def foo():\n    return 1\n"
        # Act
        result = formatter.format(code)
        # Assert
        assert result == code
    finally:
        if original_black is not None:
            sys.modules["black"] = original_black
        else:
            del sys.modules["black"]
