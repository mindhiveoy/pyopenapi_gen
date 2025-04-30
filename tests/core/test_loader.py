from pyopenapi_gen import HTTPMethod
from pyopenapi_gen.core.loader import load_ir_from_spec
from pathlib import Path
import re

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
