from pyopenapi_gen import (
    HTTPMethod,
    IROperation,
    IRParameter,
    IRResponse,
    IRSchema,
    IRSpec,
    load_ir_from_spec,
)


def test_ir_smoke() -> None:
    """Ensure that core IR dataclasses can be instantiated and linked."""

    pet_schema = IRSchema(
        name="Pet",
        type="object",
        properties={
            "id": IRSchema(name=None, type="integer", format="int64"),
            "name": IRSchema(name=None, type="string"),
        },
        required=["id", "name"],
    )

    list_pets_op = IROperation(
        operation_id="listPets",
        method=HTTPMethod.GET,
        path="/pets",
        summary="List pets",
        description=None,
        parameters=[
            IRParameter(
                name="limit",
                in_="query",
                required=False,
                schema=IRSchema(name=None, type="integer", format="int32"),
                description="How many pets to return",
            )
        ],
        request_body=None,
        responses=[
            IRResponse(
                status_code="200",
                description="A paged array of pets",
                content={"application/json": IRSchema(name=None, type="array", items=pet_schema)},
            )
        ],
        tags=["pets"],
    )

    spec = IRSpec(
        title="Petstore",
        version="1.0.0",
        schemas={"Pet": pet_schema},
        operations=[list_pets_op],
        servers=["https://example.com"],
    )

    assert spec.title == "Petstore"
    assert spec.operations[0].method == HTTPMethod.GET
    assert spec.schemas["Pet"].properties["name"].type == "string"


def test_ir_query_param_from_spec() -> None:
    """Test that load_ir_from_spec correctly parses query parameters into IR."""
    # Minimal OpenAPI spec with a query parameter
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/items": {
                "get": {
                    "operationId": "listItems",
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                            "description": "Query string",
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {"schema": {"type": "array", "items": {"type": "string"}}}},
                        }
                    },
                }
            }
        },
    }
    ir = load_ir_from_spec(spec)
    op = ir.operations[0]
    assert op.operation_id == "listItems"
    assert op.parameters
    param = op.parameters[0]
    assert param.name == "q"
    assert param.in_ == "query"
    assert param.schema.type == "string"


def test_ir_path_param_from_spec__single_path_param__correct_irparameter() -> None:
    """
    Scenario:
        - The OpenAPI spec defines a GET /items/{item_id} endpoint with a required path parameter 'item_id'.
        - We want to verify that load_ir_from_spec parses this into an IROperation with an IRParameter where in_
          == 'path', name == 'item_id', and required is True.

    Expected Outcome:
        - The resulting IRSpec contains an IROperation for /items/{item_id} with a path parameter IRParameter
          named 'item_id', in_ == 'path', required == True, and correct type.
    """
    # Arrange
    from pyopenapi_gen import load_ir_from_spec

    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/items/{item_id}": {
                "get": {
                    "operationId": "getItem",
                    "parameters": [
                        {
                            "name": "item_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "ID of the item",
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        }
                    },
                }
            }
        },
    }
    # Act
    ir = load_ir_from_spec(spec)
    op = ir.operations[0]
    # Assert
    assert op.operation_id == "getItem"
    assert op.parameters
    param = op.parameters[0]
    assert param.name == "item_id"
    assert param.in_ == "path"
    assert param.required is True
    assert param.schema.type == "string"
