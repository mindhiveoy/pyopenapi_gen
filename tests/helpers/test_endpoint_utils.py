from typing import Any
from unittest.mock import Mock, patch

from pyopenapi_gen import HTTPMethod, IROperation, IRParameter, IRRequestBody, IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.helpers.endpoint_utils import (
    format_method_args,
    get_model_stub_args,
    get_param_type,
    get_params,
    get_request_body_type,
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
            IRParameter(name="foo", param_in="query", required=True, schema=IRSchema(name=None, type="string")),
            IRParameter(name="bar", param_in="query", required=False, schema=IRSchema(name=None, type="integer")),
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
            IRParameter(name="foo", param_in="query", required=True, schema=IRSchema(name=None, type="string")),
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


# ===== Tests for get_params =====


class TestGetParams:
    def test_get_params__operation_with_required_parameters__returns_param_dicts(self) -> None:
        """
        Scenario:
            An operation has required parameters that need to be converted to parameter dicts.

        Expected Outcome:
            The function returns a list of parameter dicts with correct properties.
        """
        # Arrange
        param1 = IRParameter(name="user_id", param_in="path", required=True, schema=IRSchema(name=None, type="string"))
        param2 = IRParameter(name="limit", param_in="query", required=True, schema=IRSchema(name=None, type="integer"))
        op = IROperation(
            operation_id="get_user",
            method=HTTPMethod.GET,
            path="/users/{user_id}",
            summary=None,
            description=None,
            parameters=[param1, param2],
            request_body=None,
            responses=[],
            tags=[],
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.get_param_type") as mock_get_param_type:
            mock_get_param_type.side_effect = ["str", "int"]

            # Act
            result = get_params(op, context, schemas)

            # Assert
            assert len(result) == 2
            assert result[0]["name"] == "user_id"
            assert result[0]["type"] == "str"
            assert result[0]["default"] is None
            assert result[0]["required"] is True
            assert result[1]["name"] == "limit"
            assert result[1]["type"] == "int"
            assert result[1]["default"] is None
            assert result[1]["required"] is True

    def test_get_params__operation_with_optional_parameters__returns_param_dicts_with_none_defaults(self) -> None:
        """
        Scenario:
            An operation has optional parameters.

        Expected Outcome:
            Optional parameters should have "None" as default value.
        """
        # Arrange
        param = IRParameter(name="filter", param_in="query", required=False, schema=IRSchema(name=None, type="string"))
        op = IROperation(
            operation_id="list_users",
            method=HTTPMethod.GET,
            path="/users",
            summary=None,
            description=None,
            parameters=[param],
            request_body=None,
            responses=[],
            tags=[],
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.get_param_type") as mock_get_param_type:
            mock_get_param_type.return_value = "str"

            # Act
            result = get_params(op, context, schemas)

            # Assert
            assert len(result) == 1
            assert result[0]["name"] == "filter_"  # NameSanitizer adds underscore to reserved keywords
            assert result[0]["default"] == "None"
            assert result[0]["required"] is False

    def test_get_params__operation_with_no_parameters__returns_empty_list(self) -> None:
        """
        Scenario:
            An operation has no parameters.

        Expected Outcome:
            An empty list should be returned.
        """
        # Arrange
        op = IROperation(
            operation_id="health_check",
            method=HTTPMethod.GET,
            path="/health",
            summary=None,
            description=None,
            parameters=[],
            request_body=None,
            responses=[],
            tags=[],
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        # Act
        result = get_params(op, context, schemas)

        # Assert
        assert result == []


# ===== Tests for get_param_type =====


class TestGetParamType:
    def test_get_param_type__simple_string_parameter__returns_string_type(self) -> None:
        """
        Scenario:
            A parameter with a simple string schema.

        Expected Outcome:
            The function returns the resolved type from UnifiedTypeService.
        """
        # Arrange
        param = IRParameter(name="name", param_in="query", required=True, schema=IRSchema(name=None, type="string"))
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = "str"
            MockTypeService.return_value = mock_service

            # Act
            result = get_param_type(param, context, schemas)

            # Assert
            assert result == "str"
            mock_service.resolve_schema_type.assert_called_once_with(param.schema, context, required=param.required)

    def test_get_param_type__relative_import_type__adds_models_prefix(self) -> None:
        """
        Scenario:
            UnifiedTypeService returns a relative import starting with ".".

        Expected Outcome:
            The type should be prefixed with "models" for endpoint imports.
        """
        # Arrange
        param = IRParameter(name="user", param_in="body", required=True, schema=IRSchema(name=None, type="object"))
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = ".user.User"
            MockTypeService.return_value = mock_service

            # Act
            result = get_param_type(param, context, schemas)

            # Assert
            assert result == "models.user.User"

    def test_get_param_type__file_upload_parameter__returns_io_any(self) -> None:
        """
        Scenario:
            A parameter represents a file upload (formData with binary format).

        Expected Outcome:
            The function returns "IO[Any]" and adds appropriate imports.
        """
        # Arrange
        param = IRParameter(
            name="file",
            param_in="formData",
            required=True,
            schema=IRSchema(name=None, type="string", format="binary"),
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = "str"
            MockTypeService.return_value = mock_service

            # Patch the specific getattr calls in the function to simulate the missing in_ attribute
            with patch("pyopenapi_gen.helpers.endpoint_utils.getattr") as mock_getattr:
                # Set up the mock to return appropriate values for the file upload detection
                def getattr_side_effect(obj: Any, attr: str, default: Any = None) -> Any:
                    if obj is param and attr == "in_":
                        return "formData"
                    elif obj is param.schema and attr == "type":
                        return "string"
                    elif obj is param.schema and attr == "format":
                        return "binary"
                    # For all other getattr calls, use the real getattr to avoid recursion
                    import builtins

                    return builtins.getattr(obj, attr, default)

                mock_getattr.side_effect = getattr_side_effect

                # Act
                result = get_param_type(param, context, schemas)

                # Assert
                assert result == "IO[Any]"


# ===== Tests for get_request_body_type =====


class TestGetRequestBodyType:
    def test_get_request_body_type__json_content__returns_resolved_type(self) -> None:
        """
        Scenario:
            Request body has application/json content.

        Expected Outcome:
            The function resolves and returns the JSON schema type.
        """
        # Arrange
        json_schema = IRSchema(name="User", type="object")
        body = IRRequestBody(
            required=True,
            content={"application/json": json_schema},
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = "User"
            MockTypeService.return_value = mock_service

            # Act
            result = get_request_body_type(body, context, schemas)

            # Assert
            assert result == "User"
            mock_service.resolve_schema_type.assert_called_once_with(json_schema, context, required=body.required)

    def test_get_request_body_type__json_content_relative_import__adds_models_prefix(self) -> None:
        """
        Scenario:
            JSON content resolves to a relative import.

        Expected Outcome:
            The type should be prefixed with "models".
        """
        # Arrange
        json_schema = IRSchema(name="User", type="object")
        body = IRRequestBody(required=True, content={"application/json": json_schema})
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = ".user.User"
            MockTypeService.return_value = mock_service

            # Act
            result = get_request_body_type(body, context, schemas)

            # Assert
            assert result == "models.user.User"

    def test_get_request_body_type__json_content_any_type__returns_dict_str_any(self) -> None:
        """
        Scenario:
            JSON content resolves to "Any" type.

        Expected Outcome:
            The function returns "Dict[str, Any]" for better type hints.
        """
        # Arrange
        json_schema = IRSchema(name=None, type="object")
        body = IRRequestBody(required=True, content={"application/json": json_schema})
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = "Any"
            MockTypeService.return_value = mock_service

            # Act
            result = get_request_body_type(body, context, schemas)

            # Assert
            assert result == "Dict[str, Any]"

    def test_get_request_body_type__non_json_content__returns_any(self) -> None:
        """
        Scenario:
            Request body has no JSON content (e.g., octet-stream).

        Expected Outcome:
            The function returns "Any" as fallback.
        """
        # Arrange
        body = IRRequestBody(
            required=True,
            content={"application/octet-stream": IRSchema(name=None, type="string", format="binary")},
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        # Act
        result = get_request_body_type(body, context, schemas)

        # Assert
        assert result == "Any"

    def test_get_request_body_type__empty_content__returns_any(self) -> None:
        """
        Scenario:
            Request body has no content defined.

        Expected Outcome:
            The function returns "Any" as fallback.
        """
        # Arrange
        body = IRRequestBody(required=True, content={})
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        # Act
        result = get_request_body_type(body, context, schemas)

        # Assert
        assert result == "Any"
