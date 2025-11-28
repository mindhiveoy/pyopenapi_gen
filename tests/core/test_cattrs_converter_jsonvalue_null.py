"""
Tests for cattrs converter handling of None/null values with JsonValue and other dataclass fields.

Reproduces the bug where cattrs generated structure functions fail when encountering None values
for non-optional fields typed as dataclasses.
"""

from dataclasses import dataclass, field
from typing import Any

import pytest

from pyopenapi_gen.core.cattrs_converter import converter, structure_from_dict


@dataclass
class JsonValue:
    """Generic JSON value object that wraps arbitrary JSON data."""

    _data: dict[str, Any] = field(default_factory=dict, repr=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the JSON data."""
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Get a value from the JSON data using bracket notation."""
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a value in the JSON data using bracket notation."""
        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the JSON data."""
        return key in self._data

    def keys(self) -> Any:
        """Get all keys from the JSON data."""
        return self._data.keys()

    def values(self) -> Any:
        """Get all values from the JSON data."""
        return self._data.values()

    def items(self) -> Any:
        """Get all items from the JSON data."""
        return self._data.items()


# Register structure hook for JsonValue that handles dict directly
def _structure_jsonvalue(data: dict[str, Any] | None, _: type[JsonValue]) -> JsonValue:
    """
    Structure hook for JsonValue that handles dict data directly.

    The API sends JSON objects directly like {"key": "value"}, not {"Data": {"key": "value"}}.
    If data is None, raise a clear error about the schema mismatch.
    """
    if data is None:
        # None received for JsonValue means the API returned null for a non-optional field.
        # This is a schema violation that needs to be fixed in the OpenAPI spec.
        raise TypeError(
            "Cannot structure None into JsonValue: "
            "Received null value for non-optional field. "
            "This is likely a schema mismatch - either the API is returning null "
            "for a required field, or the OpenAPI schema is missing 'nullable: true'. "
            "To fix: make the field optional in the OpenAPI spec by adding 'nullable: true' "
            "or removing it from the 'required' array."
        )
    return JsonValue(_data=data)


converter.register_structure_hook(JsonValue, _structure_jsonvalue)


@dataclass
class DataSourceItem:
    """
    Test model that simulates AgentSchemaOutputDataSourcesItem from the bug report.

    Scenario:
        A model with a JsonValue field that receives null from the API even though
        it's not typed as Optional[JsonValue].
    """

    agent_id: str
    data_source_id: str
    id_: str
    config_: JsonValue  # This field can be null in API responses despite not being Optional

    class Meta:
        """Configure field name mapping for JSON conversion."""

        key_transform_with_load = {
            "agentId": "agent_id",
            "config": "config_",
            "dataSourceId": "data_source_id",
            "id": "id_",
        }


def test_structure_from_dict__jsonvalue_field_with_none__raises_schema_mismatch_error():
    """
    Scenario:
        API returns null for a non-optional JsonValue field. This is a schema violation
        where the OpenAPI spec marks the field as required but the API returns null.

    Expected Outcome:
        Should raise a clear ValueError explaining the schema mismatch and suggesting
        how to fix it (add 'nullable: true' to the OpenAPI schema).
    """
    # Arrange - API response with null config (schema violation)
    data = {
        "agentId": "test-agent",
        "config": None,  # ⚠️ Schema says required, but API returns null
        "dataSourceId": "test-ds",
        "id": "test-id",
    }

    # Act & Assert
    with pytest.raises(
        ValueError,
        match="Cannot structure None into JsonValue.*schema mismatch.*nullable: true",
    ):
        result = structure_from_dict(data, DataSourceItem)


def test_structure_from_dict__jsonvalue_field_with_empty_dict__works_correctly():
    """
    Scenario:
        API returns an empty object {} for a JsonValue field.

    Expected Outcome:
        Should structure successfully with an empty JsonValue.
    """
    # Arrange - API response with empty object
    data = {
        "agentId": "test-agent",
        "config": {},
        "dataSourceId": "test-ds",
        "id": "test-id",
    }

    # Act
    result = structure_from_dict(data, DataSourceItem)

    # Assert
    assert result.agent_id == "test-agent"
    assert result.config_ is not None
    assert isinstance(result.config_, JsonValue)
    assert len(result.config_._data) == 0


def test_structure_from_dict__jsonvalue_field_with_data__works_correctly():
    """
    Scenario:
        API returns actual JSON data for a JsonValue field.

    Expected Outcome:
        Should structure successfully with the data properly wrapped in JsonValue.
    """
    # Arrange - API response with actual config data
    data = {
        "agentId": "test-agent",
        "config": {"apiKey": "secret", "timeout": 30},
        "dataSourceId": "test-ds",
        "id": "test-id",
    }

    # Act
    result = structure_from_dict(data, DataSourceItem)

    # Assert
    assert result.agent_id == "test-agent"
    assert result.config_ is not None
    assert isinstance(result.config_, JsonValue)
    assert result.config_.get("apiKey") == "secret"
    assert result.config_.get("timeout") == 30


@dataclass
class OptionalDataSourceItem:
    """
    Alternative model where config is properly typed as optional.

    Scenario:
        When JsonValue fields are properly typed as Optional, null handling
        should work automatically.
    """

    agent_id: str
    data_source_id: str
    id_: str
    config_: JsonValue | None = None  # Properly typed as optional

    class Meta:
        """Configure field name mapping for JSON conversion."""

        key_transform_with_load = {
            "agentId": "agent_id",
            "config": "config_",
            "dataSourceId": "data_source_id",
            "id": "id_",
        }


def test_structure_from_dict__optional_jsonvalue_with_none__should_work():
    """
    Scenario:
        When JsonValue field is properly typed as Optional[JsonValue],
        null values should be handled automatically by cattrs.

    Expected Outcome:
        Should structure successfully with config_ set to None.
    """
    # Arrange - API response with null config
    data = {
        "agentId": "test-agent",
        "config": None,
        "dataSourceId": "test-ds",
        "id": "test-id",
    }

    # Act
    result = structure_from_dict(data, OptionalDataSourceItem)

    # Assert
    assert result.agent_id == "test-agent"
    assert result.config_ is None  # Should be None, not crash


def test_structure_from_dict__optional_jsonvalue_with_data__should_work():
    """
    Scenario:
        When JsonValue field is optional but has data, it should structure normally.

    Expected Outcome:
        Should structure successfully with config_ as JsonValue instance.
    """
    # Arrange - API response with config data
    data = {
        "agentId": "test-agent",
        "config": {"key": "value"},
        "dataSourceId": "test-ds",
        "id": "test-id",
    }

    # Act
    result = structure_from_dict(data, OptionalDataSourceItem)

    # Assert
    assert result.agent_id == "test-agent"
    assert result.config_ is not None
    assert isinstance(result.config_, JsonValue)
    assert result.config_.get("key") == "value"


@dataclass
class RequiredFieldItem:
    """
    Test model with required fields and no defaults.

    Scenario:
        When a dataclass has required fields without defaults, structuring
        None should raise a clear error message.
    """

    name: str  # Required, no default
    value: int  # Required, no default


def test_structure_from_dict__required_field_dataclass_with_none__raises_clear_error():
    """
    Scenario:
        API returns None for a field typed as a dataclass with required fields.
        This is a genuine type mismatch that should be reported clearly.

    Expected Outcome:
        Should raise ValueError (wrapping TypeError) with a clear message about None not being valid
        for non-optional fields, suggesting to make the field optional.
    """
    # Note: This is testing the None-handling in nested contexts,
    # but for simplicity we'll test it directly

    @dataclass
    class Container:
        """Container with a required dataclass field."""

        item: RequiredFieldItem  # Not optional, no default

    # Arrange - Data with None for required field
    data = {"item": None}

    # Act & Assert
    with pytest.raises(ValueError, match="Cannot structure None into RequiredFieldItem"):
        result = structure_from_dict(data, Container)
