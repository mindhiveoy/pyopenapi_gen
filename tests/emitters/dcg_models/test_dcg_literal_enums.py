"""Inline (spec-anonymous) enums are rendered as ``Literal[...]`` fields by the datamodel-code-generator backend."""

from __future__ import annotations

import importlib
import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.emitters.dcg_models.ir_to_openapi import IRSchemaSerializer
from pyopenapi_gen.emitters.dcg_models.literal_enums import find_literal_enums, is_literal_candidate
from pyopenapi_gen.emitters.dcg_models.renderer import DcgModelRenderer
from pyopenapi_gen.generator.client_generator import ClientGenerator
from pyopenapi_gen.ir import HTTPMethod, IROperation, IRParameter, IRResponse, ModelBackend, ModelType


def _enum(name: str, values: list[Any], derived: bool = True, type_: str = "string") -> IRSchema:
    return IRSchema(name=name, generation_name=name, type=type_, enum=values, _is_name_derived=derived)


def _model(name: str, **properties: IRSchema) -> IRSchema:
    return IRSchema(name=name, generation_name=name, type="object", required=list(properties), properties=properties)


def _ref(target: IRSchema) -> IRSchema:
    """A property that refers to ``target`` the way the parser leaves it."""
    return IRSchema(type=target.name, _refers_to_schema=target)


def _operation(parameter_schema: IRSchema | None = None, response_schema: IRSchema | None = None) -> IROperation:
    return IROperation(
        operation_id="op",
        method=HTTPMethod.GET,
        path="/op",
        summary=None,
        description=None,
        parameters=(
            [IRParameter(name="p", param_in="query", required=False, schema=parameter_schema)]
            if parameter_schema
            else []
        ),
        responses=(
            [IRResponse(status_code="200", description="ok", content={"application/json": response_schema})]
            if response_schema
            else []
        ),
    )


class TestIsLiteralCandidate:
    def test_is_literal_candidate__generator_named_string_enum__true(self) -> None:
        assert is_literal_candidate(_enum("PetState", ["a"]))

    @pytest.mark.parametrize(
        "schema",
        [
            _enum("PetState", ["a"], derived=False),
            _enum("PetState", [], derived=True),
            _enum("PetState", [True], type_="boolean"),
            IRSchema(name="PetState", type="string", _is_name_derived=True),
        ],
        ids=["named-in-spec", "no-values", "unsupported-type", "not-an-enum"],
    )
    def test_is_literal_candidate__not_an_inline_string_or_integer_enum__false(self, schema: IRSchema) -> None:
        assert not is_literal_candidate(schema)


class TestFindLiteralEnums:
    def test_find_literal_enums__generator_named_enum_used_as_property__returned(self) -> None:
        # Given
        state = _enum("PetState", ["new", "old"])
        pet = _model("Pet", state=_ref(state))

        # When / Then
        assert find_literal_enums([pet, state], []) == [state]

    def test_find_literal_enums__enum_referenced_by_name_only__returned(self) -> None:
        # Given the shape ``extract_inline_enums`` leaves: the property's ``type`` is the enum's name
        state = _enum("PetState", ["new"])
        pet = _model("Pet", state=IRSchema(type="PetState"))

        # When / Then
        assert find_literal_enums([pet, state], []) == [state]

    def test_find_literal_enums__integer_enum__returned(self) -> None:
        level = _enum("PetLevel", [1, 2], type_="integer")

        assert find_literal_enums([_model("Pet", level=_ref(level)), level], []) == [level]

    def test_find_literal_enums__enum_named_in_the_spec__kept_as_class(self) -> None:
        state = _enum("PetState", ["new"], derived=False)

        assert find_literal_enums([_model("Pet", state=_ref(state)), state], []) == []

    def test_find_literal_enums__enum_not_used_by_any_model__not_returned(self) -> None:
        assert find_literal_enums([_enum("PetState", ["new"])], []) == []

    def test_find_literal_enums__no_schemas__empty(self) -> None:
        assert find_literal_enums([], []) == []

    @pytest.mark.parametrize(
        "use",
        [
            lambda e: IRSchema(type="array", items=_ref(e)),
            lambda e: IRSchema(one_of=[_ref(e), IRSchema(type="integer")]),
            lambda e: IRSchema(any_of=[_ref(e), IRSchema(type="integer")]),
            lambda e: IRSchema(type="object", additional_properties=_ref(e)),
            lambda e: IRSchema(type="object", properties={"nested": _ref(e)}),
        ],
        ids=["array-item", "one-of-member", "any-of-member", "additional-properties", "anonymous-nested-object"],
    )
    def test_find_literal_enums__enum_also_used_in_another_position__kept_as_class(self, use: Any) -> None:
        # Given one property use (literal-able) and one use that needs a class
        state = _enum("PetState", ["new"])
        pet = _model("Pet", state=_ref(state), other=use(state))

        # When / Then the class is needed, so no property of it may become a literal either
        assert find_literal_enums([pet, state], []) == []

    def test_find_literal_enums__enum_used_by_an_operation__kept_as_class(self) -> None:
        state = _enum("PetState", ["new"])
        pet = _model("Pet", state=_ref(state))

        assert find_literal_enums([pet, state], [_operation(parameter_schema=_ref(state))]) == []

    def test_find_literal_enums__enum_inside_an_anonymous_response_body__kept_as_class(self) -> None:
        state = _enum("PetState", ["new"])
        pet = _model("Pet", state=_ref(state))
        body = IRSchema(type="object", properties={"state": _ref(state)})

        assert find_literal_enums([pet, state], [_operation(response_schema=body)]) == []

    def test_find_literal_enums__operation_returning_a_rendered_model__does_not_disqualify_its_enums(self) -> None:
        state = _enum("PetState", ["new"])
        pet = _model("Pet", state=_ref(state))

        assert find_literal_enums([pet, state], [_operation(response_schema=_ref(pet))]) == [state]

    def test_find_literal_enums__allof_members_merged_into_properties__enum_still_returned(self) -> None:
        # Given the parser's shape for ``allOf: [Base, {properties: {status: enum}}]``: the member's
        # properties are also merged into the parent, and the serializer renders only the merged ones
        status = _enum("ResultStatus", ["ok"])
        member = IRSchema(type="object", properties={"status": _ref(status)})
        result = IRSchema(
            name="Result", generation_name="Result", type="object", properties={"status": _ref(status)}, all_of=[member]
        )

        # When / Then
        assert find_literal_enums([result, status], []) == [status]

    def test_find_literal_enums__two_enums_with_the_same_ir_name__neither_resolved_by_name(self) -> None:
        # Given two generator-named enums that share an IR name, a bare name cannot pick one
        first, second = _enum("State", ["a"]), _enum("State", ["b"])
        second.generation_name = "State2"
        pet = _model("Pet", state=IRSchema(type="State"))

        assert find_literal_enums([pet, first, second], []) == []


class TestSerializer:
    def test_serialize__literal_enum__inlined_with_values_and_reported_without_definition(self) -> None:
        # Given
        state = _enum("PetState", ["new", "old"])
        pet = _model("Pet", state=_ref(state))

        # When
        result = IRSchemaSerializer([pet], literal_enums=[state]).serialize()

        # Then
        assert result.document["components"]["schemas"]["Pet"]["properties"]["state"] == {
            "type": "string",
            "enum": ["new", "old"],
        }
        assert "PetState" not in result.document["components"]["schemas"]
        assert result.literal_enum_fields == frozenset({"state"})

    def test_serialize__nullable_literal_enum__allows_null(self) -> None:
        state = _enum("PetState", ["new"])
        ref = _ref(state)
        ref.is_nullable = True
        pet = IRSchema(name="Pet", generation_name="Pet", type="object", properties={"state": ref})

        result = IRSchemaSerializer([pet], literal_enums=[state]).serialize()

        node = result.document["components"]["schemas"]["Pet"]["properties"]["state"]
        assert node == {"anyOf": [{"type": "string", "enum": ["new"]}, {"type": "null"}]}

    def test_serialize__literal_field_with_renamed_attribute__reports_python_attribute_name(self) -> None:
        # Given a JSON key that sanitises to a different attribute name
        kind = _enum("PetKind", ["cat"])
        pet = _model("Pet", **{"petKind": _ref(kind)})

        # When
        result = IRSchemaSerializer([pet], keep_json_names=True, literal_enums=[kind]).serialize()

        # Then DCG matches its literal map against the final attribute name, not the document key
        assert result.literal_enum_fields == frozenset({"pet_kind"})
        assert "petKind" in result.document["components"]["schemas"]["Pet"]["properties"]

    def test_serialize__no_literal_enums__reports_no_fields(self) -> None:
        state = _enum("PetState", ["new"])
        pet = _model("Pet", state=_ref(state))

        result = IRSchemaSerializer([pet, state]).serialize()

        assert result.literal_enum_fields == frozenset()
        assert result.document["components"]["schemas"]["Pet"]["properties"]["state"] == {
            "$ref": "#/components/schemas/PetState"
        }


class TestRenderer:
    @pytest.mark.parametrize("model_type", [ModelType.DATACLASS, ModelType.PYDANTIC])
    def test_render__literal_enum__field_is_a_literal_and_no_class_is_generated(self, model_type: ModelType) -> None:
        # Given a model with an inline enum field and one that refers to a spec-named enum of the same name
        state = _enum("PetState", ["new", "old"])
        named = _enum("Status", ["on", "off"], derived=False)
        pet = _model("Pet", state=_ref(state))
        device = _model("Device", state=_ref(named))

        # When
        result = DcgModelRenderer(model_type).render([pet, device, named], literal_enums=[state])

        # Then
        pet_source = result.files[f"{result.locations['Pet'].module_stem}.py"]
        assert "Literal['new', 'old']" in pet_source
        assert "PetState" not in result.locations
        device_source = result.files[f"{result.locations['Device'].module_stem}.py"]
        assert "Literal" not in device_source  # same field name, but a $ref'd enum stays a class
        assert "class Status" in result.files[f"{result.locations['Status'].module_stem}.py"]

    def test_render__renamed_pydantic_field__still_a_literal(self) -> None:
        # Given a JSON key that DCG renames through an alias (``type`` -> ``type_``)
        kind = _enum("PetType", ["cat"])
        pet = _model("Pet", type=_ref(kind))

        result = DcgModelRenderer(ModelType.PYDANTIC).render([pet], literal_enums=[kind])

        source = result.files[f"{result.locations['Pet'].module_stem}.py"]
        assert "type_: Annotated[Literal['cat'], Field(alias='type')]" in source or "Literal['cat']" in source


SPEC: dict[str, Any] = {
    "openapi": "3.1.0",
    "info": {"title": "Pets", "version": "1.0.0"},
    "paths": {
        "/pets": {
            "get": {
                "operationId": "listPets",
                "tags": ["pets"],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Pet"}}},
                    }
                },
            }
        }
    },
    "components": {
        "schemas": {
            "Species": {"type": "string", "enum": ["cat", "dog"]},
            "Pet": {
                "type": "object",
                "required": ["species", "state", "type"],
                "properties": {
                    "species": {"$ref": "#/components/schemas/Species"},
                    "state": {"type": "string", "enum": ["new", "adopted"]},
                    "type": {"type": "string", "enum": ["pet"]},
                    "rank": {"type": "integer", "enum": [1, 2]},
                },
            },
            "Cat": {
                "allOf": [
                    {"$ref": "#/components/schemas/Pet"},
                    {
                        "type": "object",
                        "properties": {"stray": {"type": "string", "enum": ["yes", "no"]}},
                    },
                ]
            },
        }
    },
}
PACKAGE = "literal_enum_client"


def _squash(source: str) -> str:
    """Source without whitespace, quote style or trailing commas, so assertions ignore post-processing."""
    return re.sub(r",(?=[\]\)])", "", re.sub(r"\s+", "", source)).replace('"', "'")


@pytest.fixture(params=[ModelType.DATACLASS, ModelType.PYDANTIC], ids=lambda t: t.value)
def generated(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[Path]:
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(SPEC))
    root = tmp_path / "project"
    ClientGenerator().generate(
        spec_path=str(spec_file),
        project_root=root,
        output_package=PACKAGE,
        force=True,
        no_postprocess=False,
        model_backend=ModelBackend.DCG,
        model_type=request.param,
    )
    sys.path.insert(0, str(root))
    importlib.invalidate_caches()
    try:
        yield root
    finally:
        sys.path.remove(str(root))
        for name in [m for m in sys.modules if m == PACKAGE or m.startswith(f"{PACKAGE}.")]:
            del sys.modules[name]


def test_generated_client__inline_enums__are_literals_and_spec_named_enum_stays_a_class(generated: Path) -> None:
    """
    Scenario:
        A spec has a component enum (``Species``) and properties with inline enums (``state``, ``type``,
        ``rank``), one of them re-declared in an ``allOf`` member of another schema.

    Expected Outcome:
        The inline enums become ``Literal`` fields with no class, module or export of their own; the
        component enum is still a class; the generated package imports.
    """
    models_dir = generated / PACKAGE / "models"
    modules = {p.stem for p in models_dir.glob("*.py")}
    assert "species" in modules
    assert not modules & {"pet_state", "pet_type", "pet_rank", "cat_stray"}
    pet_source = _squash((models_dir / "pet.py").read_text())
    assert "Literal['new','adopted']" in pet_source
    assert "Literal['pet']" in pet_source
    assert "Literal[1,2]" in pet_source
    assert "Literal['yes','no']" in _squash((models_dir / "cat.py").read_text())
    init_source = (models_dir / "__init__.py").read_text()
    assert "Species" in init_source and "PetState" not in init_source and "CatStray" not in init_source

    models = importlib.import_module(f"{PACKAGE}.models")
    assert {member.value for member in models.Species} == {"cat", "dog"}


def test_generated_client__literal_fields__round_trip_through_the_cattrs_runtime(generated: Path) -> None:
    """
    Scenario:
        A payload with literal-typed fields is structured and unstructured with the generated runtime.

    Expected Outcome:
        Values survive the round trip, and a value outside the literal is rejected.
    """
    models = importlib.import_module(f"{PACKAGE}.models")
    converter = importlib.import_module(f"{PACKAGE}.core.cattrs_converter")
    payload = {"species": "cat", "state": "adopted", "type": "pet", "rank": 2}

    pet = converter.structure_from_dict(payload, models.Pet)

    assert pet.state == "adopted" and pet.rank == 2
    assert converter.unstructure_to_dict(pet) == payload
    with pytest.raises(Exception, match="(?i)state|literal|adopted|valid"):
        converter.structure_from_dict({**payload, "state": "lost"}, models.Pet)
