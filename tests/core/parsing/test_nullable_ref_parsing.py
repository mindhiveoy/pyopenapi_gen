"""IR-level tests for nullable `$ref` properties in OpenAPI 3.0 and 3.1 specs.

A nullable reference must resolve to the referenced component with nullability
applied, and must not mint a per-field schema.
"""

from typing import Any

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_parser import _parse_schema

REASON: dict[str, Any] = {"type": "string", "enum": ["unpricedSpend", "missingRate"]}
THING: dict[str, Any] = {"type": "object", "properties": {"id": {"type": "string"}}}

NULLABLE_REF_30: dict[str, Any] = {"nullable": True, "allOf": [{"$ref": "#/components/schemas/Reason"}]}
NULLABLE_REF_31: dict[str, Any] = {"anyOf": [{"$ref": "#/components/schemas/Reason"}, {"type": "null"}]}
NULLABLE_REF_31_ONE_OF: dict[str, Any] = {"oneOf": [{"$ref": "#/components/schemas/Reason"}, {"type": "null"}]}
ALIAS_REF: dict[str, Any] = {"allOf": [{"$ref": "#/components/schemas/Reason"}]}


def _context(**extra_schemas: Any) -> ParsingContext:
    raw = {"Reason": REASON, "Thing": THING, **extra_schemas}
    return ParsingContext(raw_spec_schemas=raw, parsed_schemas={}, visited_refs=set())


def _parse_probe(prop_node: dict[str, Any], context: ParsingContext) -> IRSchema:
    """Parse a one-property `Probe` object and return that property's IR."""
    probe = _parse_schema(
        "Probe",
        {"type": "object", "properties": {"nullableRef": prop_node}, "required": ["nullableRef"]},
        context,
    )
    return probe.properties["nullableRef"]


@pytest.mark.parametrize(
    "prop_node, expected_nullable",
    [
        pytest.param(NULLABLE_REF_30, True, id="openapi-3.0-allof-nullable"),
        pytest.param(NULLABLE_REF_31, True, id="openapi-3.1-anyof-null"),
        pytest.param(NULLABLE_REF_31_ONE_OF, True, id="openapi-3.1-oneof-null"),
        pytest.param({"$ref": "#/components/schemas/Reason", "nullable": True}, True, id="ref-sibling-nullable"),
        pytest.param(ALIAS_REF, False, id="single-member-allof-alias"),
    ],
)
def test_parse_schema__nullable_ref_property__resolves_to_referenced_schema(
    prop_node: dict[str, Any], expected_nullable: bool
) -> None:
    # Arrange
    context = _context()

    # Act
    prop_ir = _parse_probe(prop_node, context)

    # Assert: the property points at Reason, not at a schema minted for the field.
    assert prop_ir.type == "Reason"
    assert prop_ir.is_nullable is expected_nullable
    assert prop_ir._refers_to_schema is not None
    assert prop_ir._refers_to_schema.name == "Reason"


@pytest.mark.parametrize(
    "prop_node",
    [
        pytest.param(NULLABLE_REF_30, id="openapi-3.0-allof-nullable"),
        pytest.param(NULLABLE_REF_31, id="openapi-3.1-anyof-null"),
        pytest.param(NULLABLE_REF_31_ONE_OF, id="openapi-3.1-oneof-null"),
        pytest.param(ALIAS_REF, id="single-member-allof-alias"),
        pytest.param({"nullable": True, "allOf": [{"$ref": "#/components/schemas/Thing"}]}, id="nullable-object-ref"),
    ],
)
def test_parse_schema__nullable_ref_property__registers_no_synthetic_schema(prop_node: dict[str, Any]) -> None:
    # Arrange
    context = _context()

    # Act
    _parse_probe(prop_node, context)

    # Assert
    assert "ProbeNullableRef" not in context.parsed_schemas


def test_parse_schema__nullable_ref_property__does_not_mutate_the_referenced_schema() -> None:
    # Arrange: two properties referencing Reason, only one of them nullable.
    context = _context()

    # Act
    probe = _parse_schema(
        "Probe",
        {
            "type": "object",
            "properties": {
                "plainRef": {"$ref": "#/components/schemas/Reason"},
                "nullableRef": NULLABLE_REF_30,
            },
            "required": ["plainRef", "nullableRef"],
        },
        context,
    )

    # Assert: nullability belongs to the property, not to the shared component.
    assert probe.properties["plainRef"].is_nullable is False
    assert probe.properties["nullableRef"].is_nullable is True
    assert context.parsed_schemas["Reason"].is_nullable is False
    assert context.parsed_schemas["Reason"].name == "Reason"


@pytest.mark.parametrize(
    "prop_node",
    [
        pytest.param(NULLABLE_REF_30, id="openapi-3.0-allof-nullable"),
        pytest.param(NULLABLE_REF_31, id="openapi-3.1-anyof-null"),
    ],
)
def test_parse_schema__nullable_ref_property__keeps_wrapper_description(prop_node: dict[str, Any]) -> None:
    # Arrange
    context = _context()
    described = {**prop_node, "description": "why it happened"}

    # Act
    prop_ir = _parse_probe(described, context)

    # Assert
    assert prop_ir.description == "why it happened"


@pytest.mark.parametrize(
    "items_node",
    [
        pytest.param(NULLABLE_REF_30, id="openapi-3.0-allof-nullable"),
        pytest.param(NULLABLE_REF_31, id="openapi-3.1-anyof-null"),
    ],
)
def test_parse_schema__array_of_nullable_refs__resolves_items_without_synthetic_schema(
    items_node: dict[str, Any],
) -> None:
    # Arrange
    context = _context()

    # Act
    probe = _parse_schema(
        "Probe",
        {"type": "object", "properties": {"reasons": {"type": "array", "items": items_node}}},
        context,
    )
    items_ir = probe.properties["reasons"].items

    # Assert
    assert items_ir is not None
    assert items_ir.type == "Reason"
    assert items_ir.is_nullable is True
    assert "ProbeReasonsItem" not in context.parsed_schemas


def test_parse_schema__named_nullable_ref_component__stays_a_named_alias() -> None:
    # Arrange: a top-level component that is itself a nullable reference.
    context = _context(MaybeReason={"nullable": True, "allOf": [{"$ref": "#/components/schemas/Reason"}]})

    # Act
    schema = _parse_schema("MaybeReason", context.raw_spec_schemas["MaybeReason"], context)

    # Assert: it keeps its own name so it renders as `MaybeReason = Reason | None`.
    assert schema.name == "MaybeReason"
    assert schema.type == "Reason"
    assert schema.is_nullable is True
    assert schema.properties == {}
    assert context.parsed_schemas["MaybeReason"] is schema


@pytest.mark.parametrize(
    "prop_node, expected_nullable",
    [
        pytest.param({"anyOf": [{"$ref": "#/components/schemas/Reason"}, {"type": "string"}]}, False, id="union"),
        pytest.param(
            {"anyOf": [{"$ref": "#/components/schemas/Reason"}, {"type": "string"}, {"type": "null"}]},
            True,
            id="nullable-union",
        ),
    ],
)
def test_parse_schema__multi_member_union_property__remains_a_union(
    prop_node: dict[str, Any], expected_nullable: bool
) -> None:
    # Arrange
    context = _context()

    # Act
    prop_ir = _parse_probe(prop_node, context)

    # Assert: genuine unions are still promoted, and keep their nullability.
    assert prop_ir.is_nullable is expected_nullable
    assert "ProbeNullableRef" in context.parsed_schemas


def test_parse_schema__real_all_of_composition__still_merges_properties() -> None:
    # Arrange
    context = _context()
    node = {
        "allOf": [
            {"$ref": "#/components/schemas/Thing"},
            {"type": "object", "properties": {"extra": {"type": "integer"}}},
        ]
    }

    # Act
    schema = _parse_schema("Merged", node, context)

    # Assert
    assert schema.type == "object"
    assert set(schema.properties) == {"id", "extra"}
