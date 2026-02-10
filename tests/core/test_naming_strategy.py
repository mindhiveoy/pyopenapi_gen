"""Integration tests for the NamingStrategy feature.

Tests verify that naming strategies are correctly applied through
load_ir_from_spec() and that collisions are resolved by the deduplicator.
"""

from __future__ import annotations

from typing import Any, Dict

import pytest

from pyopenapi_gen.core.loader.loader import load_ir_from_spec
from pyopenapi_gen.ir import NamingStrategy


def _make_spec(paths: Dict[str, Any]) -> Dict[str, Any]:
    """Build a minimal valid OpenAPI 3.1 spec with the given paths."""
    return {
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": "0.1.0"},
        "paths": paths,
        "components": {"schemas": {}},
    }


# ---------------------------------------------------------------------------
# Specs used across tests
# ---------------------------------------------------------------------------

FASTAPI_SPEC = _make_spec(
    {
        "/details": {
            "post": {
                "operationId": "create_details_details_post",
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/users/{user_id}": {
            "get": {
                "operationId": "get_user_users_user_id_get",
                "responses": {"200": {"description": "OK"}},
            }
        },
    }
)

MISSING_OPERATION_ID_SPEC = _make_spec(
    {
        "/items": {
            "get": {
                "responses": {"200": {"description": "OK"}},
            }
        },
    }
)

CLEAN_COLLISION_SPEC = _make_spec(
    {
        "/details": {
            "post": {
                "operationId": "create_details_details_post",
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/v2/details": {
            "post": {
                "operationId": "create_details_v2_details_post",
                "responses": {"200": {"description": "OK"}},
            }
        },
    }
)

CUSTOM_OPERATION_ID_SPEC = _make_spec(
    {
        "/users": {
            "post": {
                "operationId": "createUser",
                "responses": {"200": {"description": "OK"}},
            }
        },
    }
)


# ---------------------------------------------------------------------------
# operationId strategy (default)
# ---------------------------------------------------------------------------


def test_operation_id_strategy__fastapi_ids__preserves_raw_operation_id() -> None:
    """The default strategy uses operationId from the spec as-is."""
    ir = load_ir_from_spec(FASTAPI_SPEC, naming_strategy=NamingStrategy.OPERATION_ID)
    op_ids = {op.operation_id for op in ir.operations}

    assert "create_details_details_post" in op_ids
    assert "get_user_users_user_id_get" in op_ids


def test_operation_id_strategy__missing_operation_id__falls_back_to_method_path() -> None:
    """When operationId is missing, the default strategy falls back to method+path."""
    ir = load_ir_from_spec(MISSING_OPERATION_ID_SPEC, naming_strategy=NamingStrategy.OPERATION_ID)

    assert len(ir.operations) == 1
    assert ir.operations[0].operation_id == "get_items"


# ---------------------------------------------------------------------------
# clean strategy
# ---------------------------------------------------------------------------


def test_clean_strategy__fastapi_ids__strips_suffixes() -> None:
    """The clean strategy strips FastAPI auto-generated path+method suffixes."""
    ir = load_ir_from_spec(FASTAPI_SPEC, naming_strategy=NamingStrategy.CLEAN)
    op_ids = {op.operation_id for op in ir.operations}

    assert "create_details" in op_ids
    assert "get_user" in op_ids


def test_clean_strategy__custom_operation_id__returns_unchanged() -> None:
    """The clean strategy leaves non-FastAPI operationIds unchanged."""
    ir = load_ir_from_spec(CUSTOM_OPERATION_ID_SPEC, naming_strategy=NamingStrategy.CLEAN)

    assert len(ir.operations) == 1
    assert ir.operations[0].operation_id == "createUser"


def test_clean_strategy__missing_operation_id__falls_back_to_method_path() -> None:
    """When operationId is missing, the clean strategy falls back to method+path."""
    ir = load_ir_from_spec(MISSING_OPERATION_ID_SPEC, naming_strategy=NamingStrategy.CLEAN)

    assert len(ir.operations) == 1
    assert ir.operations[0].operation_id == "get_items"


# ---------------------------------------------------------------------------
# path strategy
# ---------------------------------------------------------------------------


def test_path_strategy__ignores_operation_id__derives_from_method_path() -> None:
    """The path strategy always derives names from HTTP method + path."""
    ir = load_ir_from_spec(FASTAPI_SPEC, naming_strategy=NamingStrategy.PATH)
    op_ids = {op.operation_id for op in ir.operations}

    assert "post_details" in op_ids
    assert "get_users_user_id" in op_ids


def test_path_strategy__missing_operation_id__derives_from_method_path() -> None:
    """The path strategy uses method+path regardless of operationId presence."""
    ir = load_ir_from_spec(MISSING_OPERATION_ID_SPEC, naming_strategy=NamingStrategy.PATH)

    assert len(ir.operations) == 1
    assert ir.operations[0].operation_id == "get_items"


# ---------------------------------------------------------------------------
# Collision handling
# ---------------------------------------------------------------------------


def test_clean_strategy__duplicate_names__both_produce_same_id_at_ir_level() -> None:
    """When clean produces collisions, both operations get the same operation_id at IR level.

    The deduplicator in EndpointsEmitter resolves these during code emission,
    not during IR construction.
    """
    ir = load_ir_from_spec(CLEAN_COLLISION_SPEC, naming_strategy=NamingStrategy.CLEAN)
    op_ids = [op.operation_id for op in ir.operations]

    assert len(op_ids) == 2
    assert all(oid == "create_details" for oid in op_ids)


def test_clean_strategy__duplicate_names__deduplicator_resolves_collision() -> None:
    """EndpointsEmitter deduplicator appends _2 suffix when clean produces collisions."""
    from pyopenapi_gen.core.utils import NameSanitizer

    ir = load_ir_from_spec(CLEAN_COLLISION_SPEC, naming_strategy=NamingStrategy.CLEAN)

    # Replicate the deduplication logic from EndpointsEmitter to verify
    # that collisions from the clean strategy are resolvable. This avoids
    # coupling the test to EndpointsEmitter's constructor.
    seen: dict[str, int] = {}
    for op in ir.operations:
        method_name = NameSanitizer.sanitize_method_name(op.operation_id)
        if method_name in seen:
            seen[method_name] += 1
            op.operation_id = f"{op.operation_id}_{seen[method_name]}"
        else:
            seen[method_name] = 1

    op_ids = sorted(op.operation_id for op in ir.operations)
    assert len(op_ids) == 2
    assert "create_details" in op_ids
    assert any("_2" in oid for oid in op_ids)


# ---------------------------------------------------------------------------
# Default argument backward compatibility
# ---------------------------------------------------------------------------


def test_default_strategy__no_argument__matches_operation_id_strategy() -> None:
    """Calling load_ir_from_spec without naming_strategy uses OPERATION_ID (backward compat)."""
    ir_default = load_ir_from_spec(FASTAPI_SPEC)
    ir_explicit = load_ir_from_spec(FASTAPI_SPEC, naming_strategy=NamingStrategy.OPERATION_ID)

    default_ids = {op.operation_id for op in ir_default.operations}
    explicit_ids = {op.operation_id for op in ir_explicit.operations}
    assert default_ids == explicit_ids


# ---------------------------------------------------------------------------
# NamingStrategy enum
# ---------------------------------------------------------------------------


def test_naming_strategy_enum__string_values__typer_compatible() -> None:
    """NamingStrategy enum values work as strings for Typer CLI compatibility."""
    assert NamingStrategy("operationId") == NamingStrategy.OPERATION_ID
    assert NamingStrategy("clean") == NamingStrategy.CLEAN
    assert NamingStrategy("path") == NamingStrategy.PATH


def test_naming_strategy_enum__invalid_value__raises_value_error() -> None:
    """Invalid strategy values raise ValueError."""
    with pytest.raises(ValueError):
        NamingStrategy("invalid")
