from dataclasses import dataclass
from typing import List

import pytest

from pyopenapi_gen.core.cattrs_converter import structure_from_dict


@dataclass
class Nested:
    id: int
    name: str


@dataclass
class Root:
    items: List[Nested]
    count: int


@dataclass
class DeepL3:
    value: int


@dataclass
class DeepL2:
    l3: DeepL3


@dataclass
class DeepL1:
    l2: DeepL2


def test_structure_from_dict__invalid_data__raises_informative_error():
    """
    Test that structuring invalid data raises a ValueError with informative messages.

    Scenario:
        Input data has multiple type errors (invalid int, invalid nested int).

    Expected Outcome:
        ValueError is raised containing a list of specific errors with paths.
    """
    data = {
        "items": [
            {"id": 1, "name": "one"},
            {"id": "invalid", "name": "two"},  # Invalid id type
        ],
        "count": "not_an_int",  # Invalid count type
    }

    with pytest.raises(ValueError) as excinfo:
        structure_from_dict(data, Root)

    error_msg = str(excinfo.value)

    # Verify the main error message
    assert "Failed to convert data to Root" in error_msg

    # Verify specific errors are present
    # Note: We use [] for list items as cattrs doesn't provide reliable indices
    # But we now correctly extract the field name from the nested object!
    assert "- items[].id: invalid literal for int() with base 10: 'invalid'" in error_msg
    assert "- count: invalid literal for int() with base 10: 'not_an_int'" in error_msg


def test_structure_from_dict__missing_field__raises_informative_error():
    """
    Test that missing required fields raise informative errors.

    Scenario:
        Input data is missing a required field.

    Expected Outcome:
        ValueError is raised indicating the missing field.
    """
    data = {"name": "missing_id"}  # Missing 'id'

    with pytest.raises(ValueError) as excinfo:
        structure_from_dict(data, Nested)

    error_msg = str(excinfo.value)
    assert "Failed to convert data to Nested" in error_msg
    # cattrs usually reports missing fields clearly
    assert "missing" in error_msg.lower() or "required" in error_msg.lower() or "id" in error_msg


def test_structure_from_dict__deeply_nested_error__raises_informative_error():
    """
    Test that errors in deeply nested objects have correct paths.

    Scenario:
        Input data has an error 3 levels deep (l2.l3.value).

    Expected Outcome:
        ValueError is raised with path 'l2.l3.value'.
    """
    data = {"l2": {"l3": {"value": "not_an_int"}}}

    with pytest.raises(ValueError) as excinfo:
        structure_from_dict(data, DeepL1)

    error_msg = str(excinfo.value)
    assert "Failed to convert data to DeepL1" in error_msg
    # Verify path construction
    assert "l2.l3.value" in error_msg
    assert "invalid literal for int()" in error_msg


def test_structure_from_dict__simple_type_mismatch__raises_informative_error():
    """
    Test that passing wrong type for the root object raises informative error.

    Scenario:
        Expected a dict (for dataclass) but got a string.

    Expected Outcome:
        ValueError is raised indicating type mismatch.
    """
    data = "not_a_dict"

    with pytest.raises(ValueError) as excinfo:
        structure_from_dict(data, Nested)

    error_msg = str(excinfo.value)
    assert "Failed to convert data to Nested" in error_msg
    # Should mention something about expected type or attribute access failure
    # cattrs might raise TypeError or AttributeError depending on implementation details
    # but our wrapper should catch it.
    assert "AttributeError" in error_msg or "TypeError" in error_msg or "str" in error_msg
