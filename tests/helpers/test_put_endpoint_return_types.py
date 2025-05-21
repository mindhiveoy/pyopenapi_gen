"""Tests for PUT endpoint return type inference."""

import unittest

from pyopenapi_gen import HTTPMethod, IROperation, IRRequestBody, IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.helpers.endpoint_utils import _find_resource_schema, get_return_type


def test_find_resource_schema() -> None:
    """Test _find_resource_schema helper function."""
    # Create test schemas
    tenant_schema = IRSchema(name="Tenant", type="object")
    tenant_update_schema = IRSchema(name="TenantUpdate", type="object")
    user_schema = IRSchema(name="User", type="object")

    # Create schemas dictionary
    schemas = {
        "Tenant": tenant_schema,
        "TenantUpdate": tenant_update_schema,
        "User": user_schema,
    }

    # Test finding resource schema from update schema
    resource_schema = _find_resource_schema("TenantUpdate", schemas)
    assert resource_schema is not None
    assert resource_schema.name == "Tenant"

    # Test with non-update schema name
    resource_schema = _find_resource_schema("User", schemas)
    assert resource_schema is None

    # Test with non-existent base resource schema
    resource_schema = _find_resource_schema("NonExistentUpdate", schemas)
    assert resource_schema is None


def test_put_endpoint_with_update_schema_infers_resource_type() -> None:
    """Test return type inference for PUT endpoint with Update schema."""
    # Create test schemas
    tenant_schema = IRSchema(name="Tenant", type="object")
    tenant_update_schema = IRSchema(name="TenantUpdate", type="object")

    # Create schemas dictionary
    schemas = {
        "Tenant": tenant_schema,
        "TenantUpdate": tenant_update_schema,
    }

    # Prepare schemas
    for schema_obj in schemas.values():
        if schema_obj.name:
            schema_obj.generation_name = NameSanitizer.sanitize_class_name(schema_obj.name)
            schema_obj.final_module_stem = NameSanitizer.sanitize_module_name(schema_obj.name)

    # Create context
    context = RenderContext(
        overall_project_root="/tmp",
        package_root_for_generated_code="/tmp/test_api",
        core_package_name="test_api.core",
    )

    # Create operation with PUT method and TenantUpdate request body
    operation = IROperation(
        operation_id="updateTenant",
        method=HTTPMethod.PUT,
        path="/tenants/{tenant_id}",
        parameters=[],
        responses=[],  # No response defined
        summary="Update tenant",
        description="Updates a tenant's information",
        request_body=IRRequestBody(required=True, content={"application/json": tenant_update_schema}),
    )

    # Get return type
    return_type, needs_unwrap = get_return_type(operation, context, schemas)

    # Assert return type is inferred from resource schema (Tenant), not the update schema (TenantUpdate)
    assert return_type == "Tenant"
    assert needs_unwrap is False


def test_put_endpoint_with_no_matching_resource_uses_update_type() -> None:
    """Test return type when no matching resource schema is found."""
    # Create test schema
    config_update_schema = IRSchema(name="ConfigUpdate", type="object")

    # Create schemas dictionary (without a matching Config schema)
    schemas = {
        "ConfigUpdate": config_update_schema,
    }

    # Prepare schemas
    for schema_obj in schemas.values():
        if schema_obj.name:
            schema_obj.generation_name = NameSanitizer.sanitize_class_name(schema_obj.name)
            schema_obj.final_module_stem = NameSanitizer.sanitize_module_name(schema_obj.name)

    # Create context
    context = RenderContext(
        overall_project_root="/tmp",
        package_root_for_generated_code="/tmp/test_api",
        core_package_name="test_api.core",
    )

    # Create operation with PUT method and ConfigUpdate request body
    operation = IROperation(
        operation_id="updateConfig",
        method=HTTPMethod.PUT,
        path="/config",
        parameters=[],
        responses=[],  # No response defined
        summary="Update configuration",
        description="Updates the system configuration",
        request_body=IRRequestBody(required=True, content={"application/json": config_update_schema}),
    )

    # Get return type
    return_type, needs_unwrap = get_return_type(operation, context, schemas)

    # Assert return type is the update schema itself (ConfigUpdate)
    assert return_type == "ConfigUpdate"
    assert needs_unwrap is False


def test_non_put_endpoint_returns_none_without_response() -> None:
    """Test that non-PUT endpoints still return None when no response is defined."""
    # Create test schema
    user_schema = IRSchema(name="User", type="object")

    # Create schemas dictionary
    schemas = {
        "User": user_schema,
    }

    # Prepare schemas
    for schema_obj in schemas.values():
        if schema_obj.name:
            schema_obj.generation_name = NameSanitizer.sanitize_class_name(schema_obj.name)
            schema_obj.final_module_stem = NameSanitizer.sanitize_module_name(schema_obj.name)

    # Create context
    context = RenderContext(
        overall_project_root="/tmp",
        package_root_for_generated_code="/tmp/test_api",
        core_package_name="test_api.core",
    )

    # Create operation with POST method (not PUT)
    operation = IROperation(
        operation_id="createUser",
        method=HTTPMethod.POST,
        path="/users",
        parameters=[],
        responses=[],  # No response defined
        summary="Create user",
        description="Creates a new user",
        request_body=IRRequestBody(required=True, content={"application/json": user_schema}),
    )

    # Get return type
    return_type, needs_unwrap = get_return_type(operation, context, schemas)

    # Assert return type is None for non-PUT operation without response
    assert return_type == "None"
    assert needs_unwrap is False


if __name__ == "__main__":
    unittest.main()
