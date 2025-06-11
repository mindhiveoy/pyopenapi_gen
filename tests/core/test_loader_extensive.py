import pytest
from pyopenapi_gen.core.loader.loader import load_ir_from_spec


def test_load_ir_from_spec_missing_openapi() -> None:
    with pytest.raises(ValueError) as excinfo:
        load_ir_from_spec({})
    assert "Missing 'openapi' field" in str(excinfo.value)


def test_load_ir_from_spec_missing_paths() -> None:
    with pytest.raises(ValueError) as excinfo:
        load_ir_from_spec({"openapi": "3.1.0"})
    assert "Missing 'paths' section" in str(excinfo.value)


def test_simple_operation_and_response_and_servers() -> None:
    """A minimal spec with one operation, JSON response, and server URL."""
    spec_dict = {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "0.1.0"},
        "servers": [{"url": "https://api.example"}],
        "paths": {
            "/items": {
                "get": {
                    "operationId": "get_items",
                    "summary": "Get items",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }
    spec = load_ir_from_spec(spec_dict)
    # Title, version, servers
    assert spec.title == "Test API"
    assert spec.version == "0.1.0"
    assert spec.servers == ["https://api.example"]
    # One operation
    assert len(spec.operations) == 1
    op = spec.operations[0]
    assert op.operation_id == "get_items"
    assert op.method.name == "GET"
    assert op.path == "/items"
    assert op.summary == "Get items"
    # No parameters or request body
    assert op.parameters == []
    assert op.request_body is None
    # Response content and non-streaming
    assert len(op.responses) == 1
    resp = op.responses[0]
    assert resp.status_code == "200"
    assert "application/json" in resp.content
    assert not resp.stream


def test_parse_parameters_and_request_body_and_streaming_response() -> None:
    """Spec with path and query parameters, JSON requestBody, and binary response stream."""
    spec_dict = {
        "openapi": "3.1.0",
        "info": {"title": "Full API", "version": "2.0.0"},
        "paths": {
            "/download/{fileId}": {
                "parameters": [
                    {
                        "name": "fileId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "post": {
                    "operationId": "download_file",
                    "requestBody": {
                        "required": False,
                        "description": "Optional options",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"verbose": {"type": "boolean"}},
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Binary data",
                            "content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}},
                        }
                    },
                },
            }
        },
    }
    spec = load_ir_from_spec(spec_dict)
    assert len(spec.operations) == 1
    op = spec.operations[0]
    # Parameter parsing
    assert len(op.parameters) == 1
    param = op.parameters[0]
    assert param.name == "fileId"
    assert param.param_in == "path"
    assert param.required is True
    assert param.schema.type == "string"
    # Request body parsing
    rb = op.request_body
    assert rb is not None
    assert rb.required is False
    assert rb.description == "Optional options"
    assert "application/json" in rb.content
    # Streaming response detection
    resp = op.responses[0]
    assert resp.status_code == "200"
    assert resp.stream


def test_response_ref_and_parameter_ref_and_request_body_ref_and_component_refs() -> None:
    """Spec using component references for responses, parameters, and requestBodies."""
    spec_dict = {
        "openapi": "3.1.0",
        "info": {"title": "Ref API", "version": "3.0.0"},
        "components": {
            "parameters": {
                "pageParam": {
                    "name": "page",
                    "in": "query",
                    "schema": {"type": "integer"},
                }
            },
            "responses": {"NotFound": {"description": "Not Found"}},
            "requestBodies": {
                "MyBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"type": "object"}}},
                }
            },
        },
        "paths": {
            "/ref": {
                "parameters": [{"$ref": "#/components/parameters/pageParam"}],
                "put": {
                    "operationId": "put_ref",
                    "requestBody": {"$ref": "#/components/requestBodies/MyBody"},
                    "responses": {"404": {"$ref": "#/components/responses/NotFound"}},
                },
            }
        },
    }
    spec = load_ir_from_spec(spec_dict)
    op = spec.operations[0]
    # Parameter ref resolved
    assert len(op.parameters) == 1
    assert op.parameters[0].name == "page"
    # RequestBody ref resolved
    rb = op.request_body
    assert rb is not None and rb.required is True
    # Response ref resolved
    resp = op.responses[0]
    assert resp.status_code == "404"
    assert resp.description == "Not Found"
