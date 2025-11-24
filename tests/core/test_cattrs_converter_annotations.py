from __future__ import annotations

from dataclasses import dataclass
from typing import List

from pyopenapi_gen.core.cattrs_converter import structure_from_dict


@dataclass
class NestedItem:
    item_id: int
    name: str


@dataclass
class RootContainer:
    items: List[NestedItem]
    single_item: NestedItem | None = None


def test_structure_with_future_annotations():
    """
    Test that dataclasses defined in a file with `from __future__ import annotations`
    are correctly structured, including nested dataclasses.

    Scenario:
        When `from __future__ import annotations` is used, type hints become strings.
        The converter must resolve these strings to actual types to register hooks recursively.

    Expected Outcome:
        Nested dataclasses are correctly identified and structured.
    """
    data = {
        "items": [{"itemId": 1, "name": "one"}, {"itemId": 2, "name": "two"}],
        "singleItem": {"itemId": 3, "name": "three"},
    }

    result = structure_from_dict(data, RootContainer)

    assert isinstance(result, RootContainer)
    assert len(result.items) == 2
    assert isinstance(result.items[0], NestedItem)
    assert result.items[0].item_id == 1
    assert result.items[0].name == "one"

    assert isinstance(result.single_item, NestedItem)
    assert result.single_item.item_id == 3
    assert result.single_item.name == "three"


@dataclass
class RecursiveNode:
    value: int
    children: List[RecursiveNode]


@dataclass
class DataSourceItem:
    id_: str
    data_source_id: str

    class Meta:
        key_transform_with_load = {"id": "id_", "dataSourceId": "data_source_id"}


@dataclass
class AgentSchema:
    id_: str
    data_sources: List[DataSourceItem] | None = None

    class Meta:
        key_transform_with_load = {"id": "id_", "dataSources": "data_sources"}


def test_structure_recursive_with_future_annotations():
    """
    Test recursive structure with future annotations.
    """

    data = {
        "value": 1,
        "children": [{"value": 2, "children": []}, {"value": 3, "children": [{"value": 4, "children": []}]}],
    }

    result = structure_from_dict(data, RecursiveNode)

    assert isinstance(result, RecursiveNode)
    assert result.value == 1
    assert len(result.children) == 2
    assert result.children[0].value == 2
    assert result.children[1].value == 3
    assert result.children[1].children[0].value == 4


def test_structure_complex_mapping_with_future_annotations():
    """
    Test complex field mappings (Meta, keywords) with future annotations.

    Scenario:
        Mimics the user's AgentSchemaOutput case where:
        - `from __future__ import annotations` is active
        - Fields have `_` suffix (id_) mapping to keys (id)
        - Meta.key_transform_with_load is used
        - Nested lists are present

    Expected Outcome:
        All fields are mapped correctly using the Meta configuration and
        nested objects are structured correctly.
    """
    data = {
        "id": "agent_123",
        "dataSources": [
            {"id": "ds_item_1", "dataSourceId": "source_1"},
            {"id": "ds_item_2", "dataSourceId": "source_2"},
        ],
    }

    result = structure_from_dict(data, AgentSchema)

    assert isinstance(result, AgentSchema)
    assert result.id_ == "agent_123"
    assert len(result.data_sources) == 2

    assert isinstance(result.data_sources[0], DataSourceItem)
    assert result.data_sources[0].id_ == "ds_item_1"
    assert result.data_sources[0].data_source_id == "source_1"

    assert result.data_sources[1].id_ == "ds_item_2"
    assert result.data_sources[1].data_source_id == "source_2"
