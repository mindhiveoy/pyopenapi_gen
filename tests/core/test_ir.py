from pyopenapi_gen import (
    HTTPMethod,
    IROperation,
    IRParameter,
    IRResponse,
    IRSchema,
    IRSpec,
)


def test_ir_smoke():
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
