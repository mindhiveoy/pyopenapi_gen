"""End-to-end runtime tests for the status-code -> exception pipeline.

These tests generate a real client and drive its endpoint methods against mocked
HTTP responses, asserting the correct exception (or model) results for each status
code. This exercises the *interaction* of three components that must agree:

    transport (returns every response)
        -> endpoint handler (match on response.status_code)
            -> exception aliases (NotFoundError / InternalServerError / ...)

Unit tests cover each component in isolation, but the seam between them was never
run at runtime, which is exactly how issue #344 (transport raising HTTPError before
the endpoint could raise the specific alias) slipped through. This module locks that
composed behaviour down.
"""

import asyncio
import importlib
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest
import yaml

from pyopenapi_gen.generator.client_generator import ClientGenerator

TEST_TIMEOUT_SEC = 120

# Spec declaring 200/404/500 for a single operation. 404 -> NotFoundError (ClientError),
# 500 -> InternalServerError (ServerError). No default response, so any undeclared code
# must fall through to the base HTTPError catch-all.
SPEC: dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "Error API", "version": "1.0.0"},
    "paths": {
        "/users/{id}": {
            "get": {
                "operationId": "get_user",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"id": {"type": "string"}, "name": {"type": "string"}},
                                }
                            }
                        },
                    },
                    "404": {
                        "description": "Not Found",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "properties": {"message": {"type": "string"}}}
                            }
                        },
                    },
                    "500": {
                        "description": "Server Error",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "properties": {"message": {"type": "string"}}}
                            }
                        },
                    },
                },
            }
        }
    },
}


@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_generated_client__status_codes__raise_correct_exception_per_code(tmp_path: Path) -> None:
    """
    Scenario: A generated client's endpoint is driven against mocked responses covering
        a success code, a declared client error, a declared server error, and an
        undeclared code.
    Expected Outcome:
        - 200 returns the parsed model.
        - 404 raises NotFoundError (a ClientError) carrying status_code and response.
        - 500 raises InternalServerError (a ServerError) carrying status_code.
        - An undeclared code (418) falls through to the base HTTPError catch-all.
    """
    # Arrange: generate a self-contained client from the spec
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(yaml.safe_dump(SPEC))

    pkg = "err_e2e_client"
    ClientGenerator().generate(
        spec_path=str(spec_path),
        project_root=tmp_path,
        output_package=pkg,
        force=True,
        no_postprocess=True,
    )

    sys.path.insert(0, str(tmp_path))
    try:
        # Import the generated modules at runtime
        endpoints_mod = importlib.import_module(f"{pkg}.endpoints.default")
        core_pkg = importlib.import_module(f"{pkg}.core")
        core_exc = importlib.import_module(f"{pkg}.core.exceptions")
        transport_mod = importlib.import_module(f"{pkg}.core.http_transport")

        DefaultClient = endpoints_mod.DefaultClient
        HttpxTransport = transport_mod.HttpxTransport
        HTTPError = core_exc.HTTPError
        ClientError = core_exc.ClientError
        ServerError = core_exc.ServerError
        NotFoundError = core_pkg.NotFoundError
        InternalServerError = core_pkg.InternalServerError

        def make_client(status_code: int, body: dict[str, Any]) -> tuple[Any, Any]:
            def handler(request: httpx.Request) -> httpx.Response:
                return httpx.Response(status_code, json=body)

            transport = HttpxTransport(base_url="https://api.example.com")
            transport._client._transport = httpx.MockTransport(handler)
            return DefaultClient(transport, base_url="https://api.example.com"), transport

        # Act & Assert: 200 -> parsed model
        client, transport = make_client(200, {"id": "1", "name": "Ada"})
        result = asyncio.run(client.get_user(id_="1"))
        # The 'id' field is generated as 'id_' to avoid shadowing the builtin (cattrs maps from 'id')
        assert result.id_ == "1"
        assert result.name == "Ada"
        asyncio.run(transport.close())

        # Act & Assert: 404 -> NotFoundError (subclass of ClientError) with metadata
        client, transport = make_client(404, {"message": "nope"})
        with pytest.raises(NotFoundError) as exc_info:
            asyncio.run(client.get_user(id_="1"))
        assert isinstance(exc_info.value, ClientError)
        assert exc_info.value.status_code == 404
        assert exc_info.value.response is not None
        asyncio.run(transport.close())

        # Act & Assert: 500 -> InternalServerError (subclass of ServerError)
        client, transport = make_client(500, {"message": "boom"})
        with pytest.raises(InternalServerError) as exc_info:
            asyncio.run(client.get_user(id_="1"))
        assert isinstance(exc_info.value, ServerError)
        assert exc_info.value.status_code == 500
        asyncio.run(transport.close())

        # Act & Assert: undeclared 418 -> base HTTPError catch-all (not a specific alias)
        client, transport = make_client(418, {"message": "teapot"})
        with pytest.raises(HTTPError) as exc_info:
            asyncio.run(client.get_user(id_="1"))
        assert type(exc_info.value) is HTTPError
        assert exc_info.value.status_code == 418
        asyncio.run(transport.close())
    finally:
        sys.path.remove(str(tmp_path))
        for name in list(sys.modules):
            if name == pkg or name.startswith(pkg + "."):
                del sys.modules[name]


# Spec with an explicit 200 success AND a 'default' response carrying an error body. The endpoint's
# return type is the success type, so an unhandled error code must raise rather than return the error
# body as a (mistyped) success object.
SPEC_WITH_DEFAULT: dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "Default API", "version": "1.0.0"},
    "paths": {
        "/things": {
            "get": {
                "operationId": "list_things",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {"schema": {"type": "object", "properties": {"id": {"type": "string"}}}}
                        },
                    },
                    "default": {
                        "description": "Error",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "properties": {"message": {"type": "string"}}}
                            }
                        },
                    },
                },
            }
        }
    },
}


@pytest.mark.timeout(TEST_TIMEOUT_SEC)
def test_generated_client__default_response_with_content__error_code_raises_not_returns(tmp_path: Path) -> None:
    """
    Scenario: A spec declares an explicit 200 plus a 'default' response with an error body. An
        unhandled error code (500) is returned by the server.
    Expected Outcome: The endpoint raises HTTPError carrying the real status code, rather than
        returning the error body as a mistyped success object. A 200 still returns the parsed model.
    """
    # Arrange
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(yaml.safe_dump(SPEC_WITH_DEFAULT))

    pkg = "default_e2e_client"
    ClientGenerator().generate(
        spec_path=str(spec_path),
        project_root=tmp_path,
        output_package=pkg,
        force=True,
        no_postprocess=True,
    )

    sys.path.insert(0, str(tmp_path))
    try:
        endpoints_mod = importlib.import_module(f"{pkg}.endpoints.default")
        core_exc = importlib.import_module(f"{pkg}.core.exceptions")
        transport_mod = importlib.import_module(f"{pkg}.core.http_transport")

        DefaultClient = endpoints_mod.DefaultClient
        HttpxTransport = transport_mod.HttpxTransport
        HTTPError = core_exc.HTTPError

        def make_client(status_code: int, body: dict[str, Any]) -> tuple[Any, Any]:
            def handler(request: httpx.Request) -> httpx.Response:
                return httpx.Response(status_code, json=body)

            transport = HttpxTransport(base_url="https://api.example.com")
            transport._client._transport = httpx.MockTransport(handler)
            return DefaultClient(transport, base_url="https://api.example.com"), transport

        # Act & Assert: unhandled 500 -> raises HTTPError (does NOT return a mistyped success object)
        client, transport = make_client(500, {"message": "internal boom"})
        with pytest.raises(HTTPError) as exc_info:
            asyncio.run(client.list_things())
        assert exc_info.value.status_code == 500
        asyncio.run(transport.close())

        # Act & Assert: 200 still returns the parsed success model
        client, transport = make_client(200, {"id": "abc"})
        result = asyncio.run(client.list_things())
        assert result.id_ == "abc"
        asyncio.run(transport.close())
    finally:
        sys.path.remove(str(tmp_path))
        for name in list(sys.modules):
            if name == pkg or name.startswith(pkg + "."):
                del sys.modules[name]
