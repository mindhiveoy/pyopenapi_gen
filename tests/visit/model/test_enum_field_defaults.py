"""Tests for rendering a default value on an enum-typed dataclass field.

A default must be emitted as the enum member it names, not as the raw literal
from the spec: the field is annotated with the enum type, so a bare string or int
makes the generated client lie about its own type.
"""

from typing import Any

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer
from pyopenapi_gen.visit.model.dataclass_generator import DataclassGenerator
from pyopenapi_gen.visit.model.enum_generator import EnumGenerator


def _enum_schema(name: str, type_: str, values: list[Any]) -> IRSchema:
    schema = IRSchema(name=name, type=type_, enum=values)
    schema.generation_name = name
    schema.final_module_stem = name.lower()
    return schema


@pytest.fixture
def priority() -> IRSchema:
    return _enum_schema("Priority", "string", ["default", "high"])


@pytest.fixture
def level() -> IRSchema:
    return _enum_schema("Level", "integer", [1, 2])


def _render_probe(prop: IRSchema, all_schemas: dict[str, IRSchema]) -> str:
    probe = IRSchema(name="Probe", type="object", properties={"field": prop}, required=[])
    probe.generation_name = "Probe"
    probe.final_module_stem = "probe"
    schemas = {**all_schemas, "Probe": probe}
    context = RenderContext()
    context.set_current_file("models/probe.py")
    return DataclassGenerator(PythonConstructRenderer(), schemas).generate(probe, "Probe", context)


def test_dataclass_generator__defaulted_string_enum_reference__renders_enum_member(
    priority: IRSchema,
) -> None:
    """A `$ref` to a string enum with a default renders the member, not the raw string."""
    # Arrange: the property references Priority and carries a default (the OpenAPI 3.0
    # `{default: ..., allOf: [{$ref}]}` shape parses to exactly this).
    prop = IRSchema(name="field", type="Priority", default="default")
    prop._refers_to_schema = priority

    # Act
    code = _render_probe(prop, {"Priority": priority})

    # Assert
    assert "Priority.DEFAULT" in code
    assert '= "default"' not in code


def test_dataclass_generator__defaulted_integer_enum_reference__renders_enum_member(
    level: IRSchema,
) -> None:
    """Integer enums name members VALUE_<n>, so the raw int is never a valid member."""
    # Arrange
    prop = IRSchema(name="field", type="Level", default=1)
    prop._refers_to_schema = level

    # Act
    code = _render_probe(prop, {"Level": level})

    # Assert
    assert "Level.VALUE_1" in code
    assert "= 1" not in code


def test_dataclass_generator__defaulted_inline_enum__renders_enum_member() -> None:
    """An enum declared inline on the property is resolved the same way."""
    # Arrange
    inline = _enum_schema("ProbeField", "string", ["a", "b"])
    prop = IRSchema(name="field", type="ProbeField", default="b")
    prop._refers_to_schema = inline

    # Act
    code = _render_probe(prop, {"ProbeField": inline})

    # Assert
    assert "ProbeField.B" in code


def test_dataclass_generator__defaulted_primitive__still_renders_a_literal() -> None:
    """Non-enum defaults are unaffected."""
    # Arrange
    prop = IRSchema(name="field", type="string", default="hello")

    # Act
    code = _render_probe(prop, {})

    # Assert
    assert '= "hello"' in code


def test_dataclass_generator__default_absent_from_enum__falls_back_to_the_literal() -> None:
    """A spec whose default is not one of the enum values must not invent a member."""
    # Arrange: "urgent" is not a Priority value.
    priority = _enum_schema("Priority", "string", ["default", "high"])
    prop = IRSchema(name="field", type="Priority", default="urgent")
    prop._refers_to_schema = priority

    # Act
    code = _render_probe(prop, {"Priority": priority})

    # Assert: no fabricated `Priority.URGENT`.
    assert "Priority.URGENT" not in code


def test_enum_generator__member_names_by_value__matches_the_generated_enum() -> None:
    """The mapping used for defaults must agree with the enum actually emitted."""
    # Arrange: two values that sanitise to the same member name, forcing disambiguation.
    schema = _enum_schema("Tricky", "string", ["a-b", "a b"])
    context = RenderContext()
    context.set_current_file("models/tricky.py")

    # Act
    mapping = EnumGenerator.member_names_by_value(schema)
    code = EnumGenerator(PythonConstructRenderer()).generate(schema, "Tricky", context)

    # Assert: every name the mapping reports is really a member of the rendered enum.
    assert set(mapping) == {"a-b", "a b"}
    for member_name in mapping.values():
        assert f"{member_name} = " in code
    assert len(set(mapping.values())) == 2, "duplicate names must be disambiguated"
