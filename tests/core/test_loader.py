from pyopenapi_gen.core.loader import load_ir_from_spec
from pyopenapi_gen import HTTPMethod


MIN_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Petstore", "version": "1.0.0"},
    "paths": {
        "/pets": {
            "get": {
                "operationId": "listPets",
                "summary": "List all pets",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Pet"},
                                }
                            }
                        },
                    }
                },
            }
        }
    },
    "components": {
        "schemas": {
            "Pet": {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "integer", "format": "int64"},
                    "name": {"type": "string"},
                },
            }
        }
    },
}


def test_load_ir_min_spec():
    ir = load_ir_from_spec(MIN_SPEC)

    assert ir.title == "Petstore"
    assert ir.version == "1.0.0"

    # Schemas
    assert "Pet" in ir.schemas
    pet_schema = ir.schemas["Pet"]
    assert pet_schema.type == "object"
    assert "name" in pet_schema.properties

    # Operations
    assert len(ir.operations) == 1
    op = ir.operations[0]
    assert op.operation_id == "listPets"
    assert op.method == HTTPMethod.GET
    assert op.path == "/pets"
    assert op.responses[0].status_code == "200"
