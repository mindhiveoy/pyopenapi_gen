"""Tests for __init__ module."""


import pytest


def test_package_imports():
    """Scenario: Import main package."""
    import pyopenapi_gen

    # Expected Outcome: Package imports successfully
    assert hasattr(pyopenapi_gen, "__version__")
    assert hasattr(pyopenapi_gen, "HTTPMethod")
    assert hasattr(pyopenapi_gen, "IRSpec")


def test_version_attribute():
    """Scenario: Check package version."""
    import pyopenapi_gen

    # Expected Outcome: Version is a string
    assert isinstance(pyopenapi_gen.__version__, str)
    assert len(pyopenapi_gen.__version__) > 0


def test_lazy_loading_load_ir_from_spec():
    """Scenario: Test lazy loading of load_ir_from_spec."""
    import pyopenapi_gen

    # Act: Access lazy-loaded function
    func = pyopenapi_gen.load_ir_from_spec

    # Expected Outcome: Function is imported and callable
    assert callable(func)
    assert func.__name__ == "load_ir_from_spec"


def test_lazy_loading_warning_collector():
    """Scenario: Test lazy loading of WarningCollector."""
    import pyopenapi_gen

    # Act: Access lazy-loaded class
    cls = pyopenapi_gen.WarningCollector

    # Expected Outcome: Class is imported and instantiable
    assert callable(cls)
    assert cls.__name__ == "WarningCollector"


def test_getattr_nonexistent_attribute():
    """Scenario: Access non-existent attribute."""
    import pyopenapi_gen

    # Expected Outcome: AttributeError is raised
    with pytest.raises(AttributeError, match="has no attribute 'nonexistent'"):
        _ = pyopenapi_gen.nonexistent


def test_dir_function():
    """Scenario: Test __dir__ function."""
    import pyopenapi_gen

    # Act: Get directory listing
    attrs = dir(pyopenapi_gen)

    # Expected Outcome: All __all__ items are included
    expected_attrs = [
        "HTTPMethod",
        "IRParameter",
        "IRResponse",
        "IROperation",
        "IRSchema",
        "IRSpec",
        "IRRequestBody",
        "load_ir_from_spec",
        "WarningCollector",
    ]

    for attr in expected_attrs:
        assert attr in attrs


def test_all_exports():
    """Scenario: Test all exported items are accessible."""
    import pyopenapi_gen

    # Expected Outcome: All __all__ items can be accessed
    for name in pyopenapi_gen.__all__:
        attr = getattr(pyopenapi_gen, name)
        assert attr is not None


def test_ir_classes_import():
    """Scenario: Test IR classes are properly imported."""
    from pyopenapi_gen import IROperation, IRParameter, IRRequestBody, IRResponse, IRSchema, IRSpec

    # Expected Outcome: All IR classes are available
    assert IRSpec.__name__ == "IRSpec"
    assert IRSchema.__name__ == "IRSchema"
    assert IROperation.__name__ == "IROperation"
    assert IRParameter.__name__ == "IRParameter"
    assert IRResponse.__name__ == "IRResponse"
    assert IRRequestBody.__name__ == "IRRequestBody"


def test_http_method_import():
    """Scenario: Test HTTPMethod is properly imported."""
    from pyopenapi_gen import HTTPMethod

    # Expected Outcome: HTTPMethod enum is available
    assert HTTPMethod.__name__ == "HTTPMethod"
    assert hasattr(HTTPMethod, "GET")
    assert hasattr(HTTPMethod, "POST")
