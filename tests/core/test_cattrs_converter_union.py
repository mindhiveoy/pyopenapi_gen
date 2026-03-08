"""
Tests for Union type structure hook in cattrs converter.

These tests verify that the cattrs converter can correctly structure Union types
that are commonly generated from OpenAPI oneOf/anyOf schemas.
"""

from dataclasses import dataclass
from typing import Annotated, Any, Union

import pytest

from pyopenapi_gen.core.cattrs_converter import converter, structure_from_dict

# =============================================================================
# Test Fixtures - Dataclasses representing Union variants
# =============================================================================


@dataclass
class ConfigTypeA:
    """First variant with type_a specific field."""

    type_: str
    value_a: str

    class Meta:
        key_transform_with_load = {"type": "type_", "valueA": "value_a"}
        key_transform_with_dump = {"type_": "type", "value_a": "valueA"}


@dataclass
class ConfigTypeB:
    """Second variant with type_b specific field."""

    type_: str
    value_b: int

    class Meta:
        key_transform_with_load = {"type": "type_", "valueB": "value_b"}
        key_transform_with_dump = {"type_": "type", "value_b": "valueB"}


@dataclass
class ConfigTypeC:
    """Third variant with nested data."""

    type_: str
    nested_config: str

    class Meta:
        key_transform_with_load = {"type": "type_", "nestedConfig": "nested_config"}
        key_transform_with_dump = {"type_": "type", "nested_config": "nestedConfig"}


@dataclass
class WrapperWithUnion:
    """Wrapper dataclass containing a Union-typed field."""

    id_: int
    config: Union[ConfigTypeA, ConfigTypeB, dict[str, Any], None]

    class Meta:
        key_transform_with_load = {"id": "id_"}
        key_transform_with_dump = {"id_": "id"}


@dataclass
class WrapperWithRequiredUnion:
    """Wrapper dataclass containing a required Union-typed field (no None)."""

    id_: int
    config: Union[ConfigTypeA, ConfigTypeB, dict[str, Any]]

    class Meta:
        key_transform_with_load = {"id": "id_"}
        key_transform_with_dump = {"id_": "id"}


# =============================================================================
# Test: Union with multiple dataclass variants
# =============================================================================


def test_structure_union__dataclass_variant_a__structures_correctly():
    """
    Test structuring Union type where data matches first dataclass variant.

    Scenario:
        API response contains data that matches ConfigTypeA structure.

    Expected Outcome:
        Data is correctly structured as ConfigTypeA instance.
    """
    # Arrange
    union_type = Union[ConfigTypeA, ConfigTypeB, dict[str, Any]]
    data = {"type": "a", "valueA": "test_value"}

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert isinstance(result, ConfigTypeA)
    assert result.type_ == "a"
    assert result.value_a == "test_value"


def test_structure_union__dataclass_variant_b__structures_correctly():
    """
    Test structuring Union type where data matches second dataclass variant.

    Scenario:
        API response contains data that matches ConfigTypeB structure.

    Expected Outcome:
        Data is correctly structured as ConfigTypeB instance.
    """
    # Arrange
    union_type = Union[ConfigTypeA, ConfigTypeB, dict[str, Any]]
    data = {"type": "b", "valueB": 42}

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert isinstance(result, ConfigTypeB)
    assert result.type_ == "b"
    assert result.value_b == 42


# =============================================================================
# Test: Union with dict[str, Any] fallback
# =============================================================================


def test_structure_union__unknown_schema__falls_back_to_dict():
    """
    Test that unknown schemas fall back to dict[str, Any] when present in Union.

    Scenario:
        API returns a schema variant not known to the generated client.
        The Union includes dict[str, Any] as a fallback type.

    Expected Outcome:
        Data is returned as-is (raw dict) without structuring errors.
    """
    # Arrange
    union_type = Union[ConfigTypeA, ConfigTypeB, dict[str, Any]]
    data = {"unknownField": "unknown_value", "anotherField": 123}

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert isinstance(result, dict)
    assert result == {"unknownField": "unknown_value", "anotherField": 123}


def test_structure_union__no_dict_fallback__raises_error():
    """
    Test that structuring fails with clear error when no variant matches and no dict fallback.

    Scenario:
        Union contains only specific dataclass variants without dict[str, Any] fallback.
        Data doesn't match any variant.

    Expected Outcome:
        ValueError is raised with helpful error message.
    """
    # Arrange
    union_type = Union[ConfigTypeA, ConfigTypeB]
    data = {"unknownField": "unknown_value"}

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        converter.structure(data, union_type)

    assert "Could not structure dict into any variant" in str(exc_info.value)


# =============================================================================
# Test: Optional Union (Union[..., None])
# =============================================================================


def test_structure_union__none_value_with_optional__returns_none():
    """
    Test that None is handled correctly for optional unions.

    Scenario:
        Union includes NoneType (Optional pattern).
        Data is None.

    Expected Outcome:
        None is returned without errors.
    """
    # Arrange
    union_type = Union[ConfigTypeA, ConfigTypeB, None]
    data = None

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert result is None


def test_structure_union__none_value_without_optional__raises_error():
    """
    Test that None raises error when NoneType not in Union.

    Scenario:
        Union doesn't include NoneType.
        Data is None.

    Expected Outcome:
        TypeError is raised indicating None is not valid.
    """
    # Arrange
    union_type = Union[ConfigTypeA, ConfigTypeB]
    data = None

    # Act & Assert
    with pytest.raises(TypeError) as exc_info:
        converter.structure(data, union_type)

    assert "None is not valid" in str(exc_info.value)


# =============================================================================
# Test: Union with primitive types
# =============================================================================


def test_structure_union__primitive_string__structures_correctly():
    """
    Test Union types containing primitive string type.

    Scenario:
        Union includes str as one of the variants.
        Data is a string.

    Expected Outcome:
        String is returned as-is.
    """
    # Arrange
    union_type = Union[ConfigTypeA, str, None]
    data = "simple_string_value"

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert isinstance(result, str)
    assert result == "simple_string_value"


def test_structure_union__primitive_int__structures_correctly():
    """
    Test Union types containing primitive int type.

    Scenario:
        Union includes int as one of the variants.
        Data is an integer.

    Expected Outcome:
        Integer is returned as-is.
    """
    # Arrange
    union_type = Union[ConfigTypeA, int, None]
    data = 42

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert isinstance(result, int)
    assert result == 42


# =============================================================================
# Test: Nested dataclass with Union field
# =============================================================================


def test_structure_from_dict__nested_dataclass_with_union_field__structures_correctly():
    """
    Test structuring a dataclass containing a Union-typed field.

    Scenario:
        A dataclass has a field typed as Union[ConfigA, ConfigB, dict, None].
        The JSON data contains a config matching ConfigTypeA.

    Expected Outcome:
        Both the wrapper and nested Union field are structured correctly.
    """
    # Arrange
    data = {"id": 1, "config": {"type": "a", "valueA": "nested_value"}}

    # Act
    result = structure_from_dict(data, WrapperWithUnion)

    # Assert
    assert isinstance(result, WrapperWithUnion)
    assert result.id_ == 1
    assert isinstance(result.config, ConfigTypeA)
    assert result.config.type_ == "a"
    assert result.config.value_a == "nested_value"


def test_structure_from_dict__nested_union_with_none__structures_correctly():
    """
    Test structuring a dataclass with Union field that is None.

    Scenario:
        A dataclass has a field typed as Union[ConfigA, ConfigB, dict, None].
        The JSON data contains null for the config field.

    Expected Outcome:
        Wrapper is structured correctly with config as None.
    """
    # Arrange
    data = {"id": 2, "config": None}

    # Act
    result = structure_from_dict(data, WrapperWithUnion)

    # Assert
    assert isinstance(result, WrapperWithUnion)
    assert result.id_ == 2
    assert result.config is None


def test_structure_from_dict__nested_union_with_dict_fallback__structures_correctly():
    """
    Test structuring a dataclass with Union field falling back to dict.

    Scenario:
        A dataclass has a field typed as Union[ConfigA, ConfigB, dict, None].
        The JSON data contains an unknown schema variant.

    Expected Outcome:
        Wrapper is structured with config as raw dict.
    """
    # Arrange
    data = {"id": 3, "config": {"unknownType": "someValue", "extraField": 123}}

    # Act
    result = structure_from_dict(data, WrapperWithUnion)

    # Assert
    assert isinstance(result, WrapperWithUnion)
    assert result.id_ == 3
    assert isinstance(result.config, dict)
    assert result.config == {"unknownType": "someValue", "extraField": 123}


# =============================================================================
# Test: Error messages
# =============================================================================


def test_structure_union__invalid_type__raises_clear_error():
    """
    Test that structuring incompatible type raises clear error.

    Scenario:
        Data is a list, but Union expects dict-based types.

    Expected Outcome:
        TypeError is raised with informative message.
    """
    # Arrange
    union_type = Union[ConfigTypeA, ConfigTypeB]
    data = ["not", "a", "dict"]

    # Act & Assert
    with pytest.raises(TypeError) as exc_info:
        converter.structure(data, union_type)

    assert "Cannot structure list into" in str(exc_info.value)


def test_structure_union__error_includes_variant_details():
    """
    Test that error message includes details about which variants were tried.

    Scenario:
        Data is a dict that doesn't match any dataclass variant.
        No dict[str, Any] fallback is present.

    Expected Outcome:
        Error message includes information about each variant that was attempted.
    """
    # Arrange
    union_type = Union[ConfigTypeA, ConfigTypeB, ConfigTypeC]
    data = {"completelyWrong": "data"}

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        converter.structure(data, union_type)

    error_msg = str(exc_info.value)
    assert "ConfigTypeA" in error_msg
    assert "ConfigTypeB" in error_msg
    assert "ConfigTypeC" in error_msg


# =============================================================================
# Test: Python 3.10+ pipe syntax (X | Y)
# =============================================================================


def test_structure_union__pipe_syntax__structures_correctly():
    """
    Test Union types using Python 3.10+ pipe syntax (X | Y).

    Scenario:
        Union is defined using the modern pipe syntax.

    Expected Outcome:
        Data is structured correctly just like typing.Union.
    """
    # Arrange
    union_type = ConfigTypeA | ConfigTypeB | None
    data = {"type": "a", "valueA": "pipe_syntax_value"}

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert isinstance(result, ConfigTypeA)
    assert result.value_a == "pipe_syntax_value"


def test_structure_union__pipe_syntax_with_none__handles_correctly():
    """
    Test pipe syntax Union with None value.

    Scenario:
        Union uses pipe syntax and includes None.
        Data is None.

    Expected Outcome:
        None is returned correctly.
    """
    # Arrange
    union_type = ConfigTypeA | ConfigTypeB | None
    data = None

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert result is None


# =============================================================================
# Test: Multiple dataclass variants - first match wins
# =============================================================================


def test_structure_union__multiple_matching_variants__first_wins():
    """
    Test that first matching variant is used when multiple could match.

    Scenario:
        Data could potentially match multiple variants (both have type_ field).
        ConfigTypeA is listed first in the Union.

    Expected Outcome:
        First variant (ConfigTypeA) is used for structuring.
    """
    # Arrange - data has type_ which exists in both, but valueA is specific to ConfigTypeA
    union_type = Union[ConfigTypeA, ConfigTypeB, dict[str, Any]]
    data = {"type": "shared", "valueA": "specific_to_a"}

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert isinstance(result, ConfigTypeA)
    assert result.type_ == "shared"
    assert result.value_a == "specific_to_a"


# =============================================================================
# Test: Additional edge cases
# =============================================================================


def test_structure_union__list_of_dataclass__structures_correctly():
    """
    Test Union containing List[Dataclass] type.

    Scenario:
        Union includes List[ConfigTypeA] as a variant.
        Data is a list of dicts matching ConfigTypeA.

    Expected Outcome:
        List is structured with each item as ConfigTypeA.
    """
    # Arrange
    union_type = Union[list[ConfigTypeA], ConfigTypeB, None]
    data = [
        {"type": "a1", "valueA": "first"},
        {"type": "a2", "valueA": "second"},
    ]

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(item, ConfigTypeA) for item in result)
    assert result[0].value_a == "first"
    assert result[1].value_a == "second"


def test_structure_union__optional_single_dataclass__structures_correctly():
    """
    Test Optional[Dataclass] pattern (Union[Dataclass, None]).

    Scenario:
        Very common pattern where a field is optional.
        Data contains a valid dataclass dict.

    Expected Outcome:
        Data is structured as the dataclass type.
    """
    # Arrange
    from typing import Optional

    union_type = Optional[ConfigTypeA]  # Equivalent to Union[ConfigTypeA, None]
    data = {"type": "optional", "valueA": "present"}

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert isinstance(result, ConfigTypeA)
    assert result.type_ == "optional"
    assert result.value_a == "present"


def test_structure_union__empty_dict_with_fallback__returns_empty_dict():
    """
    Test that empty dict falls back to dict[str, Any] when available.

    Scenario:
        Union includes dict[str, Any] fallback.
        Data is an empty dict which won't match any dataclass.

    Expected Outcome:
        Empty dict is returned as-is via fallback.
    """
    # Arrange
    union_type = Union[ConfigTypeA, ConfigTypeB, dict[str, Any]]
    data = {}

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert isinstance(result, dict)
    assert result == {}


def test_structure_union__datetime_in_union__structures_correctly():
    """
    Test Union containing datetime type.

    Scenario:
        Union includes datetime as a variant.
        Data is an ISO 8601 datetime string.

    Expected Outcome:
        String is structured into datetime object.
    """
    # Arrange
    from datetime import datetime

    union_type = Union[datetime, str, None]
    data = "2025-01-15T10:30:00Z"

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert isinstance(result, datetime)
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 15


def test_structure_union__bool_value__structures_as_bool():
    """
    Test that bool values are handled correctly despite bool being int subclass.

    Scenario:
        Union includes both bool and int types.
        Data is a boolean value.

    Expected Outcome:
        Boolean is preserved as bool, not converted to int.
    """
    # Arrange
    union_type = Union[bool, int, str]
    data = True

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert isinstance(result, bool)
    assert result is True


def test_structure_union__float_value__structures_correctly():
    """
    Test Union with float type.

    Scenario:
        Union includes float as a variant.
        Data is a float value.

    Expected Outcome:
        Float is returned correctly.
    """
    # Arrange
    union_type = Union[ConfigTypeA, float, None]
    data = 3.14159

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert isinstance(result, float)
    assert result == 3.14159


def test_structure_union__bytes_base64__structures_correctly():
    """
    Test Union containing bytes type with base64 encoded data.

    Scenario:
        Union includes bytes as a variant.
        Data is a base64 encoded string.

    Expected Outcome:
        String is decoded to bytes.
    """
    # Arrange
    import base64

    union_type = Union[bytes, str, None]
    original_bytes = b"hello world"
    data = base64.b64encode(original_bytes).decode("utf-8")

    # Act
    result = converter.structure(data, union_type)

    # Assert
    assert isinstance(result, bytes)
    assert result == original_bytes


def test_structure_union__mixed_complex_types__structures_correctly():
    """
    Test Union with mix of complex types.

    Scenario:
        Union includes List[dataclass], single dataclass, primitive, and None.
        This represents a realistic OpenAPI anyOf scenario.

    Expected Outcome:
        Each variant type is handled correctly.
    """
    # Arrange
    union_type = Union[list[ConfigTypeA], ConfigTypeB, str, None]

    # Test with list
    list_data = [{"type": "item", "valueA": "list_value"}]
    list_result = converter.structure(list_data, union_type)
    assert isinstance(list_result, list)
    assert isinstance(list_result[0], ConfigTypeA)

    # Test with single dataclass
    single_data = {"type": "single", "valueB": 99}
    single_result = converter.structure(single_data, union_type)
    assert isinstance(single_result, ConfigTypeB)
    assert single_result.value_b == 99

    # Test with string
    str_data = "plain string"
    str_result = converter.structure(str_data, union_type)
    assert str_result == "plain string"

    # Test with None
    none_result = converter.structure(None, union_type)
    assert none_result is None


# =============================================================================
# Test: Improved error messages with data preview
# =============================================================================


def test_structure_union__error_includes_data_preview():
    """
    Test that error message includes a preview of the failing data.

    Scenario:
        Data is a dict that doesn't match any dataclass variant.
        No dict[str, Any] fallback is present.

    Expected Outcome:
        Error message includes a preview of the data that failed to structure.
    """
    # Arrange
    union_type = Union[ConfigTypeA, ConfigTypeB]
    data = {"unknownField": "some_value", "anotherField": 123}

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        converter.structure(data, union_type)

    error_msg = str(exc_info.value)
    assert "Data:" in error_msg
    assert "unknownField" in error_msg
    assert "some_value" in error_msg


def test_structure_union__large_data__error_truncates_preview():
    """
    Test that large data payloads are truncated in error messages.

    Scenario:
        Data contains a very large string value.
        Union structuring fails.

    Expected Outcome:
        Error message truncates the data preview to a reasonable length.
    """
    # Arrange
    union_type = Union[ConfigTypeA, ConfigTypeB]
    large_value = "x" * 500  # Very long string
    data = {"field": large_value}

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        converter.structure(data, union_type)

    error_msg = str(exc_info.value)
    assert "Data:" in error_msg
    # Data preview should be truncated (max 200 chars by default)
    assert "..." in error_msg
    # The full 500-char string should not appear
    assert large_value not in error_msg


def test_structure_union__non_dict_variant_errors__accumulated():
    """
    Test that non-dict variant failures are included in error message.

    Scenario:
        Union contains only primitive/non-dataclass types.
        Data doesn't match any variant.

    Expected Outcome:
        Error includes details about which variants were tried.
    """
    # Arrange
    from datetime import datetime

    union_type = Union[datetime, int]  # No str variant
    data = "not_a_datetime_or_int"

    # Act & Assert
    with pytest.raises(TypeError) as exc_info:
        converter.structure(data, union_type)

    error_msg = str(exc_info.value)
    assert "Data:" in error_msg
    assert "not_a_datetime_or_int" in error_msg
    # Should mention what variants were tried
    assert "Tried variants:" in error_msg or "Expected one of:" in error_msg


# =============================================================================
# Regression tests: nested Annotated discriminator metadata preservation
#
# Bug: get_type_hints(cls) without include_extras=True strips Annotated[...]
# metadata when resolving dataclass field types. This caused discriminated
# unions inside List[...] fields to lose the discriminator and fall back to
# sequential variant matching, producing the wrong variant.
# =============================================================================


@dataclass(frozen=True)
class NodeDiscriminator:
    """Mimics the discriminator metadata class that the generator emits.

    property_name is the raw JSON key (before snake_case transformation),
    which is what the discriminator lookup receives.
    """

    property_name: str = "type"

    def get_mapping(self) -> dict[str, type]:
        return {
            "start": StartNode,
            "end": EndNode,
            "variable": VariableNode,
        }


@dataclass
class StartNode:
    type_: str
    label: str

    class Meta:
        key_transform_with_load = {"type": "type_", "label": "label"}
        key_transform_with_dump = {"type_": "type", "label": "label"}


@dataclass
class EndNode:
    """Intentionally minimal shape: only label and an optional field.

    This mirrors the WorkflowEndNode in the issue report. Its small required
    surface means it can accidentally absorb payloads from other variants when
    sequential fallback is used (extra keys are silently ignored).
    """

    type_: str
    label: str
    output: str | None = None

    class Meta:
        key_transform_with_load = {"type": "type_", "label": "label", "output": "output"}
        key_transform_with_dump = {"type_": "type", "label": "label", "output": "output"}


@dataclass
class VariableNode:
    """Has label (same as EndNode) plus assignments (unique to this variant)."""

    type_: str
    label: str
    assignments: list[str]

    class Meta:
        key_transform_with_load = {
            "type": "type_",
            "label": "label",
            "assignments": "assignments",
        }
        key_transform_with_dump = {
            "type_": "type",
            "label": "label",
            "assignments": "assignments",
        }


# The discriminated union alias — mirrors what the generator emits:
# NodeUnion: TypeAlias = Annotated[Union[StartNode, EndNode, VariableNode], NodeDiscriminator()]
NodeUnion = Annotated[Union[StartNode, EndNode, VariableNode], NodeDiscriminator()]


@dataclass
class NodeGraph:
    """Container that holds a list of the discriminated union — the nested case."""

    nodes: list[NodeUnion]  # type: ignore[valid-type]

    class Meta:
        key_transform_with_load = {"nodes": "nodes"}
        key_transform_with_dump = {"nodes": "nodes"}


def test_structure_annotated_union__direct__uses_discriminator():
    """
    Structuring a discriminated Annotated union directly must use the
    discriminator key for O(1) variant lookup.

    Scenario:
        structure_from_dict is called directly with NodeUnion as the target type.

    Expected Outcome:
        Each payload is structured into exactly the correct variant, not the
        first sequentially matching one.
    """
    # Arrange
    variable_payload = {"type": "variable", "label": "Set x", "assignments": ["x=1"]}

    # Act
    result = structure_from_dict(variable_payload, NodeUnion)  # type: ignore[arg-type]

    # Assert
    assert isinstance(result, VariableNode), (
        f"Expected VariableNode but got {type(result).__name__}. "
        "Sequential fallback would pick EndNode because its shape is minimal."
    )
    assert result.assignments == ["x=1"]


def test_structure_annotated_union__nested_in_list_field__preserves_discriminator():
    """
    Structuring a dataclass whose field is List[Annotated[Union, Discriminator]]
    must preserve the Annotated metadata so the discriminator is still active.

    This is the primary regression for the bug described in the issue: the
    generated converter called get_type_hints(cls) without include_extras=True,
    stripping the Annotated wrapper and losing the discriminator for nested
    fields. As a result, sequential fallback was used and EndNode was selected
    for VariableNode payloads because EndNode has a minimal required shape.

    Scenario:
        A NodeGraph containing start, variable, and end nodes is structured.

    Expected Outcome:
        Every node in graph.nodes is the correct type, not the first-match
        sequential fallback type.
    """
    # Arrange
    graph_data = {
        "nodes": [
            {"type": "start", "label": "Begin"},
            {"type": "variable", "label": "Set Result", "assignments": ["x=1", "y=2"]},
            {"type": "end", "label": "Done"},
        ]
    }

    # Act
    graph = structure_from_dict(graph_data, NodeGraph)

    # Assert
    node_types = [type(n).__name__ for n in graph.nodes]
    assert node_types == ["StartNode", "VariableNode", "EndNode"], (
        f"Expected ['StartNode', 'VariableNode', 'EndNode'] but got {node_types}. "
        "This indicates the Annotated discriminator was lost during nested structuring "
        "(get_type_hints without include_extras=True stripped the metadata)."
    )
    assert isinstance(graph.nodes[1], VariableNode)
    assert graph.nodes[1].assignments == ["x=1", "y=2"]


def test_structure_annotated_union__nested_list__all_variants_correct():
    """
    Extend the nested list test to all four supported discriminator values.

    Scenario:
        A NodeGraph with one of every node type is structured.

    Expected Outcome:
        Each node resolves to the exact correct variant.
    """
    # Arrange
    graph_data = {
        "nodes": [
            {"type": "start", "label": "S"},
            {"type": "end", "label": "E"},
            {"type": "variable", "label": "V", "assignments": []},
            {"type": "end", "label": "E2"},
            {"type": "start", "label": "S2"},
        ]
    }

    # Act
    graph = structure_from_dict(graph_data, NodeGraph)

    # Assert
    expected = ["StartNode", "EndNode", "VariableNode", "EndNode", "StartNode"]
    actual = [type(n).__name__ for n in graph.nodes]
    assert actual == expected, f"Got {actual}, expected {expected}"


def test_structure_annotated_union__wrong_discriminator_value__raises_clear_error():
    """
    An unknown discriminator value inside a nested list should raise a clear error.

    Scenario:
        A node payload has a type value not in the discriminator mapping.

    Expected Outcome:
        ValueError is raised mentioning the unknown discriminator value.
    """
    # Arrange
    graph_data = {
        "nodes": [
            {"type": "unknown_type", "label": "X"},
        ]
    }

    # Act & Assert
    with pytest.raises((ValueError, Exception)) as exc_info:
        structure_from_dict(graph_data, NodeGraph)

    assert "unknown_type" in str(exc_info.value) or "discriminator" in str(exc_info.value).lower()


# =============================================================================
# Regression: from __future__ import annotations makes annotations lazy strings
#
# Generated model files always have `from __future__ import annotations`. This
# makes every type annotation a lazy string instead of a live type object.
# cattrs' adapted_fields() resolves strings via get_type_hints() WITHOUT
# include_extras=True, stripping Annotated[...] and losing discriminator
# metadata BEFORE the structure function runs.
#
# The fix: _make_dataclass_structure_fn must own get_type_hints(include_extras=True)
# and call converter.structure(val, field_type) with the preserved type.
# =============================================================================


def _build_lazy_annotation_types() -> tuple[type, type, type, type]:
    """
    Build test types that simulate `from __future__ import annotations`.

    Returns (AlphaItem, BetaItem, ItemDiscriminator, ItemCollection).

    The module must be in sys.modules BEFORE exec so that Python's dataclass
    machinery can resolve the module reference when checking for InitVar/ClassVar
    string annotations during class creation.
    """
    import sys
    import textwrap
    import types

    module_src = textwrap.dedent(
        """
        from __future__ import annotations
        from dataclasses import dataclass
        from typing import Annotated, Union

        @dataclass(frozen=True)
        class ItemDiscriminator:
            property_name: str = "kind"
            def get_mapping(self) -> dict:
                return {"alpha": AlphaItem, "beta": BetaItem}

        @dataclass
        class BetaItem:
            kind: str
            note: str | None = None
            class Meta:
                key_transform_with_load = {"kind": "kind", "note": "note"}
                key_transform_with_dump = {"kind": "kind", "note": "note"}

        @dataclass
        class AlphaItem:
            kind: str
            value: int
            class Meta:
                key_transform_with_load = {"kind": "kind", "value": "value"}
                key_transform_with_dump = {"kind": "kind", "value": "value"}

        Item = Annotated[Union[AlphaItem, BetaItem], ItemDiscriminator()]

        @dataclass
        class ItemCollection:
            items: list[Item]
            class Meta:
                key_transform_with_load = {"items": "items"}
                key_transform_with_dump = {"items": "items"}
    """
    )

    mod = types.ModuleType("_test_lazy_annotations")
    # Register BEFORE exec so Python's dataclass machinery can find the module
    # when it inspects string annotations for InitVar/ClassVar detection.
    sys.modules["_test_lazy_annotations"] = mod
    exec(compile(module_src, "_test_lazy_annotations", "exec"), mod.__dict__)

    return (
        mod.AlphaItem,
        mod.BetaItem,
        mod.ItemDiscriminator,
        mod.ItemCollection,
    )


def test_structure_annotated_union__string_annotations_module__discriminator_preserved():
    """
    Structuring a dataclass defined in a module that uses
    `from __future__ import annotations` must preserve discriminator metadata.

    This is the critical reproduction of the real-world bug: generated model
    files always have lazy string annotations. Before the fix, cattrs resolved
    those strings without include_extras=True, stripping the Annotated wrapper
    from fields like `nodes: list[WorkflowNode]`, losing the discriminator.

    Scenario:
        Types are defined in a module with PEP 563 (string) annotations.
        The field `items: list[Item]` is stored as the string "list[Item]".
        After get_type_hints resolves it, it must still be
        `list[Annotated[Union[AlphaItem, BetaItem], ItemDiscriminator()]]`.

    Expected Outcome:
        Every item resolves to the correct variant via the discriminator,
        not the first sequentially matching variant (BetaItem absorbs everything
        when the discriminator is lost because its shape is minimal).
    """
    import sys

    # Arrange
    AlphaItem, BetaItem, ItemDiscriminator, ItemCollection = _build_lazy_annotation_types()

    data = {
        "items": [
            {"kind": "alpha", "value": 10},
            {"kind": "beta", "note": "only note"},
            {"kind": "alpha", "value": 20},
        ]
    }

    # Act
    result = structure_from_dict(data, ItemCollection)

    # Assert — without the fix, BetaItem absorbs AlphaItem payloads because
    # BetaItem's shape (only "kind" required) structurally matches anything
    # with "kind". The discriminator must route correctly.
    item_types = [type(i).__name__ for i in result.items]
    assert item_types == ["AlphaItem", "BetaItem", "AlphaItem"], (
        f"Expected ['AlphaItem', 'BetaItem', 'AlphaItem'] but got {item_types}. "
        "The discriminator was lost during structuring, likely because "
        "get_type_hints was called without include_extras=True on a module "
        "that uses `from __future__ import annotations`."
    )
    assert result.items[0].value == 10  # type: ignore[attr-defined]
    assert result.items[2].value == 20  # type: ignore[attr-defined]

    # Clean up
    if "_test_lazy_annotations" in sys.modules:
        del sys.modules["_test_lazy_annotations"]
