from pathlib import Path

from pyopenapi_gen import IRRequestBody, IRResponse
from pyopenapi_gen.core.loader.loader import load_ir_from_spec

# Spec with multipart/form-data requestBody and streaming response
MULTIPART_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "TestAPI", "version": "0.1.0"},
    "paths": {
        "/upload": {
            "post": {
                "operationId": "uploadFile",
                "requestBody": {
                    "description": "Upload a file",
                    "required": True,
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "file": {"type": "string", "format": "binary"},
                                    "meta": {"type": "string"},
                                },
                                "required": ["file"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "JSON response",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    },
                    "201": {
                        "description": "Binary response",
                        "content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}},
                    },
                },
            }
        }
    },
}


def test_loader_multipart_and_stream(tmp_path: Path) -> None:
    ir = load_ir_from_spec(MULTIPART_SPEC)
    assert len(ir.operations) == 1
    op = ir.operations[0]

    # Check request_body is mapped to IRRequestBody
    assert isinstance(op.request_body, IRRequestBody)
    rb: IRRequestBody = op.request_body
    assert rb.required is True
    assert "multipart/form-data" in rb.content
    schema = rb.content["multipart/form-data"]
    # file property has binary format
    assert schema.properties["file"].format == "binary"

    # Check responses
    res_json = op.responses[0]
    assert isinstance(res_json, IRResponse)
    assert res_json.stream is False
    res_bin = op.responses[1]
    assert res_bin.stream is True
