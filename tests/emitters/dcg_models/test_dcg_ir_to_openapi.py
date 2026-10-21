"""Unit tests for IRSchemaSerializer: the IR -> OpenAPI document step of the datamodel-code-generator backend."""

from __future__ import annotations

from typing import Any

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.emitters.dcg_models.ir_to_openapi import IRSchemaSerializer, SerializedModels
from pyopenapi_gen.ir import IRDiscriminator


def _named(name: str, **kwargs: Any) -> IRSchema:
    return IRSchema(name=name, generation_name=name, **kwargs)


def _serialize(*schemas: IRSchema) -> SerializedModels:
    return IRSchemaSerializer(list(schemas)).serialize()


def _definitions(result: SerializedModels) -> dict[str, Any]:
    definitions: dict[str, Any] = result.document["components"]["schemas"]
    return definitions


class TestConstructorContracts:
    def test_missing_generation_name__raises_assertion(self) -> None:
        # Given a schema that never went through name de-collision
        schema = IRSchema(name="Pet", type="object")

        # When / Then the serializer refuses it rather than inventing a class name
        with pytest.raises(AssertionError, match="generation_name"):
            IRSchemaSerializer([schema])

    def test_duplicate_generation_names__raises_assertion(self) -> None:
        with pytest.raises(AssertionError, match="unique"):
            IRSchemaSerializer([_named("Pet", type="object"), _named("Pet", type="object")])


class TestObjects:
    def test_required_then_optional_properties__ordered_required_first_then_alphabetical(self) -> None:
        # Given
        pet = _named(
            "Pet",
            type="object",
            required=["name"],
            properties={
                "zeta": IRSchema(type="string"),
                "alpha": IRSchema(type="integer"),
                "name": IRSchema(type="string"),
            },
        )

        # When
        result = _serialize(pet)

        # Then
        assert result.field_names["Pet"] == ["name", "alpha", "zeta"]
        assert list(_definitions(result)["Pet"]["properties"]) == ["name", "alpha", "zeta"]
        assert _definitions(result)["Pet"]["required"] == ["name"]

    def test_property_needing_sanitising__renamed_and_recorded_in_field_mappings(self) -> None:
        # Given a property whose JSON key is a Python builtin and another that is camelCase
        pet = _named(
            "Pet",
            type="object",
            required=["id", "createdAt"],
            properties={"id": IRSchema(type="integer"), "createdAt": IRSchema(type="string", format="date-time")},
        )

        # When
        result = _serialize(pet)

        # Then the document already uses Python names and the mapping remembers the JSON keys
        assert result.field_mappings["Pet"] == {"id": "id_", "createdAt": "created_at"}
        assert set(_definitions(result)["Pet"]["properties"]) == {"id_", "created_at"}

    def test_properties_sanitising_to_same_name__second_gets_numeric_suffix(self) -> None:
        # Given
        schema = _named(
            "Clash",
            type="object",
            properties={"user-name": IRSchema(type="string"), "user_name": IRSchema(type="string")},
        )

        # When
        result = _serialize(schema)

        # Then
        assert sorted(result.field_names["Clash"]) == ["user_name", "user_name_2"]

    def test_identity_shared_named_schema__emitted_as_ref(self) -> None:
        # Given a property that points at another named schema by object identity
        owner = _named("Owner", type="object", properties={"name": IRSchema(type="string")})
        pet = _named("Pet", type="object", required=["owner"], properties={"owner": owner})

        # When
        result = _serialize(pet, owner)

        # Then
        assert _definitions(result)["Pet"]["properties"]["owner"] == {"$ref": "#/components/schemas/Owner"}

    def test_reference_to_schema_outside_the_rendered_set__inlined_not_dangling_ref(self) -> None:
        # Given a property typed by a named enum the caller chose not to render
        unrendered = _named("Skipped", type="string", enum=["a"])
        pet = _named("Pet", type="object", properties={"kind": unrendered})

        # When only Pet is serialized
        result = _serialize(pet)

        # Then the property is a plain string, never a $ref to a definition that does not exist
        assert _definitions(result)["Pet"]["properties"]["kind"] == {"type": "string"}

    def test_optional_array_and_anonymous_object__default_to_empty_containers(self) -> None:
        # Given
        schema = _named(
            "Holder",
            type="object",
            properties={
                "tags": IRSchema(type="array", items=IRSchema(type="string")),
                "extra": IRSchema(type="object"),
                "label": IRSchema(type="string", default="x"),
                "note": IRSchema(type="string"),
            },
        )

        # When
        props = _definitions(_serialize(schema))["Holder"]["properties"]

        # Then
        assert props["tags"]["default"] == []
        assert props["extra"]["default"] == {}
        assert props["label"]["default"] == "x"
        assert "default" not in props["note"]

    def test_anonymous_object_with_properties__degrades_to_plain_object_and_is_counted(self) -> None:
        # Given a nested inline object that has properties but no class name
        inner = IRSchema(type="object", properties={"a": IRSchema(type="string")})
        outer = _named("Outer", type="object", properties={"inner": inner})

        # When
        result = _serialize(outer)

        # Then
        assert result.anonymous_objects_flattened == 1
        assert _definitions(result)["Outer"]["properties"]["inner"]["type"] == "object"
        assert "properties" not in _definitions(result)["Outer"]["properties"]["inner"]


class TestKeepJsonNames:
    def test_keep_json_names__document_keeps_wire_keys_but_reports_python_names(self) -> None:
        # Given a model whose keys need sanitising (the pydantic flavour maps them back with aliases)
        pet = _named(
            "Pet",
            type="object",
            required=["id", "createdAt"],
            properties={"id": IRSchema(type="integer"), "createdAt": IRSchema(type="string", format="date-time")},
        )

        # When
        result = IRSchemaSerializer([pet], keep_json_names=True).serialize()

        # Then the document uses JSON keys (DCG derives the alias from them) ...
        assert set(_definitions(result)["Pet"]["properties"]) == {"id", "createdAt"}
        assert set(_definitions(result)["Pet"]["required"]) == {"id", "createdAt"}
        # ... while the expected attribute names and the key -> name mapping are unchanged
        assert sorted(result.field_names["Pet"]) == ["created_at", "id_"]
        assert result.field_mappings["Pet"] == {"id": "id_", "createdAt": "created_at"}


class TestNullability:
    def test_nullable_primitive__type_list_includes_null(self) -> None:
        holder = _named("Holder", type="object", properties={"n": IRSchema(type="string", is_nullable=True)})

        node = _definitions(_serialize(holder))["Holder"]["properties"]["n"]

        assert node["type"] == ["string", "null"]

    def test_nullable_reference__wrapped_in_any_of_with_null(self) -> None:
        other = _named("Other", type="object", properties={"a": IRSchema(type="string")})
        ref = IRSchema(type="object", is_nullable=True)
        ref._refers_to_schema = other
        holder = _named("Holder", type="object", properties={"o": ref})

        node = _definitions(_serialize(holder, other))["Holder"]["properties"]["o"]

        assert node == {"anyOf": [{"$ref": "#/components/schemas/Other"}, {"type": "null"}]}

    def test_untyped_nullable__stays_any(self) -> None:
        holder = _named("Holder", type="object", properties={"v": IRSchema(type=None, is_nullable=True)})

        assert _definitions(_serialize(holder))["Holder"]["properties"]["v"] == {}


class TestEnums:
    def test_named_string_enum__keeps_values_and_legacy_member_names(self) -> None:
        # Given
        status = _named("Status", type="string", enum=["active", "in-progress"])

        # When
        node = _definitions(_serialize(status))["Status"]

        # Then
        assert node["enum"] == ["active", "in-progress"]
        assert node["x-enum-varnames"] == ["ACTIVE", "IN_PROGRESS"]

    def test_anonymous_inline_enum__rendered_as_primitive_not_enum(self) -> None:
        # Given two anonymous one-value enums inside a union (the shape that made DCG emit a self-referencing alias)
        name = _named(
            "Name",
            any_of=[IRSchema(type="string", enum=["a"]), IRSchema(type="string", enum=["b"])],
        )

        # When
        members = _definitions(_serialize(name))["Name"]["anyOf"]

        # Then DCG is given nothing it would have to name
        assert members == [{"type": "string"}, {"type": "string"}]


class TestCompositions:
    def test_one_of_with_discriminator__mapping_uses_generation_names(self) -> None:
        # Given
        cat = _named("Cat", type="object", properties={"kind": IRSchema(type="string")})
        dog = _named("Dog", type="object", properties={"kind": IRSchema(type="string")})
        pet = _named(
            "Pet",
            one_of=[cat, dog],
            discriminator=IRDiscriminator(
                property_name="kind",
                mapping={"cat": "#/components/schemas/Cat", "dog": "#/components/schemas/Dog"},
            ),
        )

        # When
        node = _definitions(_serialize(pet, cat, dog))["Pet"]

        # Then
        assert node["oneOf"] == [{"$ref": "#/components/schemas/Cat"}, {"$ref": "#/components/schemas/Dog"}]
        assert node["discriminator"] == {
            "propertyName": "kind",
            "mapping": {"cat": "#/components/schemas/Cat", "dog": "#/components/schemas/Dog"},
        }

    def test_array_of_named_schema__items_is_ref(self) -> None:
        item = _named("Item", type="object", properties={"a": IRSchema(type="string")})
        items = _named("Items", type="array", items=item)

        assert _definitions(_serialize(items, item))["Items"] == {
            "type": "array",
            "items": {"$ref": "#/components/schemas/Item"},
        }

    def test_all_of__parts_emitted_as_refs(self) -> None:
        base = _named("Base", type="object", properties={"a": IRSchema(type="string")})
        child = _named("Child", all_of=[base, IRSchema(type="object", properties={"b": IRSchema(type="string")})])

        node = _definitions(_serialize(child, base))["Child"]

        assert node["allOf"][0] == {"$ref": "#/components/schemas/Base"}
        assert len(node["allOf"]) == 2

    def test_type_null_schema__treated_as_any_not_null_type(self) -> None:
        # The parser uses ``type: null`` for "unknown"; legacy renders Any, so no ``type`` may be emitted.
        alias = _named("Whatever", type="null")

        assert "type" not in _definitions(_serialize(alias))["Whatever"]


class TestFreeForm:
    @pytest.mark.parametrize(
        ("additional", "expected"),
        [
            (True, {"type": "object", "additionalProperties": True}),
            (None, {"type": "object"}),
            (IRSchema(type="string"), {"type": "object", "additionalProperties": {"type": "string"}}),
        ],
    )
    def test_object_without_properties__additional_properties_carried_over(
        self, additional: Any, expected: dict[str, Any]
    ) -> None:
        schema = _named("Bag", type="object", additional_properties=additional)

        assert _definitions(_serialize(schema))["Bag"] == expected


def test_serialize__document_has_one_definition_per_named_schema() -> None:
    a = _named("A", type="string")
    b = _named("B", type="integer")

    result = _serialize(a, b)

    assert set(_definitions(result)) == {"A", "B"}
    assert result.definitions == frozenset({"A", "B"})
    assert result.document["openapi"] == "3.1.0"
