"""
Systematic tests for structure_from_dict with all type permutations.

Tests verify key transforms at EVERY nesting level:
- Top-level container types (list, dict, Optional, Union, TypeAlias)
- Child element key transforms within containers
- Nested dataclass key transforms within list/dict elements
- Deeply nested chains: list → dataclass → list → dataclass
- Roundtrip (structure + unstructure) preserving original JSON keys
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypeAlias, Union

from pyopenapi_gen.core.cattrs_converter import structure_from_dict, unstructure_to_dict

# ===== Test models with multi-level key transforms =====


class PriorityEnum(str, Enum):
    LOW = "low"
    HIGH = "high"


@dataclass
class Tag:
    """Level 3: Leaf-level dataclass with key transforms."""

    tag_name: str
    tag_category: str

    class Meta:
        key_transform_with_load = {"tagName": "tag_name", "tagCategory": "tag_category"}
        key_transform_with_dump = {"tag_name": "tagName", "tag_category": "tagCategory"}


@dataclass
class ConfigItem:
    """Level 2: Mid-level dataclass with nested dataclass list + enum + datetime."""

    tool_name: str
    is_enabled: bool
    priority_level: PriorityEnum
    last_modified: datetime
    tool_tags: List[Tag] = field(default_factory=list)

    class Meta:
        key_transform_with_load = {
            "toolName": "tool_name",
            "isEnabled": "is_enabled",
            "priorityLevel": "priority_level",
            "lastModified": "last_modified",
            "toolTags": "tool_tags",
        }
        key_transform_with_dump = {
            "tool_name": "toolName",
            "is_enabled": "isEnabled",
            "priority_level": "priorityLevel",
            "last_modified": "lastModified",
            "tool_tags": "toolTags",
        }


@dataclass
class AgentRecord:
    """Level 1: Top-level dataclass with nested objects, lists, and Python keyword fields."""

    id_: str
    agent_name: str
    created_at: datetime
    config_items: List[ConfigItem] = field(default_factory=list)
    primary_config: ConfigItem | None = None
    extra_tags: List[str] = field(default_factory=list)

    class Meta:
        key_transform_with_load = {
            "id": "id_",
            "agentName": "agent_name",
            "createdAt": "created_at",
            "configItems": "config_items",
            "primaryConfig": "primary_config",
            "extraTags": "extra_tags",
        }
        key_transform_with_dump = {
            "id_": "id",
            "agent_name": "agentName",
            "created_at": "createdAt",
            "config_items": "configItems",
            "primary_config": "primaryConfig",
            "extra_tags": "extraTags",
        }


@dataclass
class SimpleItem:
    """Simple model for basic list/dict tests."""

    item_name: str
    item_value: int

    class Meta:
        key_transform_with_load = {"itemName": "item_name", "itemValue": "item_value"}
        key_transform_with_dump = {"item_name": "itemName", "item_value": "itemValue"}


@dataclass
class NoTransformModel:
    """Model without Meta (no key transforms)."""

    name: str
    value: int


# ===== TypeAlias definitions (matching generated client patterns) =====

AgentRecordList: TypeAlias = List[AgentRecord]
SimpleItemList: TypeAlias = List[SimpleItem]
FloatVector: TypeAlias = List[float]
EmbeddingMatrix: TypeAlias = List[List[float]]
MixedUnion: TypeAlias = Union[dict[str, Any], str]


# ===== Shared test data factories =====


def _make_tag_json(name: str, category: str) -> dict[str, Any]:
    return {"tagName": name, "tagCategory": category}


def _make_config_json(
    tool: str,
    enabled: bool = True,
    priority: str = "high",
    modified: str = "2025-01-01T00:00:00Z",
    tags: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "toolName": tool,
        "isEnabled": enabled,
        "priorityLevel": priority,
        "lastModified": modified,
        "toolTags": tags or [],
    }


def _make_agent_json(
    id_: str,
    name: str,
    created: str = "2025-06-01T12:00:00Z",
    configs: list[dict[str, Any]] | None = None,
    primary: dict[str, Any] | None = None,
    extra_tags: list[str] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": id_,
        "agentName": name,
        "createdAt": created,
        "configItems": configs or [],
    }
    if primary is not None:
        result["primaryConfig"] = primary
    if extra_tags is not None:
        result["extraTags"] = extra_tags
    return result


# ===========================================================================
# Test Group 1: list[Dataclass] — key transforms in child elements
# ===========================================================================


class TestListDataclass:
    def test_list_builtin__child_key_transforms_applied(self) -> None:
        """Verify camelCase → snake_case in every child element."""
        data = [
            {"itemName": "alpha", "itemValue": 10},
            {"itemName": "beta", "itemValue": 20},
        ]

        result = structure_from_dict(data, list[SimpleItem])

        assert len(result) == 2
        assert isinstance(result[0], SimpleItem)
        assert isinstance(result[1], SimpleItem)
        assert result[0].item_name == "alpha"
        assert result[0].item_value == 10
        assert result[1].item_name == "beta"
        assert result[1].item_value == 20

    def test_typing_list__identical_to_builtin(self) -> None:
        data = [{"itemName": "gamma", "itemValue": 30}]
        result = structure_from_dict(data, List[SimpleItem])
        assert result[0].item_name == "gamma"
        assert result[0].item_value == 30

    def test_typealias_list__identical_to_builtin(self) -> None:
        data = [{"itemName": "delta", "itemValue": 40}]
        result = structure_from_dict(data, SimpleItemList)
        assert result[0].item_name == "delta"
        assert result[0].item_value == 40

    def test_list_empty__returns_empty(self) -> None:
        assert structure_from_dict([], list[SimpleItem]) == []

    def test_list_single_element__transforms_applied(self) -> None:
        result = structure_from_dict([{"itemName": "one", "itemValue": 1}], list[SimpleItem])
        assert len(result) == 1
        assert result[0].item_name == "one"


# ===========================================================================
# Test Group 2: Deep nesting — list → dataclass → list → dataclass
# ===========================================================================


class TestDeepNesting:
    """Verify key transforms at 3+ nesting levels within list elements."""

    def test_list_agent__level1_transforms(self) -> None:
        """Level 1: AgentRecord fields (id, agentName, createdAt)."""
        data = [_make_agent_json("a1", "Agent One")]

        result = structure_from_dict(data, list[AgentRecord])

        agent = result[0]
        assert isinstance(agent, AgentRecord)
        assert agent.id_ == "a1"
        assert agent.agent_name == "Agent One"
        assert isinstance(agent.created_at, datetime)

    def test_list_agent__level2_config_transforms(self) -> None:
        """Level 2: ConfigItem fields nested within AgentRecord.configItems."""
        config = _make_config_json("search", enabled=True, priority="high", modified="2025-03-15T09:00:00Z")
        data = [_make_agent_json("a2", "Agent Two", configs=[config])]

        result = structure_from_dict(data, list[AgentRecord])

        agent = result[0]
        assert len(agent.config_items) == 1
        cfg = agent.config_items[0]
        assert isinstance(cfg, ConfigItem)
        assert cfg.tool_name == "search"
        assert cfg.is_enabled is True
        assert cfg.priority_level == PriorityEnum.HIGH
        assert isinstance(cfg.last_modified, datetime)
        assert cfg.last_modified.year == 2025
        assert cfg.last_modified.month == 3

    def test_list_agent__level3_tag_transforms(self) -> None:
        """Level 3: Tag fields nested within ConfigItem.toolTags within AgentRecord."""
        tags = [_make_tag_json("ml", "category-ai"), _make_tag_json("nlp", "category-ai")]
        config = _make_config_json("embedder", tags=tags)
        data = [_make_agent_json("a3", "Agent Three", configs=[config])]

        result = structure_from_dict(data, list[AgentRecord])

        agent = result[0]
        tag_list = agent.config_items[0].tool_tags
        assert len(tag_list) == 2
        assert isinstance(tag_list[0], Tag)
        assert isinstance(tag_list[1], Tag)
        assert tag_list[0].tag_name == "ml"
        assert tag_list[0].tag_category == "category-ai"
        assert tag_list[1].tag_name == "nlp"

    def test_list_agent__optional_nested_dataclass(self) -> None:
        """Optional nested ConfigItem (primaryConfig) within list element."""
        primary = _make_config_json("primary-tool", priority="low")
        data = [_make_agent_json("a4", "Agent Four", primary=primary)]

        result = structure_from_dict(data, list[AgentRecord])

        agent = result[0]
        assert agent.primary_config is not None
        assert agent.primary_config.tool_name == "primary-tool"
        assert agent.primary_config.priority_level == PriorityEnum.LOW

    def test_list_agent__optional_nested_none(self) -> None:
        """Optional nested ConfigItem is None when not present."""
        data = [_make_agent_json("a5", "Agent Five")]

        result = structure_from_dict(data, list[AgentRecord])

        assert result[0].primary_config is None

    def test_list_agent__multiple_items_all_levels(self) -> None:
        """Multiple list elements, each with full 3-level nesting."""
        data = [
            _make_agent_json(
                "a6",
                "First",
                configs=[
                    _make_config_json("tool-a", tags=[_make_tag_json("t1", "c1")]),
                    _make_config_json(
                        "tool-b", enabled=False, tags=[_make_tag_json("t2", "c2"), _make_tag_json("t3", "c3")]
                    ),
                ],
                extra_tags=["prod"],
            ),
            _make_agent_json(
                "a7",
                "Second",
                created="2025-12-31T23:59:59Z",
                configs=[_make_config_json("tool-c")],
            ),
        ]

        result = structure_from_dict(data, list[AgentRecord])

        # First agent
        first = result[0]
        assert first.id_ == "a6"
        assert first.agent_name == "First"
        assert first.extra_tags == ["prod"]
        assert len(first.config_items) == 2
        assert first.config_items[0].tool_name == "tool-a"
        assert len(first.config_items[0].tool_tags) == 1
        assert first.config_items[0].tool_tags[0].tag_name == "t1"
        assert first.config_items[1].tool_name == "tool-b"
        assert first.config_items[1].is_enabled is False
        assert len(first.config_items[1].tool_tags) == 2
        assert first.config_items[1].tool_tags[1].tag_name == "t3"
        assert first.config_items[1].tool_tags[1].tag_category == "c3"

        # Second agent
        second = result[1]
        assert second.id_ == "a7"
        assert second.agent_name == "Second"
        assert second.created_at.year == 2025
        assert second.created_at.month == 12

    def test_typealias_list_agent__deep_nesting(self) -> None:
        """Same deep nesting via TypeAlias."""
        tags = [_make_tag_json("alias-tag", "alias-cat")]
        config = _make_config_json("alias-tool", tags=tags)
        data = [_make_agent_json("alias-1", "Alias Agent", configs=[config])]

        result = structure_from_dict(data, AgentRecordList)

        agent = result[0]
        assert agent.id_ == "alias-1"
        assert agent.config_items[0].tool_name == "alias-tool"
        assert agent.config_items[0].tool_tags[0].tag_name == "alias-tag"
        assert agent.config_items[0].tool_tags[0].tag_category == "alias-cat"


# ===========================================================================
# Test Group 3: Dict[str, Dataclass] — key transforms in dict values
# ===========================================================================


class TestDictDataclass:
    def test_dict_str_dataclass__child_transforms(self) -> None:
        data = {
            "x": {"itemName": "first", "itemValue": 1},
            "y": {"itemName": "second", "itemValue": 2},
        }

        result = structure_from_dict(data, Dict[str, SimpleItem])

        assert isinstance(result["x"], SimpleItem)
        assert result["x"].item_name == "first"
        assert result["x"].item_value == 1
        assert result["y"].item_name == "second"

    def test_dict_str_nested_dataclass__deep_transforms(self) -> None:
        """Dict values are complex dataclasses with nested lists and transforms."""
        config = _make_config_json("dict-tool", tags=[_make_tag_json("dt", "dc")])
        data = {"agent-x": _make_agent_json("dx", "Dict Agent", configs=[config])}

        result = structure_from_dict(data, Dict[str, AgentRecord])

        agent = result["agent-x"]
        assert agent.id_ == "dx"
        assert agent.agent_name == "Dict Agent"
        assert agent.config_items[0].tool_name == "dict-tool"
        assert agent.config_items[0].tool_tags[0].tag_name == "dt"

    def test_dict_empty__returns_empty(self) -> None:
        assert structure_from_dict({}, Dict[str, SimpleItem]) == {}


# ===========================================================================
# Test Group 4: Optional[Dataclass] — transforms when present
# ===========================================================================


class TestOptionalDataclass:
    def test_optional_with_value__transforms_applied(self) -> None:
        data = {"itemName": "opt", "itemValue": 42}
        result = structure_from_dict(data, Optional[SimpleItem])
        assert result is not None
        assert result.item_name == "opt"
        assert result.item_value == 42

    def test_optional_with_none__returns_none(self) -> None:
        assert structure_from_dict(None, Optional[SimpleItem]) is None

    def test_optional_nested_dataclass__deep_transforms(self) -> None:
        config = _make_config_json("opt-tool", tags=[_make_tag_json("ot", "oc")])
        data = _make_agent_json("opt-1", "Opt Agent", configs=[config])

        result = structure_from_dict(data, Optional[AgentRecord])

        assert result is not None
        assert result.id_ == "opt-1"
        assert result.config_items[0].tool_name == "opt-tool"
        assert result.config_items[0].tool_tags[0].tag_name == "ot"


# ===========================================================================
# Test Group 5: Union and TypeAlias Union
# ===========================================================================


class TestUnionTypes:
    def test_union_dict_or_str__dict(self) -> None:
        result = structure_from_dict({"key": "value"}, MixedUnion)
        assert result == {"key": "value"}

    def test_union_dict_or_str__string(self) -> None:
        result = structure_from_dict("text", MixedUnion)
        assert result == "text"


# ===========================================================================
# Test Group 6: Primitive list types (no dataclass elements)
# ===========================================================================


class TestPrimitiveLists:
    def test_list_float_alias(self) -> None:
        assert structure_from_dict([0.1, 0.2], FloatVector) == [0.1, 0.2]

    def test_list_float_empty(self) -> None:
        assert structure_from_dict([], FloatVector) == []

    def test_nested_list_of_lists(self) -> None:
        data = [[1.0, 2.0], [3.0]]
        result = structure_from_dict(data, EmbeddingMatrix)
        assert result == [[1.0, 2.0], [3.0]]


# ===========================================================================
# Test Group 7: No Meta (no transforms)
# ===========================================================================


class TestNoTransforms:
    def test_list_no_meta__field_names_as_is(self) -> None:
        data = [{"name": "a", "value": 1}, {"name": "b", "value": 2}]
        result = structure_from_dict(data, list[NoTransformModel])
        assert result[0].name == "a"
        assert result[1].value == 2


# ===========================================================================
# Test Group 8: Full roundtrip (structure → unstructure)
# ===========================================================================


class TestRoundtrip:
    def test_simple_list_roundtrip(self) -> None:
        original = [
            {"itemName": "rt-1", "itemValue": 100},
            {"itemName": "rt-2", "itemValue": 200},
        ]
        structured = structure_from_dict(original, list[SimpleItem])
        unstructured = [unstructure_to_dict(item) for item in structured]
        assert unstructured == original

    def test_deep_nested_roundtrip(self) -> None:
        """Roundtrip for 3-level nesting: verify JSON keys restored at all levels."""
        tags_json = [_make_tag_json("rt-tag", "rt-cat")]
        config_json = _make_config_json("rt-tool", priority="low", tags=tags_json)
        agent_json = _make_agent_json("rt-agent", "Roundtrip Agent", configs=[config_json], extra_tags=["test"])

        structured = structure_from_dict(agent_json, AgentRecord)
        unstructured = unstructure_to_dict(structured)

        # Level 1: AgentRecord keys
        assert "id" in unstructured
        assert "agentName" in unstructured
        assert "createdAt" in unstructured
        assert "configItems" in unstructured
        assert "extraTags" in unstructured
        assert unstructured["id"] == "rt-agent"
        assert unstructured["agentName"] == "Roundtrip Agent"
        assert unstructured["extraTags"] == ["test"]

        # Level 2: ConfigItem keys
        cfg = unstructured["configItems"][0]
        assert "toolName" in cfg
        assert "isEnabled" in cfg
        assert "priorityLevel" in cfg
        assert "lastModified" in cfg
        assert "toolTags" in cfg
        assert cfg["toolName"] == "rt-tool"
        assert cfg["priorityLevel"] == "low"

        # Level 3: Tag keys
        tag = cfg["toolTags"][0]
        assert "tagName" in tag
        assert "tagCategory" in tag
        assert tag["tagName"] == "rt-tag"
        assert tag["tagCategory"] == "rt-cat"

    def test_list_of_nested_roundtrip(self) -> None:
        """Roundtrip for list of deeply nested agents."""
        tags_json = [_make_tag_json("lr-tag", "lr-cat")]
        config_json = _make_config_json("lr-tool", tags=tags_json)
        agents_json = [
            _make_agent_json("lr-1", "First", configs=[config_json]),
            _make_agent_json("lr-2", "Second"),
        ]

        structured = structure_from_dict(agents_json, list[AgentRecord])
        unstructured = [unstructure_to_dict(agent) for agent in structured]

        # First agent
        assert unstructured[0]["id"] == "lr-1"
        assert unstructured[0]["agentName"] == "First"
        assert unstructured[0]["configItems"][0]["toolName"] == "lr-tool"
        assert unstructured[0]["configItems"][0]["toolTags"][0]["tagName"] == "lr-tag"

        # Second agent
        assert unstructured[1]["id"] == "lr-2"
        assert unstructured[1]["agentName"] == "Second"
        assert unstructured[1]["configItems"] == []
