from pyopenapi_gen.context.import_collector import ImportCollector
from pyopenapi_gen.core.utils import NameSanitizer


def test_import_collector_basic() -> None:
    """Test the basic functionality of the ImportCollector.

    Scenario:
        - Add single imports from different modules
        - Generate import statements

    Expected outcome:
        - Each import should be properly formatted as 'from module import name'
        - All added imports should be present in the generated statements
    """
    collector = ImportCollector()
    collector.add_import("os", "path")
    collector.add_import("sys", "exit")

    statements = collector.get_import_statements()

    assert "from os import path" in statements
    assert "from sys import exit" in statements


def test_import_collector_multiple_from_same_module() -> None:
    """Test collecting multiple imports from the same module.

    Scenario:
        - Add multiple imports from a single module
        - Generate import statements

    Expected outcome:
        - All imports from the same module should be consolidated into a single statement
        - The imports should be alphabetically sorted
        - The format should be 'from module import name1, name2, name3'
    """
    collector = ImportCollector()
    collector.add_imports("os", ["path", "environ", "makedirs"])

    statements = collector.get_import_statements()
    assert len(statements) == 1
    assert "from os import environ, makedirs, path" in statements


def test_import_collector_typing_imports() -> None:
    """Test the specialized helper for typing imports.

    Scenario:
        - Use the add_typing_import helper to add multiple typing imports
        - Generate import statements

    Expected outcome:
        - All typing imports should be consolidated into a single statement
        - The imports should be alphabetically sorted
        - The format should be 'from typing import Type1, Type2, Type3'
    """
    collector = ImportCollector()
    collector.add_typing_import("List")
    collector.add_typing_import("Dict")
    collector.add_typing_import("Optional")

    statements = collector.get_import_statements()
    assert len(statements) == 1
    assert "from typing import Dict, List, Optional" in statements


def test_import_collector_relative_imports() -> None:
    """Test the relative import collection functionality.

    Scenario:
        - Add relative imports (imports prefixed with '.') using add_relative_import
        - Generate import statements

    Expected outcome:
        - Relative imports should be included in the generated statements
        - Multiple imports from the same relative module should be consolidated
        - The format should be 'from .module import Name1, Name2'
    """
    collector = ImportCollector()
    collector.add_relative_import(".models", "Pet")
    collector.add_relative_import(".models", "User")

    statements = collector.get_import_statements()
    assert "from .models import Pet, User" in statements


def test_import_collector_formatted_output() -> None:
    """Test the formatted string output method.

    Scenario:
        - Add various imports
        - Generate a formatted string of import statements

    Expected outcome:
        - The output should be a string containing all import statements
        - Each import statement should be on its own line
        - The format should follow our import ordering conventions
    """
    collector = ImportCollector()
    collector.add_import("os", "path")
    collector.add_typing_import("List")

    formatted = collector.get_formatted_imports()

    assert "from os import path" in formatted
    assert "from typing import List" in formatted
    assert isinstance(formatted, str)


def test_import_collector_empty() -> None:
    """Test the behavior when no imports have been added.

    Scenario:
        - Create an ImportCollector but don't add any imports
        - Generate import statements

    Expected outcome:
        - The list of import statements should be empty
        - The formatted output should be an empty string
    """
    collector = ImportCollector()

    statements = collector.get_import_statements()
    formatted = collector.get_formatted_imports()

    assert len(statements) == 0
    assert formatted == ""


def test_import_collector_has_import() -> None:
    """Test the has_import method for checking if imports exist.

    Scenario:
        - Add some imports
        - Check for existence of added and non-added imports

    Expected outcome:
        - has_import should return True for imports that have been added
        - has_import should return False for imports that haven't been added
    """
    collector = ImportCollector()
    collector.add_import("os", "path")
    collector.add_typing_import("List")

    assert collector.has_import("os", "path") is True
    assert collector.has_import("typing", "List") is True
    assert collector.has_import("os", "environ") is False
    assert collector.has_import("sys", "exit") is False


def test_normalize_tag_key__varied_cases_and_punctuation__returns_same_key() -> None:
    """
    Scenario:
        - Tags with different cases and punctuation (e.g., 'DataSources', 'datasources', 'data-sources', 'DATA_SOURCES')
        - We want to ensure they normalize to the same key for deduplication.

    Expected Outcome:
        - All variants should produce the same normalized key string.
    """
    tags = [
        "DataSources",
        "datasources",
        "data-sources",
        "DATA_SOURCES",
        "Data Sources",
    ]
    keys = {NameSanitizer.normalize_tag_key(tag) for tag in tags}
    assert len(keys) == 1
    assert list(keys)[0] == "datasources"


def test_tag_deduplication__multiple_variants__only_one_survives() -> None:
    """
    Scenario:
        - Given a list of tags with different cases and punctuation, simulate deduplication
          logic as in the client emitter.
        - Only the first occurrence of a normalized tag should be kept.

    Expected Outcome:
        - The deduplicated tag list should contain only one entry for all variants.
        - The preserved tag should be the first variant encountered.
    """
    tags = [
        "DataSources",
        "datasources",
        "data-sources",
        "DATA_SOURCES",
        "Data Sources",
    ]
    tag_map = {}
    for tag in tags:
        key = NameSanitizer.normalize_tag_key(tag)
        if key not in tag_map:
            tag_map[key] = tag
    deduped = list(tag_map.values())
    assert deduped == ["DataSources"]


def test_sanitize_module_name__camel_and_pascal_case__snake_case_result() -> None:
    """
    Scenario:
        - Test sanitize_module_name with camel case, PascalCase, and mixed-case names.
        - Names like 'GetDatasourceResponse', 'DataSource', 'getDataSource', 'get_datasource_response',
          'get-datasource-response'.
        - Also include names with dots, already snake_case, ALL_CAPS, and leading/trailing underscores.
    Expected Outcome:
        - All are converted to proper snake_case: 'get_datasource_response', 'data_source', etc.
    """
    assert NameSanitizer.sanitize_module_name("GetDatasourceResponse") == "get_datasource_response"
    assert NameSanitizer.sanitize_module_name("DataSource") == "data_source"
    assert NameSanitizer.sanitize_module_name("getDataSource") == "get_data_source"
    assert NameSanitizer.sanitize_module_name("get_datasource_response") == "get_datasource_response"
    assert NameSanitizer.sanitize_module_name("get-datasource-response") == "get_datasource_response"
    assert NameSanitizer.sanitize_module_name("getDataSource123") == "get_data_source_123"
    assert NameSanitizer.sanitize_module_name("123DataSource") == "_123_data_source"
    assert NameSanitizer.sanitize_module_name("class") == "class_"
    assert NameSanitizer.sanitize_module_name("agent.config.Model") == "agent_config_model"
    assert NameSanitizer.sanitize_module_name("APIKey") == "api_key"
    assert NameSanitizer.sanitize_module_name("HTTP_Response_Code") == "http_response_code"
    assert NameSanitizer.sanitize_module_name("_leadingUnderscore") == "leading_underscore"
    assert NameSanitizer.sanitize_module_name("trailingUnderscore_") == "trailing_underscore"
    assert NameSanitizer.sanitize_module_name("ALL_CAPS_MODULE") == "all_caps_module"
    assert NameSanitizer.sanitize_module_name("openapi_schema.json") == "openapi_schema_json"


def test_sanitize_method_name__various_cases__returns_valid_python_identifier() -> None:
    """
    Scenario:
        - Test sanitize_method_name with paths, operationIds, and invalid Python identifiers.
        - Includes slashes, curly braces, dashes, spaces, numbers, keywords, dots, and ALL_CAPS.

    Expected Outcome:
        - All are converted to valid, snake_case Python method names.
    """
    # Arrange & Act & Assert
    assert NameSanitizer.sanitize_method_name("GET_/tenants/{tenantId}/feedback") == "get_tenants_tenant_id_feedback"
    assert NameSanitizer.sanitize_method_name("get-user-by-id") == "get_user_by_id"
    assert NameSanitizer.sanitize_method_name("postUser") == "post_user"
    assert NameSanitizer.sanitize_method_name("/foo/bar/{baz}") == "foo_bar_baz"
    assert NameSanitizer.sanitize_method_name("123start") == "_123start"
    assert NameSanitizer.sanitize_method_name("class") == "class_"
    assert NameSanitizer.sanitize_method_name("already_valid") == "already_valid"
    assert NameSanitizer.sanitize_method_name("multiple___underscores") == "multiple_underscores"
    assert NameSanitizer.sanitize_method_name("with space and-dash") == "with_space_and_dash"
    assert NameSanitizer.sanitize_method_name("{param}") == "param"
    assert NameSanitizer.sanitize_method_name("_leading_underscore") == "leading_underscore"
    assert NameSanitizer.sanitize_method_name("trailing_underscore_") == "trailing_underscore"
    assert NameSanitizer.sanitize_method_name("ALL_CAPS_METHOD") == "all_caps_method"
    assert NameSanitizer.sanitize_method_name("Method.With.Dots") == "method_with_dots"
    assert NameSanitizer.sanitize_method_name("openapi_schema.json") == "openapi_schema_json"
    assert NameSanitizer.sanitize_method_name("users/{userId}/profile") == "users_user_id_profile"


# --- clean_auto_generated_operation_id tests ---


def test_clean_auto_generated_operation_id__fastapi_simple_path__strips_suffix() -> None:
    """FastAPI-style operationId with a simple path is cleaned to just the function name."""
    assert NameSanitizer.clean_auto_generated_operation_id("create_details_details_post", "POST", "/details") == (
        "create_details"
    )


def test_clean_auto_generated_operation_id__fastapi_nested_path__strips_suffix() -> None:
    """FastAPI-style operationId with nested path parameters is cleaned correctly."""
    assert (
        NameSanitizer.clean_auto_generated_operation_id(
            "get_user_profile_users_user_id_profile_get", "GET", "/users/{user_id}/profile"
        )
        == "get_user_profile"
    )


def test_clean_auto_generated_operation_id__fastapi_versioned_path__strips_suffix() -> None:
    """FastAPI-style operationId with versioned API path is cleaned correctly."""
    assert (
        NameSanitizer.clean_auto_generated_operation_id("list_items_api_v1_items_get", "GET", "/api/v1/items")
        == "list_items"
    )


def test_clean_auto_generated_operation_id__fastapi_delete__strips_suffix() -> None:
    """FastAPI-style DELETE operationId is cleaned correctly."""
    assert (
        NameSanitizer.clean_auto_generated_operation_id("delete_details_details_delete", "DELETE", "/details")
        == "delete_details"
    )


def test_clean_auto_generated_operation_id__fastapi_put_nested__strips_suffix() -> None:
    """FastAPI-style PUT with nested path parameters is cleaned correctly."""
    assert (
        NameSanitizer.clean_auto_generated_operation_id(
            "update_settings_tenants_tenant_id_settings_put", "PUT", "/tenants/{tenant_id}/settings"
        )
        == "update_settings"
    )


def test_clean_auto_generated_operation_id__clean_no_suffix__returns_unchanged() -> None:
    """An operationId without the method suffix is returned unchanged."""
    assert NameSanitizer.clean_auto_generated_operation_id("createUser", "POST", "/users") == "createUser"


def test_clean_auto_generated_operation_id__camel_case_no_suffix__returns_unchanged() -> None:
    """A camelCase operationId without method suffix is returned unchanged."""
    assert NameSanitizer.clean_auto_generated_operation_id("listPets", "GET", "/pets") == "listPets"


def test_clean_auto_generated_operation_id__path_mismatch__returns_unchanged() -> None:
    """An operationId with method suffix but non-matching path is returned unchanged."""
    assert NameSanitizer.clean_auto_generated_operation_id("create_blog_post", "POST", "/articles") == (
        "create_blog_post"
    )


def test_clean_auto_generated_operation_id__root_path__returns_unchanged() -> None:
    """Root path '/' produces empty normalised path, so operationId is returned unchanged."""
    assert NameSanitizer.clean_auto_generated_operation_id("root_get", "GET", "/") == "root_get"


def test_clean_auto_generated_operation_id__just_method_name__returns_unchanged() -> None:
    """An operationId that is just the method name (no suffix pattern) is returned unchanged."""
    assert NameSanitizer.clean_auto_generated_operation_id("get", "GET", "/") == "get"


def test_clean_auto_generated_operation_id__path_only_parameter__strips_suffix() -> None:
    """Path with only a parameter segment is handled correctly."""
    assert NameSanitizer.clean_auto_generated_operation_id("get_item_item_id_get", "GET", "/{item_id}") == "get_item"


def test_clean_auto_generated_operation_id__case_insensitive_method_lower__strips_suffix() -> None:
    """Method matching is case-insensitive (lowercase input)."""
    assert NameSanitizer.clean_auto_generated_operation_id("create_details_details_post", "post", "/details") == (
        "create_details"
    )


def test_clean_auto_generated_operation_id__case_insensitive_method_mixed__strips_suffix() -> None:
    """Method matching is case-insensitive (mixed case input)."""
    assert NameSanitizer.clean_auto_generated_operation_id("create_details_details_post", "Post", "/details") == (
        "create_details"
    )


def test_clean_auto_generated_operation_id__path_with_hyphens__strips_suffix() -> None:
    """Hyphens in path segments are normalised to underscores (matching FastAPI behaviour)."""
    assert (
        NameSanitizer.clean_auto_generated_operation_id("list_users_api_v2_users_get", "GET", "/api-v2/users")
        == "list_users"
    )


def test_clean_auto_generated_operation_id__path_with_dots__strips_suffix() -> None:
    """Dots in path segments are normalised to underscores (matching FastAPI behaviour)."""
    assert (
        NameSanitizer.clean_auto_generated_operation_id("get_config_api_v1_0_config_get", "GET", "/api/v1.0/config")
        == "get_config"
    )


def test_clean_auto_generated_operation_id__multiple_path_parameters__strips_suffix() -> None:
    """Multiple path parameters are handled correctly."""
    assert (
        NameSanitizer.clean_auto_generated_operation_id(
            "get_user_role_org_id_users_user_id_get", "GET", "/{org_id}/users/{user_id}"
        )
        == "get_user_role"
    )


def test_clean_auto_generated_operation_id__empty_prefix__returns_unchanged() -> None:
    """When stripping both suffixes would yield an empty method name, returns original."""
    assert NameSanitizer.clean_auto_generated_operation_id("details_post", "POST", "/details") == "details_post"


def test_sanitize_tag_class_name__various_inputs__pascal_case_client_result() -> None:
    """
    Scenario:
        - Test sanitize_tag_class_name with various input tag strings.
        - Tags can have spaces, hyphens, underscores, and mixed casing.

    Expected Outcome:
        - All inputs are converted to valid Python class names in PascalCase,
          with "Client" appended.
    """
    # Arrange & Act & Assert
    assert NameSanitizer.sanitize_tag_class_name("DataSources") == "DatasourcesClient"
    assert NameSanitizer.sanitize_tag_class_name("user events") == "UserEventsClient"
    assert NameSanitizer.sanitize_tag_class_name("api-keys") == "ApiKeysClient"
    assert NameSanitizer.sanitize_tag_class_name("auth_module") == "AuthModuleClient"
    assert NameSanitizer.sanitize_tag_class_name("ALL_CAPS_TAG") == "AllCapsTagClient"
    assert NameSanitizer.sanitize_tag_class_name("mixedCaseTag") == "MixedcasetagClient"
    assert (
        NameSanitizer.sanitize_tag_class_name("123Tag") == "123tagClient"
    )  # Note: sanitize_class_name would prefix with _, but this one doesn't


def test_sanitize_tag_attr_name__various_inputs__snake_case_result() -> None:
    """
    Scenario:
        - Test sanitize_tag_attr_name with various input tag strings.
        - Tags can have spaces, hyphens, underscores, and mixed casing.

    Expected Outcome:
        - All inputs are converted to valid Python attribute names in snake_case.
    """
    # Arrange & Act & Assert
    assert NameSanitizer.sanitize_tag_attr_name("DataSources") == "datasources"
    assert NameSanitizer.sanitize_tag_attr_name("user events") == "user_events"
    assert NameSanitizer.sanitize_tag_attr_name("api-keys") == "api_keys"
    assert NameSanitizer.sanitize_tag_attr_name("auth_module") == "auth_module"
    assert NameSanitizer.sanitize_tag_attr_name("ALL_CAPS_TAG") == "all_caps_tag"
    assert NameSanitizer.sanitize_tag_attr_name("mixedCaseTag") == "mixedcasetag"  # Default re.sub behavior
    assert NameSanitizer.sanitize_tag_attr_name("123Tag") == "123tag"
    assert NameSanitizer.sanitize_tag_attr_name("_Tag_With_Leading_Trailing_") == "tag_with_leading_trailing"


def test_sanitize_filename__various_inputs__snake_case_py_result() -> None:
    """
    Scenario:
        - Test sanitize_filename with various input strings.
        - Inputs include PascalCase, camelCase, names with spaces, hyphens, and dots.
        - Test with default '.py' suffix and a custom suffix.

    Expected Outcome:
        - All inputs are converted to valid Python filenames in snake_case, with the
          specified suffix (defaulting to '.py').
        - Keywords are appended with an underscore before the suffix.
        - Names starting with digits are prefixed with an underscore.
    """
    # Arrange & Act & Assert
    assert NameSanitizer.sanitize_filename("UserListResponse") == "user_list_response.py"
    assert NameSanitizer.sanitize_filename("agent.config") == "agent_config.py"
    assert NameSanitizer.sanitize_filename("getHtmlData") == "get_html_data.py"
    assert NameSanitizer.sanitize_filename("My API Endpoint") == "my_api_endpoint.py"
    assert NameSanitizer.sanitize_filename("123Start") == "_123_start.py"
    assert NameSanitizer.sanitize_filename("class") == "class_.py"
    assert (
        NameSanitizer.sanitize_filename("ComplexName-With-Dots.and_numbers123")
        == "complex_name_with_dots_and_numbers_123.py"
    )
    # Test with custom suffix
    assert NameSanitizer.sanitize_filename("MyModel") == "my_model.py"
    assert NameSanitizer.sanitize_filename("MyModelType") == "my_model_type.py"
    assert NameSanitizer.sanitize_filename("MyOtherModel", suffix=".model.py") == "my_other_model.model.py"
    assert NameSanitizer.sanitize_filename("class", suffix=".md") == "class_.md"


def test_import_collector_double_dot_relative_import() -> None:
    """
    Scenario:
        - Add a relative import with three leading dots (e.g., '...models.foo').
        - Generate import statements.
    Expected outcome:
        - The import statement should be 'from ...models.foo import Bar'.
        - No slashes should appear in the output.
    """
    collector = ImportCollector()
    collector.add_relative_import("...models.foo", "Bar")
    statements = collector.get_import_statements()
    assert "from ...models.foo import Bar" in statements
    for stmt in statements:
        assert "/" not in stmt, f"Slash found in import statement: {stmt}"


def test_import_collector_sibling_directory_import() -> None:
    """
    Scenario:
        - Simulate an endpoint importing from a sibling models directory (e.g., '..models.bar').
        - Generate import statements.
    Expected outcome:
        - The import statement should be 'from ..models.bar import Baz'.
        - No slashes should appear in the output.
    """
    collector = ImportCollector()
    collector.add_relative_import("..models.bar", "Baz")
    statements = collector.get_import_statements()
    assert "from ..models.bar import Baz" in statements
    for stmt in statements:
        assert "/" not in stmt, f"Slash found in import statement: {stmt}"


# DataclassSerializer Tests


def test_dataclass_serializer__baseschema_with_mappings__uses_api_field_names() -> None:
    """Test DataclassSerializer respects BaseSchema field name mappings.

    Scenario:
        - Create a BaseSchema dataclass with field mappings (snake_case -> camelCase)
        - Serialize the instance using DataclassSerializer.serialize()

    Expected Outcome:
        - The serialized dictionary should use API field names (camelCase)
        - Should not use Python field names (snake_case)
    """
    # Arrange
    from dataclasses import dataclass

    from pyopenapi_gen.core.utils import DataclassSerializer

    @dataclass
    class DocumentUpdate:
        """Test schema with field mappings."""

        data_source_id: str
        mime_type: str | None = None
        last_modified: str | None = None

        class Meta:
            """Field mappings."""

            key_transform_with_dump = {
                "data_source_id": "dataSourceId",
                "mime_type": "mimeType",
                "last_modified": "lastModified",
            }

    obj = DocumentUpdate(data_source_id="source-123", mime_type="text/html", last_modified="2024-10-23")

    # Act
    result = DataclassSerializer.serialize(obj)

    # Assert
    assert isinstance(result, dict)
    assert "dataSourceId" in result  # camelCase (API name)
    assert "mimeType" in result
    assert "lastModified" in result
    assert "data_source_id" not in result  # snake_case (Python name) should NOT be present
    assert "mime_type" not in result
    assert "last_modified" not in result
    assert result["dataSourceId"] == "source-123"
    assert result["mimeType"] == "text/html"
    assert result["lastModified"] == "2024-10-23"


def test_dataclass_serializer__nested_baseschema__maps_recursively() -> None:
    """Test DataclassSerializer handles nested BaseSchema instances with field mappings.

    Scenario:
        - Create nested BaseSchema dataclasses with field mappings
        - Serialize the parent instance

    Expected Outcome:
        - Both parent and nested objects should use API field names
        - Nested field mappings should be respected recursively
    """
    # Arrange
    from dataclasses import dataclass

    from pyopenapi_gen.core.utils import DataclassSerializer

    @dataclass
    class Address:
        """Nested schema with field mappings."""

        street_name: str
        postal_code: str

        class Meta:
            """Field mappings."""

            key_transform_with_dump = {"street_name": "streetName", "postal_code": "postalCode"}

    @dataclass
    class User:
        """Parent schema with field mappings."""

        user_id: str
        full_name: str
        home_address: Address

        class Meta:
            """Field mappings."""

            key_transform_with_dump = {
                "user_id": "userId",
                "full_name": "fullName",
                "home_address": "homeAddress",
            }

    address = Address(street_name="Main St", postal_code="12345")
    user = User(user_id="user-123", full_name="John Doe", home_address=address)

    # Act
    result = DataclassSerializer.serialize(user)

    # Assert
    assert isinstance(result, dict)
    assert "userId" in result
    assert "fullName" in result
    assert "homeAddress" in result
    assert isinstance(result["homeAddress"], dict)
    assert "streetName" in result["homeAddress"]
    assert "postalCode" in result["homeAddress"]
    assert result["userId"] == "user-123"
    assert result["homeAddress"]["streetName"] == "Main St"


def test_dataclass_serializer__plain_dataclass__still_works() -> None:
    """Test DataclassSerializer backwards compatibility with plain dataclasses.

    Scenario:
        - Create a plain dataclass (not BaseSchema)
        - Serialize the instance

    Expected Outcome:
        - Should use field.name directly (no field mapping)
        - Backwards compatibility maintained
    """
    # Arrange
    from dataclasses import dataclass

    from pyopenapi_gen.core.utils import DataclassSerializer

    @dataclass
    class PlainModel:
        """Plain dataclass without BaseSchema."""

        field_one: str
        field_two: int

    obj = PlainModel(field_one="value", field_two=42)

    # Act
    result = DataclassSerializer.serialize(obj)

    # Assert
    assert isinstance(result, dict)
    assert "field_one" in result
    assert "field_two" in result
    assert result["field_one"] == "value"
    assert result["field_two"] == 42


def test_dataclass_serializer__exclude_none_handling() -> None:
    """Test DataclassSerializer excludes None values when using BaseSchema.

    Scenario:
        - Create a BaseSchema instance with some None values
        - Serialize the instance

    Expected Outcome:
        - None values should be excluded from the result
        - Non-None values should be present with correct field names
    """
    # Arrange
    from dataclasses import dataclass

    from pyopenapi_gen.core.utils import DataclassSerializer

    @dataclass
    class OptionalFields:
        """Schema with optional fields."""

        required_field: str
        optional_field: str | None = None
        another_optional: str | None = None

        class Meta:
            """Field mappings."""

            key_transform_with_dump = {
                "required_field": "requiredField",
                "optional_field": "optionalField",
                "another_optional": "anotherOptional",
            }

    obj = OptionalFields(required_field="present", optional_field=None, another_optional=None)

    # Act
    result = DataclassSerializer.serialize(obj)

    # Assert
    assert isinstance(result, dict)
    assert "requiredField" in result
    assert "optionalField" not in result  # None values excluded
    assert "anotherOptional" not in result
    assert result["requiredField"] == "present"


def test_dataclass_serializer__list_of_baseschema__maps_all_items() -> None:
    """Test DataclassSerializer handles lists of BaseSchema instances.

    Scenario:
        - Create a list of BaseSchema instances with field mappings
        - Serialize the list

    Expected Outcome:
        - Each item in the list should have field names mapped
        - All items should use API field names
    """
    # Arrange
    from dataclasses import dataclass

    from pyopenapi_gen.core.utils import DataclassSerializer

    @dataclass
    class Item:
        """Schema with field mappings."""

        item_id: str
        item_name: str

        class Meta:
            """Field mappings."""

            key_transform_with_dump = {"item_id": "itemId", "item_name": "itemName"}

    items = [Item(item_id="1", item_name="First"), Item(item_id="2", item_name="Second")]

    # Act
    result = DataclassSerializer.serialize(items)

    # Assert
    assert isinstance(result, list)
    assert len(result) == 2
    assert all("itemId" in item for item in result)
    assert all("itemName" in item for item in result)
    assert result[0]["itemId"] == "1"
    assert result[1]["itemName"] == "Second"
