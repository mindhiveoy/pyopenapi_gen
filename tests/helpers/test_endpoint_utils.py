import pytest
from pyopenapi_gen.helpers.endpoint_utils import (
    format_method_args,
    get_model_stub_args,
    merge_params_with_model_fields,
)
import types


def test_format_method_args__required_only__returns_correct_signature():
    """
    Scenario:
        All parameters are required. We want to ensure the function returns a comma-separated list with type annotations and no defaults.

    Expected Outcome:
        The function returns the correct argument string for required parameters only.
    """
    # Arrange
    params = [
        {"name": "foo", "type": "str", "default": None, "required": True},
        {"name": "bar", "type": "int", "default": None, "required": True},
    ]
    # Act
    result = format_method_args(params)
    # Assert
    assert result == "foo: str, bar: int"


def test_format_method_args__optional_only__returns_correct_signature():
    """
    Scenario:
        All parameters are optional. We want to ensure the function returns a comma-separated list with type annotations and defaults.

    Expected Outcome:
        The function returns the correct argument string for optional parameters only.
    """
    # Arrange
    params = [
        {"name": "foo", "type": "str", "default": '"abc"', "required": False},
        {"name": "bar", "type": "int", "default": "0", "required": False},
    ]
    # Act
    result = format_method_args(params)
    # Assert
    assert result == 'foo: str = "abc", bar: int = 0'


def test_format_method_args__mixed_required_and_optional__returns_correct_order():
    """
    Scenario:
        Parameters are a mix of required and optional. We want to ensure required come first, then optional, all with correct type annotations and defaults.

    Expected Outcome:
        The function returns the correct argument string with required first, then optional.
    """
    # Arrange
    params = [
        {"name": "foo", "type": "str", "default": None, "required": True},
        {"name": "bar", "type": "int", "default": "0", "required": False},
        {"name": "baz", "type": "float", "default": None, "required": True},
        {"name": "qux", "type": "bool", "default": "False", "required": False},
    ]
    # Act
    result = format_method_args(params)
    # Assert
    assert result == "foo: str, baz: float, bar: int = 0, qux: bool = False"


def test_format_method_args__empty_list__returns_empty_string():
    """
    Scenario:
        The parameter list is empty. We want to ensure the function returns an empty string.

    Expected Outcome:
        The function returns an empty string.
    """
    # Arrange
    params = []
    # Act
    result = format_method_args(params)
    # Assert
    assert result == ""


def make_schema(properties, required=None):
    schema = types.SimpleNamespace()
    schema.properties = properties
    schema.required = required or []
    return schema


def make_pschema(type_):
    ps = types.SimpleNamespace()
    ps.type = type_
    return ps


def test_get_model_stub_args__all_fields_present__uses_args():
    """
    Scenario:
        All required fields are present in present_args.
    Expected Outcome:
        The function uses the variable names for all fields.
    """
    # Arrange
    schema = make_schema(
        {"foo": make_pschema("string"), "bar": make_pschema("integer")}, ["foo", "bar"]
    )
    present_args = {"foo", "bar"}
    # Act
    result = get_model_stub_args(schema, None, present_args)
    # Assert
    assert result == "foo=foo, bar=bar"


def test_get_model_stub_args__some_fields_missing__uses_defaults():
    """
    Scenario:
        Some required fields are missing from present_args.
    Expected Outcome:
        The function uses the variable for present fields and safe defaults for missing ones.
    """
    # Arrange
    schema = make_schema(
        {"foo": make_pschema("string"), "bar": make_pschema("integer")}, ["foo", "bar"]
    )
    present_args = {"foo"}
    # Act
    result = get_model_stub_args(schema, None, present_args)
    # Assert
    assert result == "foo=foo, bar=0"


def test_get_model_stub_args__all_fields_missing__all_defaults():
    """
    Scenario:
        No required fields are present in present_args.
    Expected Outcome:
        The function uses safe defaults for all required fields.
    """
    # Arrange
    schema = make_schema(
        {"foo": make_pschema("string"), "bar": make_pschema("integer")}, ["foo", "bar"]
    )
    present_args = set()
    # Act
    result = get_model_stub_args(schema, None, present_args)
    # Assert
    assert result == 'foo="", bar=0'


def test_get_model_stub_args__optional_fields__uses_none():
    """
    Scenario:
        Some fields are not required.
    Expected Outcome:
        The function uses None for optional fields.
    """
    # Arrange
    schema = make_schema(
        {"foo": make_pschema("string"), "bar": make_pschema("integer")}, ["foo"]
    )
    present_args = set()
    # Act
    result = get_model_stub_args(schema, None, present_args)
    # Assert
    assert result == 'foo="", bar=None'


def test_get_model_stub_args__unknown_type__uses_ellipsis():
    """
    Scenario:
        A required field has an unknown type.
    Expected Outcome:
        The function uses ... for unknown types.
    """
    # Arrange
    schema = make_schema({"foo": make_pschema(None)}, ["foo"])
    present_args = set()
    # Act
    result = get_model_stub_args(schema, None, present_args)
    # Assert
    assert result == "foo=..."


def test_get_model_stub_args__no_properties__returns_empty():
    """
    Scenario:
        The schema has no properties.
    Expected Outcome:
        The function returns an empty string.
    """
    # Arrange
    schema = make_schema({})
    present_args = set()
    # Act
    result = get_model_stub_args(schema, None, present_args)
    # Assert
    assert result == ""


def test_merge_params_with_model_fields__endpoint_only__returns_endpoint_params():
    """
    Scenario:
        The operation has only endpoint parameters, and the model has no required fields.
    Expected Outcome:
        The function returns only the endpoint parameters.
    """

    # Arrange
    class DummyOp:
        parameters = [
            types.SimpleNamespace(
                name="foo", required=True, schema=types.SimpleNamespace(type="string")
            ),
            types.SimpleNamespace(
                name="bar", required=False, schema=types.SimpleNamespace(type="integer")
            ),
        ]

    op = DummyOp()
    model_schema = types.SimpleNamespace(properties={}, required=[])
    context = types.SimpleNamespace()
    # Act
    result = merge_params_with_model_fields(op, model_schema, context)
    # Assert
    assert {p["name"] for p in result} == {"foo", "bar"}


def test_merge_params_with_model_fields__model_only__returns_model_fields():
    """
    Scenario:
        The operation has no endpoint parameters, and the model has required fields.
    Expected Outcome:
        The function returns all required model fields as parameters.
    """

    # Arrange
    class DummyOp:
        parameters = []

    op = DummyOp()
    model_schema = types.SimpleNamespace(
        properties={
            "foo": types.SimpleNamespace(type="string"),
            "bar": types.SimpleNamespace(type="integer"),
        },
        required=["foo", "bar"],
    )
    context = types.SimpleNamespace()
    # Act
    result = merge_params_with_model_fields(op, model_schema, context)
    # Assert
    assert {p["name"] for p in result} == {"foo", "bar"}
    assert all(p["required"] for p in result)


def test_merge_params_with_model_fields__overlapping_names__endpoint_takes_precedence():
    """
    Scenario:
        The operation and model have overlapping required field names.
    Expected Outcome:
        The function includes the endpoint parameter only once, with endpoint param taking precedence.
    """

    # Arrange
    class DummyOp:
        parameters = [
            types.SimpleNamespace(
                name="foo", required=True, schema=types.SimpleNamespace(type="string")
            ),
        ]

    op = DummyOp()
    model_schema = types.SimpleNamespace(
        properties={
            "foo": types.SimpleNamespace(type="string"),
            "bar": types.SimpleNamespace(type="integer"),
        },
        required=["foo", "bar"],
    )
    context = types.SimpleNamespace()
    # Act
    result = merge_params_with_model_fields(op, model_schema, context)
    # Assert
    names = [p["name"] for p in result]
    assert names.count("foo") == 1
    assert set(names) == {"foo", "bar"}


def test_merge_params_with_model_fields__optional_model_fields__only_required_merged():
    """
    Scenario:
        The model has both required and optional fields.
    Expected Outcome:
        Only required model fields are merged as parameters.
    """

    # Arrange
    class DummyOp:
        parameters = []

    op = DummyOp()
    model_schema = types.SimpleNamespace(
        properties={
            "foo": types.SimpleNamespace(type="string"),
            "bar": types.SimpleNamespace(type="integer"),
        },
        required=["foo"],
    )
    context = types.SimpleNamespace()
    # Act
    result = merge_params_with_model_fields(op, model_schema, context)
    # Assert
    names = [p["name"] for p in result]
    assert "foo" in names
    assert "bar" not in names


def test_merge_params_with_model_fields__empty_everything__returns_empty():
    """
    Scenario:
        Both the operation and model have no parameters or fields.
    Expected Outcome:
        The function returns an empty list.
    """

    # Arrange
    class DummyOp:
        parameters = []

    op = DummyOp()
    model_schema = types.SimpleNamespace(properties={}, required=[])
    context = types.SimpleNamespace()
    # Act
    result = merge_params_with_model_fields(op, model_schema, context)
    # Assert
    assert result == []
