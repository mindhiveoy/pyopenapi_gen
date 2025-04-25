import pytest

from pyopenapi_gen.utils import NameSanitizer, ParamSubstitutor, KwargsBuilder


def test_sanitize_module_name():
    # Basic conversions
    assert NameSanitizer.sanitize_module_name("Vector Databases") == "vector_databases"
    assert NameSanitizer.sanitize_module_name("  My-API.Client!! ") == "my_api_client"
    # Leading digits and keywords
    assert NameSanitizer.sanitize_module_name("123Test") == "_123test"
    assert NameSanitizer.sanitize_module_name("class") == "class_"


def test_sanitize_class_name():
    # PascalCase conversion
    assert NameSanitizer.sanitize_class_name("vector databases") == "VectorDatabases"
    assert NameSanitizer.sanitize_class_name("my-api_client") == "MyApi_client"
    # Leading digits and keywords
    assert NameSanitizer.sanitize_class_name("123test") == "_123test"
    assert NameSanitizer.sanitize_class_name("class") == "Class"


def test_sanitize_filename():
    assert NameSanitizer.sanitize_filename("Test Name") == "test_name.py"
    assert (
        NameSanitizer.sanitize_filename("AnotherExample", suffix=".py")
        == "anotherexample.py"
    )


def test_param_substitutor_render_path():
    template = "/users/{userId}/items/{itemId}"
    values = {"userId": 42, "itemId": "abc"}
    assert ParamSubstitutor.render_path(template, values) == "/users/42/items/abc"
    # Missing values should leave placeholder intact
    assert ParamSubstitutor.render_path("/test/{foo}", {}) == "/test/{foo}"


def test_kwargs_builder():
    # Only params
    builder = KwargsBuilder().with_params(a=1, b=None, c="x")
    assert builder.build() == {"params": {"a": 1, "c": "x"}}

    # Only json
    builder = KwargsBuilder().with_json({"k": "v"})
    assert builder.build() == {"json": {"k": "v"}}

    # Chaining params then json
    builder = KwargsBuilder().with_params(x=0).with_json({"foo": "bar"})
    assert builder.build() == {"params": {"x": 0}, "json": {"foo": "bar"}}
