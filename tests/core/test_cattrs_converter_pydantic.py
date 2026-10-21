"""Tests for the pydantic support in the cattrs runtime copied into clients generated with ``--model-type pydantic``."""

from __future__ import annotations

import dataclasses
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Literal

import pytest
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypeAliasType

from pyopenapi_gen.core.cattrs_converter import (
    _is_pydantic_model_class,
    _needs_pydantic,
    is_pydantic_model,
    structure_from_dict,
    unstructure_to_dict,
)
from pyopenapi_gen.core.http_transport import _prepare_multipart_parts
from pyopenapi_gen.core.utils import DataclassSerializer


class Color(str, Enum):
    RED = "red"
    DARK_BLUE = "dark-blue"


class Owner(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    full_name: str = Field(..., alias="fullName")


class Pet(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id_: int = Field(..., alias="id")
    color: Color
    created_at: datetime | None = Field(None, alias="createdAt")
    owner: Owner | None = None
    tags: list[str] = []


class Cat(BaseModel):
    kind: Literal["cat"]
    lives: int


class Dog(BaseModel):
    kind: Literal["dog"]
    good: bool


Animal = TypeAliasType("Animal", Annotated[Cat | Dog, Field(..., discriminator="kind")])
Ids = TypeAliasType("Ids", list[int])


@dataclasses.dataclass
class PlainDataclass:
    value: int


class TestDetection:
    def test_pydantic_model_class_and_instance__are_detected_separately(self) -> None:
        # Given / When / Then: the class is a model class but not a model instance, and vice versa
        assert _is_pydantic_model_class(Pet)
        assert not is_pydantic_model(Pet)
        assert is_pydantic_model(Pet(id_=1, color=Color.RED))

    @pytest.mark.parametrize("value", [PlainDataclass(1), {"a": 1}, [1], "text", None, PlainDataclass])
    def test_non_pydantic_values__are_not_detected(self, value: Any) -> None:
        assert not is_pydantic_model(value)

    @pytest.mark.parametrize("tp", [int, str, list[int], PlainDataclass, list[PlainDataclass], dict[str, Any], Any])
    def test_needs_pydantic__types_without_pydantic__false(self, tp: Any) -> None:
        assert not _needs_pydantic(tp)

    @pytest.mark.parametrize("tp", [Pet, list[Pet], dict[str, Pet], Pet | None, Animal, list[Ids], Ids])
    def test_needs_pydantic__models_aliases_and_containers_of_them__true(self, tp: Any) -> None:
        assert _needs_pydantic(tp)


class TestStructure:
    def test_structure__wire_payload__uses_aliases_enums_and_nested_models(self) -> None:
        # Given a camelCase wire payload
        payload = {
            "id": 7,
            "color": "dark-blue",
            "createdAt": "2026-01-02T03:04:05+00:00",
            "owner": {"fullName": "Ada"},
        }

        # When
        pet = structure_from_dict(payload, Pet)

        # Then
        assert pet.id_ == 7
        assert pet.color is Color.DARK_BLUE
        assert pet.created_at == datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        assert pet.owner is not None and pet.owner.full_name == "Ada"
        assert pet.tags == []

    def test_structure__list_of_models__each_item_validated(self) -> None:
        pets = structure_from_dict([{"id": 1, "color": "red"}, {"id": 2, "color": "red"}], list[Pet])

        assert [p.id_ for p in pets] == [1, 2]

    def test_structure__discriminated_union_alias__picks_variant_by_discriminator(self) -> None:
        animals = structure_from_dict(
            [{"kind": "cat", "lives": 9}, {"kind": "dog", "good": True}],
            list[Animal],  # type: ignore[valid-type]
        )

        assert isinstance(animals[0], Cat) and isinstance(animals[1], Dog)

    def test_structure__array_alias__validated_as_list(self) -> None:
        assert structure_from_dict([1, 2, 3], Ids) == [1, 2, 3]  # type: ignore[type-abstract]

    def test_structure__invalid_payload__raises_value_error_naming_wire_field_and_problem(self) -> None:
        # Given a payload with a wrongly typed field and a missing required field
        with pytest.raises(ValueError) as excinfo:
            structure_from_dict({"id": "x"}, Pet)

        # Then the message has the same "Failed to convert data to" shape as the cattrs path
        message = str(excinfo.value)
        assert message.startswith("Failed to convert data to Pet:")
        assert "- id:" in message
        assert "- color: Field required" in message

    def test_structure__adapter_is_cached_between_calls(self) -> None:
        from pyopenapi_gen.core import cattrs_converter

        structure_from_dict({"id": 1, "color": "red"}, Pet)
        first = cattrs_converter._pydantic_adapters[Pet]

        structure_from_dict({"id": 2, "color": "red"}, Pet)

        assert cattrs_converter._pydantic_adapters[Pet] is first

    def test_structure__dataclass_target__still_uses_cattrs(self) -> None:
        assert structure_from_dict({"value": 3}, PlainDataclass) == PlainDataclass(value=3)


class TestUnstructure:
    def test_unstructure__model__emits_wire_names_json_values_and_omits_none(self) -> None:
        pet = Pet(id_=7, color=Color.DARK_BLUE, created_at=datetime(2026, 1, 2, tzinfo=timezone.utc))

        wire = unstructure_to_dict(pet)

        assert wire["id"] == 7
        assert wire["color"] == "dark-blue"
        assert isinstance(wire["createdAt"], str)
        assert "owner" not in wire
        json.dumps(wire)  # must be JSON-serialisable as is

    def test_unstructure__models_nested_in_containers__converted_by_serializer(self) -> None:
        owner = Owner(full_name="Ada")

        wire = DataclassSerializer.serialize({"owners": [owner], "main": owner})

        assert wire == {"owners": [{"fullName": "Ada"}], "main": {"fullName": "Ada"}}

    def test_unstructure__round_trip__reproduces_payload(self) -> None:
        payload = {"id": 7, "color": "red", "owner": {"fullName": "Ada"}, "tags": ["a"]}

        assert DataclassSerializer.serialize(structure_from_dict(payload, Pet)) == payload


def test_multipart__pydantic_model_part__is_sent_as_json_part() -> None:
    """
    Scenario:
        A multipart body contains a pydantic model next to a plain field.

    Expected Outcome:
        The model is encoded as an ``application/json`` part using its wire names, like a dataclass would be.
    """
    parts = _prepare_multipart_parts({"owner": Owner(full_name="Ada"), "note": "hi"})

    by_name = {name: part for name, part in parts}
    _, payload, content_type = by_name["owner"]
    assert content_type == "application/json"
    assert json.loads(payload) == {"fullName": "Ada"}
