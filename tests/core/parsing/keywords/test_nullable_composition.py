"""Tests for detection and unwrapping of nullable/single-member composition wrappers.

These wrapper shapes are how OpenAPI 3.0 and 3.1 each spell "a nullable reference
to a component". Neither is a new anonymous object, so the parser must see through
them to the referenced schema.
"""

from typing import Any, Mapping

import pytest

from pyopenapi_gen.core.parsing.keywords.nullable_composition import (
    has_ref_siblings,
    is_reference_like_node,
    unwrap_nullable_composition,
)

REF: dict[str, Any] = {"$ref": "#/components/schemas/Reason"}
INLINE_OBJECT: dict[str, Any] = {"type": "object", "properties": {"id": {"type": "string"}}}
NULL_MEMBER: dict[str, Any] = {"type": "null"}


@pytest.mark.parametrize(
    "node, expected_inner, expected_nullable",
    [
        # OpenAPI 3.0: the only legal way to express a nullable $ref.
        ({"nullable": True, "allOf": [REF]}, REF, True),
        # Single-member allOf without nullable is a plain alias.
        ({"allOf": [REF]}, REF, False),
        # OpenAPI 3.1 spellings, in either member order.
        ({"anyOf": [REF, NULL_MEMBER]}, REF, True),
        ({"anyOf": [NULL_MEMBER, REF]}, REF, True),
        ({"oneOf": [REF, NULL_MEMBER]}, REF, True),
        # Single-member anyOf/oneOf is an alias too.
        ({"anyOf": [REF]}, REF, False),
        ({"oneOf": [REF]}, REF, False),
        # $ref with a sibling nullable flag (emitted by some 3.0 tooling).
        ({"$ref": REF["$ref"], "nullable": True}, REF, True),
        # Annotation-only siblings do not disqualify a wrapper.
        ({"nullable": True, "description": "d", "allOf": [REF]}, REF, True),
        ({"anyOf": [REF, NULL_MEMBER], "description": "d", "default": None}, REF, True),
        # The inner member may be inline rather than a $ref.
        ({"anyOf": [INLINE_OBJECT, NULL_MEMBER]}, INLINE_OBJECT, True),
        # A null member expressed as a single-element type list.
        ({"anyOf": [REF, {"type": ["null"]}]}, REF, True),
    ],
)
def test_unwrap_nullable_composition__wrapper_shapes__returns_inner_and_nullability(
    node: Mapping[str, Any], expected_inner: Mapping[str, Any], expected_nullable: bool
) -> None:
    # Act
    result = unwrap_nullable_composition(node)

    # Assert
    assert result is not None
    inner, is_nullable = result
    assert inner == expected_inner
    assert is_nullable is expected_nullable


@pytest.mark.parametrize(
    "node",
    [
        # Genuine unions of two real types are not nullable wrappers.
        {"anyOf": [REF, {"type": "string"}]},
        {"oneOf": [REF, INLINE_OBJECT]},
        # More than one non-null member stays a union even when null is present.
        {"anyOf": [REF, {"type": "string"}, NULL_MEMBER]},
        # Real allOf composition must keep merging.
        {"allOf": [REF, INLINE_OBJECT]},
        # A sibling structural keyword means the node adds something of its own.
        {"allOf": [REF], "properties": {"extra": {"type": "string"}}},
        {"allOf": [REF], "type": "object"},
        {"anyOf": [REF, NULL_MEMBER], "enum": ["a"]},
        {"allOf": [REF], "discriminator": {"propertyName": "kind"}},
        # Plain nodes.
        REF,
        INLINE_OBJECT,
        {"type": "string", "nullable": True},
        {},
        # Empty or null-only compositions carry no inner schema.
        {"allOf": []},
        {"anyOf": [NULL_MEMBER]},
    ],
)
def test_unwrap_nullable_composition__non_wrapper_shapes__returns_none(node: Mapping[str, Any]) -> None:
    # Act / Assert
    assert unwrap_nullable_composition(node) is None


@pytest.mark.parametrize(
    "node, expected",
    [
        (REF, True),
        ({"nullable": True, "allOf": [REF]}, True),
        ({"anyOf": [REF, NULL_MEMBER]}, True),
        # Nested wrappers still bottom out at a $ref.
        ({"allOf": [{"anyOf": [REF, NULL_MEMBER]}]}, True),
        # Inline inner schemas are not reference-like; they still need promotion.
        ({"anyOf": [INLINE_OBJECT, NULL_MEMBER]}, False),
        (INLINE_OBJECT, False),
        ({"anyOf": [REF, {"type": "string"}]}, False),
    ],
)
def test_is_reference_like_node__various__reports_whether_it_bottoms_out_at_a_ref(
    node: Mapping[str, Any], expected: bool
) -> None:
    # Act / Assert
    assert is_reference_like_node(node) is expected


def test_unwrap_nullable_composition__non_mapping__returns_none() -> None:
    # Act / Assert
    assert unwrap_nullable_composition(None) is None  # type: ignore[arg-type]
    assert unwrap_nullable_composition([REF]) is None  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "node, expected",
    [
        # OpenAPI 3.1 allows annotations beside `$ref`; they belong to this use site.
        ({"$ref": REF["$ref"], "description": "d"}, True),
        ({"$ref": REF["$ref"], "title": "T"}, True),
        ({"$ref": REF["$ref"], "default": None}, True),
        ({"$ref": REF["$ref"], "example": "x"}, True),
        ({"$ref": REF["$ref"], "examples": ["x"]}, True),
        ({"$ref": REF["$ref"], "nullable": True}, True),
        # A bare `$ref` carries nothing of its own.
        (REF, False),
        # Not a reference at all.
        (INLINE_OBJECT, False),
        ({"allOf": [REF]}, False),
        ({}, False),
        # Keys that are neither structural nor IR-representable annotations do not
        # make a use site - honouring them would change the IR while preserving
        # nothing.
        ({"$ref": REF["$ref"], "$comment": "note"}, False),
        ({"$ref": REF["$ref"], "deprecated": True}, False),
        ({"$ref": REF["$ref"], "readOnly": True}, False),
    ],
)
def test_has_ref_siblings__various__reports_whether_the_ref_carries_annotations(
    node: Mapping[str, Any], expected: bool
) -> None:
    # Act / Assert
    assert has_ref_siblings(node) is expected


def test_has_ref_siblings__non_mapping__returns_false() -> None:
    # Act / Assert
    assert has_ref_siblings(None) is False
    assert has_ref_siblings([REF]) is False
