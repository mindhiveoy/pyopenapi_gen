import re
from pathlib import Path

from pyopenapi_gen import HTTPMethod
from pyopenapi_gen.core.loader import load_ir_from_spec

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


def test_load_ir_min_spec() -> None:
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


def test_load_ir_query_params() -> None:
    """
    Scenario:
        The OpenAPI spec defines a GET endpoint with two query parameters (start_date, end_date).
    Expected Outcome:
        The resulting IROperation contains both parameters with in_ == 'query', correct names, and required flags.
    """
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "Analytics", "version": "1.0.0"},
        "paths": {
            "/tenants/{tenant_id}/analytics/chat-stats": {
                "get": {
                    "operationId": "getTenantChatStats",
                    "summary": "Get chat statistics for a tenant",
                    "parameters": [
                        {
                            "name": "tenant_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "start_date",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "end_date",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }
    ir = load_ir_from_spec(spec)
    op = ir.operations[0]
    query_params = [p for p in op.parameters if p.in_ == "query"]
    assert len(query_params) == 2
    names = {p.name for p in query_params}
    assert names == {"start_date", "end_date"}
    for p in query_params:
        assert p.required is False
        assert p.schema.type == "string"


def test_codegen_analytics_query_params(tmp_path: Path) -> None:
    """
    Scenario:
        The OpenAPI spec defines a GET endpoint with a path param and two query params (start_date, end_date).
    Expected Outcome:
        The generated endpoint code includes both query params in the params dict, and not the path param.
    """
    from pyopenapi_gen.core.loader import load_ir_from_spec
    from pyopenapi_gen.emitters.endpoints_emitter import EndpointsEmitter

    spec = {
        "openapi": "3.1.0",
        "info": {"title": "Analytics", "version": "1.0.0"},
        "paths": {
            "/tenants/{tenant_id}/analytics/chat-stats": {
                "get": {
                    "operationId": "getTenantChatStats",
                    "summary": "Get chat statistics for a tenant",
                    "parameters": [
                        {
                            "name": "tenant_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "start_date",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "end_date",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {"200": {"description": "OK"}},
                    "tags": ["analytics"],
                }
            }
        },
    }
    ir = load_ir_from_spec(spec)
    out_dir = tmp_path / "out"
    emitter = EndpointsEmitter()
    emitter.emit(ir, str(out_dir))
    analytics_file = out_dir / "endpoints" / "analytics.py"
    assert analytics_file.exists(), "analytics.py not generated"
    content = analytics_file.read_text()
    # Extract the params dict assignment block (multi-line)
    match = re.search(r"params: dict\[str, Any\] = \{([\s\S]*?)\}\n", content, re.MULTILINE)
    assert match, "params dict assignment not found in generated code"
    params_block = match.group(1)
    # Assert that all query params are included in the params dict
    assert "start_date" in params_block, f"start_date not in params dict: {params_block}"
    assert "end_date" in params_block, f"end_date not in params dict: {params_block}"
    assert "tenant_id" not in params_block, f"tenant_id should not be in params dict: {params_block}"
    # Ensure params dict is not empty
    assert params_block.strip(), "params dict is empty, should include query params"


def test_parse_schema_nullable_type_array() -> None:
    """
    Scenario:
        - A schema property uses `type: ["string", "null"]`.
    Expected Outcome:
        - The corresponding IRSchema in `properties` should have `type="string"` and `is_nullable=True`.
    """
    # Arrange
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "Nullable Test", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "TestSchema": {
                    "type": "object",
                    "properties": {
                        "nullable_prop": {"type": ["string", "null"], "description": "Can be string or null"}
                    },
                }
            }
        },
    }

    # Act
    ir = load_ir_from_spec(spec)

    # Assert
    assert "TestSchema" in ir.schemas
    test_schema = ir.schemas["TestSchema"]
    assert "nullable_prop" in test_schema.properties
    prop_schema = test_schema.properties["nullable_prop"]

    assert prop_schema.type == "string"
    assert prop_schema.is_nullable is True
    assert prop_schema.any_of is None  # Ensure composition fields are not set


def test_parse_schema_nullable_anyof() -> None:
    """
    Scenario:
        - A schema uses `anyOf` containing a reference and `{type: "null"}`.
    Expected Outcome:
        - The resulting IRSchema should have `is_nullable=True`.
        - Its `any_of` list should contain only the IRSchema for the referenced type.
    """
    # Arrange
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "Nullable anyOf Test", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "TypeA": {"type": "string"},
                "TestSchema": {
                    "anyOf": [{"$ref": "#/components/schemas/TypeA"}, {"type": "null"}],
                    "description": "Can be TypeA or null",
                },
            }
        },
    }

    # Act
    ir = load_ir_from_spec(spec)

    # Assert
    assert "TestSchema" in ir.schemas
    test_schema = ir.schemas["TestSchema"]

    assert test_schema.is_nullable is True
    assert test_schema.any_of is not None
    assert len(test_schema.any_of) == 1
    assert test_schema.any_of[0].name == "TypeA"
    assert test_schema.type is None  # Primary type shouldn't be set directly


def test_parse_schema_anyof_union() -> None:
    """
    Scenario:
        - A schema uses `anyOf` with two different references.
    Expected Outcome:
        - The resulting IRSchema should have `any_of` populated with IRSchemas for both types.
        - `is_nullable` should be False.
    """
    # Arrange
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "anyOf Union Test", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "TypeA": {"type": "string"},
                "TypeB": {"type": "integer"},
                "TestSchema": {
                    "anyOf": [{"$ref": "#/components/schemas/TypeA"}, {"$ref": "#/components/schemas/TypeB"}],
                    "description": "Can be TypeA or TypeB",
                },
            }
        },
    }

    # Act
    ir = load_ir_from_spec(spec)

    # Assert
    assert "TestSchema" in ir.schemas
    test_schema = ir.schemas["TestSchema"]

    assert test_schema.is_nullable is False
    assert test_schema.any_of is not None
    assert len(test_schema.any_of) == 2
    assert {s.name for s in test_schema.any_of} == {"TypeA", "TypeB"}
    assert test_schema.type is None


def test_parse_schema_allof_storage() -> None:
    """
    Scenario:
        - A schema uses `allOf` with two different references.
    Expected Outcome:
        - The resulting IRSchema should have `all_of` populated with IRSchemas for both types.
        - Other fields like `properties` should not be merged from the components.
    """
    # Arrange
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "allOf Storage Test", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Base": {"type": "object", "properties": {"base_prop": {"type": "string"}}},
                "Mixin": {"type": "object", "properties": {"mixin_prop": {"type": "integer"}}},
                "TestSchema": {
                    "allOf": [{"$ref": "#/components/schemas/Base"}, {"$ref": "#/components/schemas/Mixin"}],
                    "description": "Combines Base and Mixin",
                },
            }
        },
    }

    # Act
    ir = load_ir_from_spec(spec)

    # Assert
    assert "TestSchema" in ir.schemas
    test_schema = ir.schemas["TestSchema"]

    assert test_schema.is_nullable is False
    assert test_schema.all_of is not None
    assert len(test_schema.all_of) == 2
    assert {s.name for s in test_schema.all_of} == {"Base", "Mixin"}
    assert test_schema.type is None  # Type is not directly set for allOf wrapper
    assert not test_schema.properties  # Properties are not merged in the loader anymore
