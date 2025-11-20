"""
Tests for datetime and date field handling in cattrs converter.

These tests validate that JSON datetime/date strings are correctly structured into
Python datetime/date objects and vice versa.
"""

from dataclasses import dataclass
from datetime import date, datetime

import pytest
from cattrs.errors import ClassValidationError

from pyopenapi_gen.core.cattrs_converter import structure_from_dict, unstructure_to_dict


@dataclass
class EventWithDatetime:
    """Event model with datetime field."""

    event_id: int
    event_name: str
    created_at: datetime
    updated_at: datetime | None = None

    class Meta:
        key_transform_with_load = {
            "eventId": "event_id",
            "eventName": "event_name",
            "createdAt": "created_at",
            "updatedAt": "updated_at",
        }
        key_transform_with_dump = {
            "event_id": "eventId",
            "event_name": "eventName",
            "created_at": "createdAt",
            "updated_at": "updatedAt",
        }


@dataclass
class PersonWithDate:
    """Person model with date field."""

    person_id: int
    name: str
    birth_date: date
    hire_date: date | None = None

    class Meta:
        key_transform_with_load = {
            "personId": "person_id",
            "birthDate": "birth_date",
            "hireDate": "hire_date",
        }
        key_transform_with_dump = {
            "person_id": "personId",
            "birth_date": "birthDate",
            "hire_date": "hireDate",
        }


def test_structure_datetime__iso8601_with_timezone__converts_correctly():
    """
    Test datetime structuring with ISO 8601 format with timezone.

    Scenario:
        JSON contains datetime string in ISO 8601 format with 'Z' suffix (UTC).

    Expected Outcome:
        String is converted to Python datetime object with timezone info.
    """
    # Arrange
    json_data = {
        "eventId": 1,
        "eventName": "Product Launch",
        "createdAt": "2025-11-20T10:30:00Z",
        "updatedAt": "2025-11-20T12:00:00Z",
    }

    # Act
    result = structure_from_dict(json_data, EventWithDatetime)

    # Assert
    assert result.event_id == 1
    assert result.event_name == "Product Launch"
    assert isinstance(result.created_at, datetime)
    assert result.created_at.year == 2025
    assert result.created_at.month == 11
    assert result.created_at.day == 20
    assert result.created_at.hour == 10
    assert result.created_at.minute == 30
    assert result.updated_at is not None
    assert isinstance(result.updated_at, datetime)


def test_structure_datetime__iso8601_without_timezone__converts_correctly():
    """
    Test datetime structuring with ISO 8601 format without timezone.

    Scenario:
        JSON contains datetime string in ISO 8601 format without timezone info.

    Expected Outcome:
        String is converted to Python datetime object (naive datetime).
    """
    # Arrange
    json_data = {
        "eventId": 2,
        "eventName": "Team Meeting",
        "createdAt": "2025-11-20T14:00:00",
    }

    # Act
    result = structure_from_dict(json_data, EventWithDatetime)

    # Assert
    assert result.event_id == 2
    assert isinstance(result.created_at, datetime)
    assert result.created_at.year == 2025
    assert result.created_at.hour == 14
    assert result.updated_at is None


def test_structure_datetime__iso8601_with_offset__converts_correctly():
    """
    Test datetime structuring with ISO 8601 format with timezone offset.

    Scenario:
        JSON contains datetime string with timezone offset (+02:00).

    Expected Outcome:
        String is converted to Python datetime object with timezone offset.
    """
    # Arrange
    json_data = {
        "eventId": 3,
        "eventName": "Conference",
        "createdAt": "2025-11-20T10:30:00+02:00",
    }

    # Act
    result = structure_from_dict(json_data, EventWithDatetime)

    # Assert
    assert isinstance(result.created_at, datetime)
    assert result.created_at.year == 2025
    assert result.created_at.hour == 10


def test_unstructure_datetime__converts_to_iso8601():
    """
    Test datetime unstructuring to ISO 8601 string.

    Scenario:
        Python datetime object needs to be converted back to JSON string.

    Expected Outcome:
        Datetime is converted to ISO 8601 formatted string.
    """
    # Arrange
    event = EventWithDatetime(
        event_id=1,
        event_name="Launch",
        created_at=datetime(2025, 11, 20, 10, 30, 0),
        updated_at=datetime(2025, 11, 20, 12, 0, 0),
    )

    # Act
    result = unstructure_to_dict(event)

    # Assert
    assert result["eventId"] == 1
    assert result["eventName"] == "Launch"
    assert isinstance(result["createdAt"], str)
    assert "2025-11-20" in result["createdAt"]
    assert "10:30:00" in result["createdAt"]
    assert isinstance(result["updatedAt"], str)


def test_structure_date__iso8601_date__converts_correctly():
    """
    Test date structuring with ISO 8601 date format.

    Scenario:
        JSON contains date string in ISO 8601 format (YYYY-MM-DD).

    Expected Outcome:
        String is converted to Python date object.
    """
    # Arrange
    json_data = {
        "personId": 1,
        "name": "John Doe",
        "birthDate": "1990-05-15",
        "hireDate": "2020-01-10",
    }

    # Act
    result = structure_from_dict(json_data, PersonWithDate)

    # Assert
    assert result.person_id == 1
    assert result.name == "John Doe"
    assert isinstance(result.birth_date, date)
    assert result.birth_date.year == 1990
    assert result.birth_date.month == 5
    assert result.birth_date.day == 15
    assert result.hire_date is not None
    assert isinstance(result.hire_date, date)
    assert result.hire_date.year == 2020


def test_structure_date__missing_optional__handles_correctly():
    """
    Test date structuring with missing optional field.

    Scenario:
        JSON has required date field but missing optional date field.

    Expected Outcome:
        Required date is structured, optional date is None.
    """
    # Arrange
    json_data = {
        "personId": 2,
        "name": "Jane Smith",
        "birthDate": "1985-08-22",
    }

    # Act
    result = structure_from_dict(json_data, PersonWithDate)

    # Assert
    assert isinstance(result.birth_date, date)
    assert result.hire_date is None


def test_unstructure_date__converts_to_iso8601():
    """
    Test date unstructuring to ISO 8601 string.

    Scenario:
        Python date object needs to be converted back to JSON string.

    Expected Outcome:
        Date is converted to ISO 8601 formatted string (YYYY-MM-DD).
    """
    # Arrange
    person = PersonWithDate(
        person_id=1,
        name="John Doe",
        birth_date=date(1990, 5, 15),
        hire_date=date(2020, 1, 10),
    )

    # Act
    result = unstructure_to_dict(person)

    # Assert
    assert result["personId"] == 1
    assert result["name"] == "John Doe"
    assert result["birthDate"] == "1990-05-15"
    assert result["hireDate"] == "2020-01-10"


def test_structure_datetime__invalid_format__raises_error():
    """
    Test datetime structuring with invalid format.

    Scenario:
        JSON contains datetime string in invalid format.

    Expected Outcome:
        ValueError is raised indicating invalid format.
    """
    # Arrange
    json_data = {
        "eventId": 1,
        "eventName": "Test",
        "createdAt": "invalid-datetime",
    }

    # Act & Assert
    with pytest.raises((ValueError, ClassValidationError)):
        structure_from_dict(json_data, EventWithDatetime)


def test_structure_date__invalid_format__raises_error():
    """
    Test date structuring with invalid format.

    Scenario:
        JSON contains date string in invalid format.

    Expected Outcome:
        ValueError is raised indicating invalid format.
    """
    # Arrange
    json_data = {
        "personId": 1,
        "name": "Test",
        "birthDate": "2020/01/15",  # Wrong separator
    }

    # Act & Assert
    with pytest.raises((ValueError, ClassValidationError)):
        structure_from_dict(json_data, PersonWithDate)


@dataclass
class MixedTypesModel:
    """Model with multiple datetime and date fields."""

    item_id: int
    created_date: date
    modified_date: date | None
    created_datetime: datetime
    modified_datetime: datetime | None

    class Meta:
        key_transform_with_load = {
            "itemId": "item_id",
            "createdDate": "created_date",
            "modifiedDate": "modified_date",
            "createdDatetime": "created_datetime",
            "modifiedDatetime": "modified_datetime",
        }
        key_transform_with_dump = {
            "item_id": "itemId",
            "created_date": "createdDate",
            "modified_date": "modifiedDate",
            "created_datetime": "createdDatetime",
            "modified_datetime": "modifiedDatetime",
        }


def test_structure_mixed_types__dates_and_datetimes__converts_correctly():
    """
    Test structuring with both date and datetime fields.

    Scenario:
        JSON contains both date and datetime fields.

    Expected Outcome:
        Both types are correctly structured to their respective Python types.
    """
    # Arrange
    json_data = {
        "itemId": 1,
        "createdDate": "2025-11-20",
        "modifiedDate": "2025-11-21",
        "createdDatetime": "2025-11-20T10:00:00Z",
        "modifiedDatetime": "2025-11-21T15:30:00Z",
    }

    # Act
    result = structure_from_dict(json_data, MixedTypesModel)

    # Assert
    assert isinstance(result.created_date, date)
    assert isinstance(result.modified_date, date)
    assert isinstance(result.created_datetime, datetime)
    assert isinstance(result.modified_datetime, datetime)
    assert result.created_date.year == 2025
    assert result.created_datetime.hour == 10


def test_unstructure_mixed_types__dates_and_datetimes__converts_correctly():
    """
    Test unstructuring with both date and datetime fields.

    Scenario:
        Python object has both date and datetime fields.

    Expected Outcome:
        Both types are correctly unstructured to ISO 8601 strings.
    """
    # Arrange
    item = MixedTypesModel(
        item_id=1,
        created_date=date(2025, 11, 20),
        modified_date=date(2025, 11, 21),
        created_datetime=datetime(2025, 11, 20, 10, 0, 0),
        modified_datetime=datetime(2025, 11, 21, 15, 30, 0),
    )

    # Act
    result = unstructure_to_dict(item)

    # Assert
    assert result["createdDate"] == "2025-11-20"
    assert result["modifiedDate"] == "2025-11-21"
    assert "2025-11-20" in result["createdDatetime"]
    assert "10:00:00" in result["createdDatetime"]
    assert "2025-11-21" in result["modifiedDatetime"]
