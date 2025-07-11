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
