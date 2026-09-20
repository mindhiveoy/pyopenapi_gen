"""IR-level tests for referencing properties in OpenAPI 3.0 and 3.1 specs.

A reference - plain, nullable, or annotated - must resolve to the referenced
component, must not mint a per-field schema, and must never write use-site
details onto the shared component.
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


# --- OpenAPI 3.1 `$ref` with sibling annotations -----------------------------
# 3.0 forbids any key beside `$ref`; 3.1 allows annotations there, and they
# describe this use site rather than the component being referenced.

THING_WITH_DESCRIPTION: dict[str, Any] = {**THING, "description": "the component description"}


def _context_with_described_thing() -> ParsingContext:
    return ParsingContext(
        raw_spec_schemas={"Reason": REASON, "Thing": THING_WITH_DESCRIPTION},
        parsed_schemas={},
        visited_refs=set(),
    )


def test_parse_schema__ref_with_sibling_description__uses_the_sibling_description() -> None:
    # Arrange
    context = _context_with_described_thing()

    # Act
    prop_ir = _parse_probe({"$ref": "#/components/schemas/Thing", "description": "why this field exists"}, context)

    # Assert
    assert prop_ir.type == "Thing"
    assert prop_ir.description == "why this field exists"


def test_parse_schema__ref_with_sibling_annotations__does_not_mutate_the_component() -> None:
    # Arrange: one plain reference and one annotated reference to the same component.
    context = _context_with_described_thing()

    # Act
    probe = _parse_schema(
        "Probe",
        {
            "type": "object",
            "properties": {
                "plain": {"$ref": "#/components/schemas/Thing"},
                "annotated": {
                    "$ref": "#/components/schemas/Thing",
                    "description": "why this field exists",
                    "title": "Annotated thing",
                },
            },
        },
        context,
    )

    # Assert: the annotation stays on the use site.
    assert probe.properties["annotated"].description == "why this field exists"
    assert probe.properties["annotated"].title == "Annotated thing"
    # The component, and every plain reference to it, keep their own description.
    assert context.parsed_schemas["Thing"].description == "the component description"
    assert context.parsed_schemas["Thing"].title is None
    assert probe.properties["plain"].description == "the component description"


def test_parse_schema__bare_ref__still_resolves_to_the_shared_component() -> None:
    # Arrange
    context = _context_with_described_thing()

    # Act
    prop_ir = _parse_probe({"$ref": "#/components/schemas/Thing"}, context)

    # Assert: no holder is interposed when the reference carries nothing of its own.
    assert prop_ir is context.parsed_schemas["Thing"]


def test_parse_schema__ref_with_sibling_default__carries_the_default_to_the_use_site() -> None:
    # Arrange
    context = _context()

    # Act
    prop_ir = _parse_probe({"$ref": "#/components/schemas/Reason", "default": "missingRate"}, context)

    # Assert
    assert prop_ir.type == "Reason"
    assert prop_ir.default == "missingRate"
    assert context.parsed_schemas["Reason"].default is None


def test_parse_schema__ref_with_sibling_annotations__registers_no_synthetic_schema() -> None:
    # Arrange
    context = _context_with_described_thing()

    # Act
    _parse_probe({"$ref": "#/components/schemas/Thing", "description": "d"}, context)

    # Assert
    assert "ProbeNullableRef" not in context.parsed_schemas


def test_parse_schema__nullable_ref_with_sibling_description__keeps_both() -> None:
    # Arrange: 3.1 allows `description` beside the anyOf that spells nullability.
    context = _context_with_described_thing()

    # Act
    prop_ir = _parse_probe(
        {
            "description": "why this field exists",
            "anyOf": [{"$ref": "#/components/schemas/Thing"}, {"type": "null"}],
        },
        context,
    )

    # Assert
    assert prop_ir.type == "Thing"
    assert prop_ir.is_nullable is True
    assert prop_ir.description == "why this field exists"


@pytest.mark.parametrize(
    "prop_node, expected_example",
    [
        pytest.param({"type": "string", "example": "abc"}, "abc", id="openapi-3.0-example"),
        pytest.param({"type": "string", "examples": ["abc", "def"]}, "abc", id="openapi-3.1-examples"),
        # An explicit `example` wins over the array if a spec carries both.
        pytest.param({"type": "string", "example": "abc", "examples": ["zzz"]}, "abc", id="both-spellings"),
        pytest.param({"type": "string", "examples": []}, None, id="empty-examples"),
    ],
)
def test_parse_schema__example_spellings__normalize_to_a_single_example(
    prop_node: dict[str, Any], expected_example: Any
) -> None:
    # Arrange
    context = _context()

    # Act
    prop_ir = _parse_probe(prop_node, context)

    # Assert
    assert prop_ir.example == expected_example


def test_parse_schema__ref_with_sibling_examples__carries_the_first_example() -> None:
    # Arrange
    context = _context()

    # Act
    prop_ir = _parse_probe({"$ref": "#/components/schemas/Reason", "examples": ["missingRate"]}, context)

    # Assert
    assert prop_ir.type == "Reason"
    assert prop_ir.example == "missingRate"
    assert context.parsed_schemas["Reason"].example is None


# --- Shapes the wrapper machinery must not swallow ---------------------------


@pytest.mark.parametrize(
    "prop_node",
    [
        # `$ref` beside a structural keyword narrows the reference. The intersection
        # is not modelled, but the reference must still win - dropping it would be
        # the very "silently wrong type" this module exists to prevent.
        pytest.param({"$ref": "#/components/schemas/Thing", "type": "object"}, id="ref-plus-type"),
        pytest.param(
            {"$ref": "#/components/schemas/Thing", "type": "object", "description": "d"},
            id="ref-plus-type-and-annotation",
        ),
        pytest.param(
            {"$ref": "#/components/schemas/Thing", "properties": {"extra": {"type": "string"}}},
            id="ref-plus-properties",
        ),
    ],
)
def test_parse_schema__ref_beside_structural_keyword__still_resolves_to_the_reference(
    prop_node: dict[str, Any],
) -> None:
    # Arrange
    context = _context()

    # Act
    prop_ir = _parse_probe(prop_node, context)

    # Assert
    assert prop_ir.type in ("Thing", "object")
    assert prop_ir.properties.keys() <= {"id"}
    assert "ProbeNullableRef" not in context.parsed_schemas


def test_parse_schema__colliding_sanitized_names__keeps_both_schemas() -> None:
    # Arrange: two component names that sanitize to the same Python name, one of
    # them a nullable reference.
    raw = {
        "Thing": THING,
        "FooBar": {"type": "object", "properties": {"real": {"type": "string"}}},
        "Foo-Bar": {"nullable": True, "allOf": [{"$ref": "#/components/schemas/Thing"}]},
    }
    context = ParsingContext(raw_spec_schemas=raw, parsed_schemas={}, visited_refs=set())

    # Act
    _parse_schema("FooBar", raw["FooBar"], context)
    alias = _parse_schema("Foo-Bar", raw["Foo-Bar"], context)

    # Assert: the alias is registered rather than dropped, so the emitter can see it
    # and de-collide the names - it must not silently vanish behind the real FooBar.
    assert alias.type == "Thing"
    assert alias in context.parsed_schemas.values()
    assert context.parsed_schemas["FooBar"].properties.keys() == {"real"}


# --- Wrappers around inline (non-$ref) subschemas -----------------------------


@pytest.mark.parametrize(
    "prop_node",
    [
        pytest.param(
            {"nullable": True, "allOf": [{"type": "object", "properties": {"x": {"type": "string"}}}]},
            id="openapi-3.0-allof-inline-object",
        ),
        pytest.param(
            {"anyOf": [{"type": "object", "properties": {"x": {"type": "string"}}}, {"type": "null"}]},
            id="openapi-3.1-anyof-inline-object",
        ),
    ],
)
def test_parse_schema__wrapper_around_inline_object__promotes_it_and_keeps_nullability(
    prop_node: dict[str, Any],
) -> None:
    # Arrange
    context = _context()

    # Act
    prop_ir = _parse_probe(prop_node, context)

    # Assert: an inline object genuinely needs a model, so it is promoted - but the
    # wrapper's nullability travels with it.
    assert prop_ir.type == "ProbeNullableRef"
    assert prop_ir.is_nullable is True
    assert context.parsed_schemas["ProbeNullableRef"].properties.keys() == {"x"}


@pytest.mark.parametrize(
    "prop_node",
    [
        pytest.param({"nullable": True, "allOf": [{"type": "string"}]}, id="openapi-3.0-allof-inline-primitive"),
        pytest.param({"anyOf": [{"type": "string"}, {"type": "null"}]}, id="openapi-3.1-anyof-inline-primitive"),
    ],
)
def test_parse_schema__wrapper_around_inline_primitive__stays_inline(prop_node: dict[str, Any]) -> None:
    # Arrange
    context = _context()

    # Act
    prop_ir = _parse_probe(prop_node, context)

    # Assert
    assert prop_ir.type == "string"
    assert prop_ir.is_nullable is True
    assert "ProbeNullableRef" not in context.parsed_schemas


def test_parse_schema__wrapper_around_inline_object__carries_the_wrapper_description() -> None:
    # Arrange
    context = _context()

    # Act
    prop_ir = _parse_probe(
        {
            "description": "why this field exists",
            "anyOf": [{"type": "object", "properties": {"x": {"type": "string"}}}, {"type": "null"}],
        },
        context,
    )

    # Assert
    assert prop_ir.description == "why this field exists"
    assert prop_ir.is_nullable is True


@pytest.mark.parametrize("bad_ref", ["", "#/"])
def test_parse_schema__wrapper_around_malformed_ref__keeps_nullability(bad_ref: str) -> None:
    # Arrange
    context = _context()

    # Act
    prop_ir = _parse_probe({"nullable": True, "allOf": [{"$ref": bad_ref}]}, context)

    # Assert: nothing to point at, so it degrades to an unresolved placeholder -
    # but the field is still known to be nullable.
    assert prop_ir.is_nullable is True
    assert prop_ir._from_unresolved_ref is True


def test_parse_schema__wrapper_around_unresolvable_ref__degrades_without_losing_nullability() -> None:
    # Arrange
    context = _context()

    # Act
    prop_ir = _parse_probe({"nullable": True, "allOf": [{"$ref": "#/components/schemas/Missing"}]}, context)

    # Assert
    assert prop_ir.is_nullable is True
    assert prop_ir.description is not None and "Unresolved $ref" in prop_ir.description


def test_parse_schema__ref_with_sibling_example__carries_the_example() -> None:
    # Arrange
    context = _context()

    # Act
    prop_ir = _parse_probe({"$ref": "#/components/schemas/Reason", "example": "missingRate"}, context)

    # Assert
    assert prop_ir.type == "Reason"
    assert prop_ir.example == "missingRate"
