from typing import Any

from pyopenapi_gen import HTTPMethod, IROperation, IRParameter, IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.helpers.endpoint_utils import (
    format_method_args,
    get_model_stub_args,
    merge_params_with_model_fields,
)


def test_format_method_args__required_only__returns_correct_signature() -> None:
    """
    Scenario:
        All parameters are required. We want to ensure the function returns a comma-separated list with type
        annotations and no defaults.

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


def test_format_method_args__optional_only__returns_correct_signature() -> None:
    """
    Scenario:
        All parameters are optional. We want to ensure the function returns a comma-separated list with
        type annotations and defaults.

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


def test_format_method_args__mixed_required_and_optional__returns_correct_order() -> None:
    """
    Scenario:
        Parameters are a mix of required and optional. We want to ensure required come first, then optional,
        all with correct type annotations and defaults.

    Expected Outcome:
        The function returns the correct argument string with required first, then optional.
    """
    # Arrange
    params: list[dict[str, Any]] = [
        {"name": "foo", "type": "str", "default": None, "required": True},
        {"name": "bar", "type": "int", "default": "0", "required": False},
        {"name": "baz", "type": "float", "default": None, "required": True},
        {"name": "qux", "type": "bool", "default": "False", "required": False},
    ]
    # Act
    result = format_method_args(params)
    # Assert
    assert result == "foo: str, baz: float, bar: int = 0, qux: bool = False"


def test_format_method_args__empty_list__returns_empty_string() -> None:
    """
    Scenario:
        The parameter list is empty. We want to ensure the function returns an empty string.

    Expected Outcome:
        The function returns an empty string.
    """
    # Arrange
    params: list[dict[str, Any]] = []
    # Act
    result = format_method_args(params)
    # Assert
    assert result == ""


def make_schema(properties: dict[str, Any], required: list[str] | None = None) -> IRSchema:
    return IRSchema(
        name=None,
        type="object",
        properties=properties,
        required=required or [],
    )


def make_pschema(type_: str) -> IRSchema:
    return IRSchema(
        name=None,
        type=type_,
        properties={},
        required=[],
    )


def test_get_model_stub_args__all_fields_present__uses_args() -> None:
    """
    Scenario:
        All required fields are present in present_args.
    Expected Outcome:
        The function uses the variable names for all fields.
    """
    # Arrange
    schema = make_schema({"foo": make_pschema("string"), "bar": make_pschema("integer")}, ["foo", "bar"])
    present_args: set[str] = {"foo", "bar"}
    context = RenderContext()
    # Act
    result = get_model_stub_args(schema, context, present_args)
    # Assert
    assert result == "foo=foo, bar=bar"


def test_get_model_stub_args__some_fields_missing__uses_defaults() -> None:
    """
    Scenario:
        Some required fields are missing from present_args.
    Expected Outcome:
        The function uses the variable for present fields and safe defaults for missing ones.
    """
    # Arrange
    schema = make_schema({"foo": make_pschema("string"), "bar": make_pschema("integer")}, ["foo", "bar"])
    present_args: set[str] = {"foo"}
    context = RenderContext()
    # Act
    result = get_model_stub_args(schema, context, present_args)
    # Assert
    assert result == "foo=foo, bar=0"


def test_get_model_stub_args__all_fields_missing__all_defaults() -> None:
    """
    Scenario:
        No required fields are present in present_args.
    Expected Outcome:
        The function uses safe defaults for all required fields.
    """
    # Arrange
    schema = make_schema({"foo": make_pschema("string"), "bar": make_pschema("integer")}, ["foo", "bar"])
    present_args: set[str] = set()
    context = RenderContext()
    # Act
    result = get_model_stub_args(schema, context, present_args)
    # Assert
    assert result == 'foo="", bar=0'


def test_get_model_stub_args__optional_fields__uses_none() -> None:
    """
    Scenario:
        Some fields are not required.
    Expected Outcome:
        The function uses None for optional fields.
    """
    # Arrange
    schema = make_schema({"foo": make_pschema("string"), "bar": make_pschema("integer")}, ["foo"])
    present_args: set[str] = set()
    context = RenderContext()
    # Act
    result = get_model_stub_args(schema, context, present_args)
    # Assert
    assert result == 'foo="", bar=None'


def test_get_model_stub_args__unknown_type__uses_ellipsis() -> None:
    """
    Scenario:
        A required field has an unknown type.
    Expected Outcome:
        The function uses ... for unknown types.
    """
    # Arrange
    schema = make_schema({"foo": IRSchema(name=None, type=None)}, ["foo"])
    present_args: set[str] = set()
    context = RenderContext()
    # Act
    result = get_model_stub_args(schema, context, present_args)
    # Assert
    assert result == "foo=..."


def test_get_model_stub_args__no_properties__returns_empty() -> None:
    """
    Scenario:
        The schema has no properties.
    Expected Outcome:
        The function returns an empty string.
    """
    # Arrange
    schema = make_schema({})
    present_args: set[str] = set()
    context = RenderContext()
    # Act
    result = get_model_stub_args(schema, context, present_args)
    # Assert
    assert result == ""


def test_merge_params_with_model_fields__endpoint_only__returns_endpoint_params() -> None:
    """
    Scenario:
        The operation has only endpoint parameters, and the model has no required fields.
    Expected Outcome:
        The function returns only the endpoint parameters.
    """

    # Arrange
    op = IROperation(
        operation_id="dummy",
        method=HTTPMethod.GET,
        path="/dummy",
        summary=None,
        description=None,
        parameters=[
            IRParameter(name="foo", in_="query", required=True, schema=IRSchema(name=None, type="string")),
            IRParameter(name="bar", in_="query", required=False, schema=IRSchema(name=None, type="integer")),
        ],
        request_body=None,
        responses=[],
        tags=[],
    )
    model_schema = IRSchema(name=None, type="object", properties={}, required=[])
    context = RenderContext()
    # Act
    result = merge_params_with_model_fields(op, model_schema, context, schemas={})
    # Assert
    assert {p["name"] for p in result} == {"foo", "bar"}


def test_merge_params_with_model_fields__model_only__returns_model_fields() -> None:
    """
    Scenario:
        The operation has no endpoint parameters, and the model has required fields.
    Expected Outcome:
        The function returns all required model fields as parameters.
    """

    # Arrange
    op = IROperation(
        operation_id="dummy",
        method=HTTPMethod.GET,
        path="/dummy",
        summary=None,
        description=None,
        parameters=[],
        request_body=None,
        responses=[],
        tags=[],
    )
    model_schema = IRSchema(
        name=None,
        type="object",
        properties={
            "foo": IRSchema(name=None, type="string"),
            "bar": IRSchema(name=None, type="integer"),
        },
        required=["foo", "bar"],
    )
    context = RenderContext()
    # Act
    result = merge_params_with_model_fields(op, model_schema, context, schemas={})
    # Assert
    assert {p["name"] for p in result} == {"foo", "bar"}
    assert all(p["required"] for p in result)


def test_merge_params_with_model_fields__overlapping_names__endpoint_takes_precedence() -> None:
    """
    Scenario:
        The operation and model have overlapping required field names.
    Expected Outcome:
        The function includes the endpoint parameter only once, with endpoint param taking precedence.
    """

    # Arrange
    op = IROperation(
        operation_id="dummy",
        method=HTTPMethod.GET,
        path="/dummy",
        summary=None,
        description=None,
        parameters=[
            IRParameter(name="foo", in_="query", required=True, schema=IRSchema(name=None, type="string")),
        ],
        request_body=None,
        responses=[],
        tags=[],
    )
    model_schema = IRSchema(
        name=None,
        type="object",
        properties={
            "foo": IRSchema(name=None, type="string"),
            "bar": IRSchema(name=None, type="integer"),
        },
        required=["foo", "bar"],
    )
    context = RenderContext()
    # Act
    result = merge_params_with_model_fields(op, model_schema, context, schemas={})
    # Assert
    names = [p["name"] for p in result]
    assert names.count("foo") == 1
    assert set(names) == {"foo", "bar"}


def test_merge_params_with_model_fields__optional_model_fields__only_required_merged() -> None:
    """
    Scenario:
        The model has both required and optional fields.
    Expected Outcome:
        Only required model fields are merged as parameters.
    """

    # Arrange
    op = IROperation(
        operation_id="dummy",
        method=HTTPMethod.GET,
        path="/dummy",
        summary=None,
        description=None,
        parameters=[],
        request_body=None,
        responses=[],
        tags=[],
    )
    model_schema = IRSchema(
        name=None,
        type="object",
        properties={
            "foo": IRSchema(name=None, type="string"),
            "bar": IRSchema(name=None, type="integer"),
        },
        required=["foo"],
    )
    context = RenderContext()
    # Act
    result = merge_params_with_model_fields(op, model_schema, context, schemas={})
    # Assert
    names = [p["name"] for p in result]
    assert "foo" in names
    assert "bar" not in names


def test_merge_params_with_model_fields__empty_everything__returns_empty() -> None:
    """
    Scenario:
        Both the operation and model have no parameters or fields.
    Expected Outcome:
        The function returns an empty list.
    """

    # Arrange
    op = IROperation(
        operation_id="dummy",
        method=HTTPMethod.GET,
        path="/dummy",
        summary=None,
        description=None,
        parameters=[],
        request_body=None,
        responses=[],
        tags=[],
    )
    model_schema = IRSchema(name=None, type="object", properties={}, required=[])
    context = RenderContext()
    # Act
    result = merge_params_with_model_fields(op, model_schema, context, schemas={})
    # Assert
    assert result == []
