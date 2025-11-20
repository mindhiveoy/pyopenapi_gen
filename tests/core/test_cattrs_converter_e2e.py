"""
End-to-end tests for cattrs converter with real-world JSON responses.

Tests the generic camelCase ↔ snake_case transformation system with actual
API responses to ensure the converter works correctly for nested structures.
"""

from dataclasses import dataclass, field
from typing import List

from pyopenapi_gen.core.cattrs_converter import structure_from_dict, unstructure_to_dict


# Test dataclasses matching the tenant API response structure
@dataclass
class TenantCount:
    """Represents the _count field in tenant responses."""

    pass  # Can be empty dict in actual responses


@dataclass
class TenantDataItem:
    """
    Represents a single tenant item in the response.

    Scenario:
        Model for tenant data with camelCase JSON keys that need to be
        transformed to snake_case Python fields, including special handling
        for Python keywords like 'id'.
    """

    id_: str  # Maps from 'id' (Python keyword)
    name: str
    domain: str
    count: TenantCount | None = None  # Maps from '_count'

    class Meta:
        """Configure field name mapping for JSON conversion."""

        key_transform_with_load = {
            "_count": "count",
            "id": "id_",
        }
        key_transform_with_dump = {
            "count": "_count",
            "id_": "id",
        }


@dataclass
class PaginationMeta:
    """
    Represents pagination metadata in paginated responses.

    Scenario:
        Model for pagination info with camelCase JSON keys that need to be
        transformed to snake_case Python fields.
    """

    page: int
    page_size: int  # Maps from 'pageSize'
    total: int
    total_pages: int  # Maps from 'totalPages'
    has_next: bool | None = None  # Maps from 'hasNext'
    has_previous: bool | None = None  # Maps from 'hasPrevious'

    class Meta:
        """Configure field name mapping for JSON conversion."""

        key_transform_with_load = {
            "hasNext": "has_next",
            "hasPrevious": "has_previous",
            "pageSize": "page_size",
            "totalPages": "total_pages",
        }
        key_transform_with_dump = {
            "has_next": "hasNext",
            "has_previous": "hasPrevious",
            "page_size": "pageSize",
            "total_pages": "totalPages",
        }


@dataclass
class TenantsResponse:
    """
    Represents the complete tenants API response.

    Scenario:
        Top-level response model containing a list of tenant items and pagination
        metadata. Tests nested dataclass structuring with field name transformations.
    """

    data: List[TenantDataItem] = field(default_factory=list)
    meta: PaginationMeta | None = None


def test_structure_from_dict__real_tenants_json__structures_correctly():
    """
    Test structuring actual tenant API JSON response into dataclasses.

    Scenario:
        An API endpoint returns a paginated list of tenants with camelCase keys.
        The JSON contains nested objects (meta) and lists of objects (data array).
        Some fields use Python keywords (id) which get transformed to id_.
        The converter should handle all name transformations automatically.

    Expected Outcome:
        The JSON is correctly structured into Python dataclasses with all field
        names transformed from camelCase to snake_case, including nested objects
        and list items. Python keyword conflicts are handled (id → id_).
    """
    # Arrange: Actual JSON response from tenant list endpoint
    json_response = {
        "data": [
            {"id": "demo", "name": "Demo Tenant", "domain": "demo.mindhive.fi", "_count": {}},
            {"id": "development", "name": "Development Tenant", "domain": "localhost:3000", "_count": {}},
            {"id": "system", "name": "System Tenant", "domain": "system.mindhive.fi", "_count": {}},
        ],
        "meta": {
            "page": 0,
            "pageSize": 10,
            "total": 3,
            "totalPages": 1,
            "hasNext": False,
            "hasPrevious": False,
        },
    }

    # Act: Structure the JSON into Python dataclasses
    result = structure_from_dict(json_response, TenantsResponse)

    # Assert: Verify top-level structure
    assert isinstance(result, TenantsResponse)
    assert len(result.data) == 3
    assert result.meta is not None

    # Assert: Verify first tenant item
    first_tenant = result.data[0]
    assert isinstance(first_tenant, TenantDataItem)
    assert first_tenant.id_ == "demo"  # Note: id_ not id (Python keyword handling)
    assert first_tenant.name == "Demo Tenant"
    assert first_tenant.domain == "demo.mindhive.fi"
    assert isinstance(first_tenant.count, TenantCount)

    # Assert: Verify second tenant item
    second_tenant = result.data[1]
    assert second_tenant.id_ == "development"
    assert second_tenant.name == "Development Tenant"
    assert second_tenant.domain == "localhost:3000"

    # Assert: Verify third tenant item
    third_tenant = result.data[2]
    assert third_tenant.id_ == "system"
    assert third_tenant.name == "System Tenant"
    assert third_tenant.domain == "system.mindhive.fi"

    # Assert: Verify pagination metadata (camelCase → snake_case transformation)
    assert isinstance(result.meta, PaginationMeta)
    assert result.meta.page == 0
    assert result.meta.page_size == 10  # Transformed from 'pageSize'
    assert result.meta.total == 3
    assert result.meta.total_pages == 1  # Transformed from 'totalPages'
    assert result.meta.has_next is False  # Transformed from 'hasNext'
    assert result.meta.has_previous is False  # Transformed from 'hasPrevious'


def test_unstructure_to_dict__structured_tenants__unstructures_correctly():
    """
    Test unstructuring Python dataclasses back to JSON with camelCase keys.

    Scenario:
        Python dataclasses with snake_case fields need to be serialised back to
        JSON with camelCase keys for API responses. This tests the reverse
        transformation (snake_case → camelCase).

    Expected Outcome:
        The dataclasses are correctly unstructured into a dictionary with camelCase
        keys matching the original JSON format, including nested objects and lists.
    """
    # Arrange: Create Python dataclass instances
    response = TenantsResponse(
        data=[
            TenantDataItem(id_="demo", name="Demo Tenant", domain="demo.mindhive.fi", count=TenantCount()),
            TenantDataItem(
                id_="development",
                name="Development Tenant",
                domain="localhost:3000",
                count=TenantCount(),
            ),
        ],
        meta=PaginationMeta(
            page=0,
            page_size=10,
            total=2,
            total_pages=1,
            has_next=False,
            has_previous=False,
        ),
    )

    # Act: Unstructure to dictionary
    result = unstructure_to_dict(response)

    # Assert: Verify top-level structure
    assert "data" in result
    assert "meta" in result
    assert len(result["data"]) == 2

    # Assert: Verify first tenant has correct JSON keys (snake_case → camelCase)
    first_tenant = result["data"][0]
    assert first_tenant["id"] == "demo"  # id_ → id
    assert first_tenant["name"] == "Demo Tenant"
    assert first_tenant["domain"] == "demo.mindhive.fi"
    assert "_count" in first_tenant  # count → _count

    # Assert: Verify meta has correct JSON keys
    meta = result["meta"]
    assert meta["page"] == 0
    assert meta["pageSize"] == 10  # page_size → pageSize
    assert meta["total"] == 2
    assert meta["totalPages"] == 1  # total_pages → totalPages
    assert meta["hasNext"] is False  # has_next → hasNext
    assert meta["hasPrevious"] is False  # has_previous → hasPrevious


def test_structure_from_dict__empty_data_list__handles_correctly():
    """
    Test structuring response with empty data array.

    Scenario:
        API returns a valid response but with no data items (empty result set).
        The converter should handle empty lists correctly.

    Expected Outcome:
        Response is structured correctly with empty data list and valid metadata.
    """
    # Arrange
    json_response = {
        "data": [],
        "meta": {
            "page": 0,
            "pageSize": 10,
            "total": 0,
            "totalPages": 0,
            "hasNext": False,
            "hasPrevious": False,
        },
    }

    # Act
    result = structure_from_dict(json_response, TenantsResponse)

    # Assert
    assert isinstance(result, TenantsResponse)
    assert len(result.data) == 0
    assert result.meta is not None
    assert result.meta.total == 0
    assert result.meta.total_pages == 0


def test_structure_from_dict__missing_optional_fields__uses_defaults():
    """
    Test structuring response with missing optional fields.

    Scenario:
        API response may not include optional fields like hasNext/hasPrevious.
        The converter should use None defaults for missing optional fields.

    Expected Outcome:
        Response is structured correctly with None for missing optional fields.
    """
    # Arrange: JSON without optional fields
    json_response = {
        "data": [{"id": "test", "name": "Test", "domain": "test.example.com", "_count": {}}],
        "meta": {
            "page": 0,
            "pageSize": 10,
            "total": 1,
            "totalPages": 1,
            # hasNext and hasPrevious intentionally missing
        },
    }

    # Act
    result = structure_from_dict(json_response, TenantsResponse)

    # Assert
    assert isinstance(result, TenantsResponse)
    assert len(result.data) == 1
    assert result.meta is not None
    assert result.meta.has_next is None  # Should default to None
    assert result.meta.has_previous is None  # Should default to None
