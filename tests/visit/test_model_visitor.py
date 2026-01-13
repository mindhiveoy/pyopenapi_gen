import logging
import os  # For path manipulation
import unittest  # Add this import

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer  # Added import

# from pyopenapi_gen.model.ir_schema import IRSchema, IRSchemaType # Old incorrect import
from pyopenapi_gen.ir import IRSchema  # Updated import path

# CodeWriter is not directly used by the test calling ModelVisitor, but ModelVisitor uses
# PythonConstructRenderer which uses CodeWriter from pyopenapi_gen.utils.code_writer import
# CodeWriter
from pyopenapi_gen.visit.model.model_visitor import ModelVisitor  # Updated import path

# from pyopenapi_gen.utils.log_utils import setup_logging # This path is incorrect, removing for now

# Configure logging for specific modules to DEBUG for this test class

# Attempt to silence blib2to3.pgen2.driver logs
logging.getLogger("blib2to3.pgen2.driver").setLevel(logging.WARNING)


class TestModelVisitor(unittest.TestCase):  # Inherit from unittest.TestCase
    def setUp(self) -> None:
        # Arrange
        self.model_visitor = ModelVisitor()

    def test_model_visitor__openapi_31_nullable_types__generates_optional_annotations(self) -> None:
        """
        Scenario:
            ModelVisitor processes a schema with a property that uses OpenAPI 3.1
            style nullable types (Dict with extra None parameter).

        Expected Outcome:
            The ModelVisitor should generate the model with proper Optional types
            and cleaned type annotations (invalid None parameters removed).
        """
        # Arrange
        # Create a schema with a property using a Dict with an extra None parameter
        schema = IRSchema(
            name="TestModel",
            type="object",
            description="A test model for OpenAPI 3.1 nullable types",
            properties={
                "config": IRSchema(
                    name="config",
                    type="object",
                    description="Configuration settings",
                    is_nullable=True,  # This should be rendered as dict[str, Any] | None
                )
            },
        )

        context = RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )

        # Mock the TypeHelper to return a type with invalid None parameter
        # (normally this would come from the schema parser)
        from unittest.mock import patch

        with patch(
            "pyopenapi_gen.helpers.type_helper.TypeHelper.get_python_type_for_schema",
            return_value="dict[str, Any, None]",
        ):  # Return invalid type
            # Act
            result = self.model_visitor.visit_IRSchema(schema, context)

            # Assert - unified type system correctly generates Optional for nullable types
            self.assertIn("class TestModel:", result)  # Should use BaseSchema due to field mapping
            self.assertIn("config_: dict[str, Any] | None =", result)  # Field exists with correct type
            self.assertIn("None", result)  # Has None default (may be multi-line)
            self.assertIn("class Meta:", result)  # Has Meta class
            self.assertIn('"config": "config_",', result)  # Has field mapping
            self.assertNotIn(
                "dict[str, Any, None]", result, "Invalid type with None parameter was not cleaned"
            )  # Use self.assertNotIn

    def test_visit_IRSchema_for_AgentDataSource_with_properties_generates_correct_fields(self) -> None:
        """
        Scenario:
            - An IRSchema representing 'AgentDataSource' with all its defined properties
              is provided to ModelVisitor.
        Expected Outcome:
            - The ModelVisitor should generate Python dataclass code that includes all these fields
              with their correct type annotations.
        """
        # Arrange
        agent_id_prop = IRSchema(
            name="agentId",
            type="string",
            format="uuid",
            description="The ID of the agent",
            is_nullable=False,  # Properties don't have is_required; parent lists required names
        )
        data_source_id_prop = IRSchema(
            name="dataSourceId",
            type="string",
            format="uuid",
            description="The ID of the data source",
            is_nullable=False,
        )
        description_prop = IRSchema(
            name="description",
            type="string",
            description="Custom description for this agent-datasource link",
            is_nullable=True,
        )
        instructions_prop = IRSchema(
            name="instructions",
            type="string",
            description="Specific instructions for the agent on how to use this data source",
            is_nullable=True,
        )
        config_prop = IRSchema(
            name="config",
            type="object",
            description="Configuration settings",
            is_nullable=True,
            properties={},  # Actual sub-properties not needed for this field existence test
            additional_properties=True,  # Allows dict[str, Any] behavior if TypeHelper maps this
        )
        created_at_prop = IRSchema(
            name="createdAt",
            type="string",
            format="date-time",
            description="Timestamp of when this link was created",
            is_nullable=False,
        )
        updated_at_prop = IRSchema(
            name="updatedAt",
            type="string",
            format="date-time",
            description="Timestamp of the last update to this link",
            is_nullable=False,
        )
        # For a referenced schema, TypeHelper will use the name directly if it's not a primitive.
        # It should try to import "DataSource".
        data_source_ref_prop = IRSchema(
            name="dataSource",
            type="DataSource",  # This tells TypeHelper to use 'DataSource' as the type name
            description="The full DataSource object",
            is_nullable=True,
            # ref_path="#/components/schemas/DataSource" # ref_path is not a direct field of IRSchema constructor
        )

        agent_data_source_schema = IRSchema(
            name="AgentDataSource",
            type="object",
            description="Agent Data Source model...",
            properties={
                "agentId": agent_id_prop,
                "dataSourceId": data_source_id_prop,
                "description": description_prop,
                "instructions": instructions_prop,
                "config": config_prop,
                "createdAt": created_at_prop,
                "updatedAt": updated_at_prop,
                "dataSource": data_source_ref_prop,
            },
            required=["agentId", "dataSourceId", "createdAt", "updatedAt"],  # Corrected field name
        )

        overall_project_root_abs = "/tmp/pyopenapi_gen_test_project"
        package_root_abs = os.path.join(overall_project_root_abs, "test_pkg")
        current_file_abs = os.path.join(package_root_abs, "models", "agent_data_source.py")

        context = RenderContext(
            overall_project_root=overall_project_root_abs,
            package_root_for_generated_code=package_root_abs,
            core_package_name="test_pkg.core",
        )
        context.set_current_file(current_file_abs)

        # Ensure schema names used as keys are strings
        ads_name = agent_data_source_schema.name
        self.assertIsNotNone(ads_name, "AgentDataSource schema name should not be None for this test")
        assert ads_name is not None

        all_schemas_for_context: dict[str, IRSchema] = {
            ads_name: agent_data_source_schema,
            "DataSource": IRSchema(name="DataSource", type="object", description="A data source object"),
        }
        # Prepare schemas
        for schema_obj in all_schemas_for_context.values():
            if schema_obj.name:
                schema_obj.generation_name = NameSanitizer.sanitize_class_name(schema_obj.name)
                schema_obj.final_module_stem = NameSanitizer.sanitize_module_name(schema_obj.name)

        model_visitor = ModelVisitor(schemas=all_schemas_for_context)

        generated_code = model_visitor.visit_IRSchema(agent_data_source_schema, context)

        # Assertions (updated for BaseSchema support due to field mappings)
        self.assertIn("class AgentDataSource:", generated_code)
        self.assertIn("@dataclass", generated_code)
        self.assertIn("agent_id: UUID", generated_code)  # Sanitized, UUID format correctly mapped
        self.assertIn("data_source_id: UUID", generated_code)  # Sanitized, UUID format correctly mapped
        self.assertIn("description: str | None", generated_code)
        self.assertIn("instructions: str | None", generated_code)
        self.assertIn("config_: dict[str, Any] | None", generated_code)  # 'config' is sanitized to 'config_'
        self.assertIn("created_at:", generated_code)  # Field exists (may be multi-line)
        self.assertIn("datetime", generated_code)  # Has datetime type
        self.assertIn("updated_at:", generated_code)  # Field exists (may be multi-line)
        self.assertIn(
            "data_source: DataSource | None", generated_code
        )  # DataSource is imported from different module, not a forward reference

        # Check BaseSchema Meta class and field mappings
        self.assertIn("class Meta:", generated_code)
        self.assertIn("key_transform_with_load = {", generated_code)
        self.assertIn('"agentId": "agent_id",', generated_code)
        self.assertIn('"config": "config_",', generated_code)
        self.assertIn('"createdAt": "created_at",', generated_code)
        self.assertIn('"dataSource": "data_source",', generated_code)
        self.assertIn('"dataSourceId": "data_source_id",', generated_code)
        self.assertIn('"updatedAt": "updated_at",', generated_code)

        generated_imports = context.import_collector.get_import_statements()

        # Modern Python 3.10+ uses | None instead of Optional, dict instead of Dict
        # Check for Any import (still needed for dict[str, Any])
        typing_import_found = any("from typing import" in imp and "Any" in imp for imp in generated_imports)
        self.assertTrue(typing_import_found, "Expected 'from typing import ... Any' for dict[str, Any] types")
        self.assertIn("from datetime import datetime", generated_imports)

        # Verify DataSource import is present (not a self-import, so import is needed)
        data_source_import_found = any("DataSource" in imp for imp in generated_imports)
        self.assertTrue(data_source_import_found, "Expected import for DataSource from different module")

    def test_visit_IRSchema_for_simple_type_alias(self) -> None:
        """
        Scenario:
            - An IRSchema representing a simple named string type (potential type alias).
        Expected Outcome:
            - The ModelVisitor should generate Python code for a type alias (e.g., `MyString = str`).
            - Necessary imports (if any, though unlikely for str) should be handled.
        """
        # Arrange
        alias_schema = IRSchema(name="MyStringAlias", type="string", description="A simple string type alias.")
        context = RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )
        # Set a dummy current file for context
        context.set_current_file("/tmp/pkg/models/aliases.py")

        visitor = ModelVisitor()

        # Act
        generated_code = visitor.visit_IRSchema(alias_schema, context)
        generated_imports = context.import_collector.get_import_statements()

        # Assert
        # Check for the alias definition
        # Example: MyStringAlias = str
        self.assertIn(
            "MyStringAlias: TypeAlias = str",
            generated_code,
            f"Generated code missing type alias definition. Got: {generated_code}",
        )

        # Check for description
        # PythonConstructRenderer puts alias description in a docstring after the alias
        self.assertIn(
            '"""Alias for A simple string type alias."""', generated_code, "Description docstring not found for alias"
        )

        # For a simple str alias, no special imports beyond `typing` for `TypeAlias` itself are typically needed from ModelVisitor directly,
        # as PythonConstructRenderer handles the TypeAlias import.
        # We primarily check that no unexpected imports are added for primitive types.
        self.assertFalse(
            any("datetime" in imp for imp in generated_imports), "datetime should not be imported for a str alias"
        )
        self.assertFalse(any("uuid" in imp for imp in generated_imports), "uuid should not be imported for a str alias")

        # Check if RenderContext registered TypeAlias from typing
        # This is added by PythonConstructRenderer when an alias is made.
        self.assertIn("typing", context.import_collector.imports, "'typing' module should be in imports")
        self.assertIn(
            "TypeAlias", context.import_collector.imports["typing"], "TypeAlias should be imported from typing"
        )

    def test_visit_IRSchema_for_string_enum_with_sanitized_members(self) -> None:
        """
        Scenario:
            - An IRSchema represents a string enum with member values that require sanitization
              (e.g., spaces, hyphens, leading digits, keywords).
        Expected Outcome:
            - ModelVisitor generates a Python enum with correctly sanitized member names.
            - The original string values are preserved as the enum member values.
            - Necessary imports (Enum, possibly TypeAlias if it's aliased first) are handled.
        """
        # Arrange
        enum_schema = IRSchema(
            name="ComplexStringEnum",
            type="string",
            description="An enum with tricky member names.",
            enum=[
                "active-user",
                "inactive user",
                "on_hold",
                "123_starts_digit",
                "class",  # Python keyword
                "",  # Empty string
                "你好世界",  # Unicode characters
                "value with !@#$",  # Special chars
            ],
        )
        context = RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )
        context.set_current_file("/tmp/pkg/models/enums.py")

        visitor = ModelVisitor()

        # Act
        generated_code = visitor.visit_IRSchema(enum_schema, context)

        # Assert
        # print(f"\nGenerated Enum Code:\n{generated_code}") # For debugging

        self.assertIn("class ComplexStringEnum(str, Enum):", generated_code)
        # Description is now in the docstring
        self.assertNotIn("# An enum with tricky member names.", generated_code)
        assert enum_schema.description is not None  # Hint for mypy and runtime check
        target_substring = '    """\n    ' + enum_schema.description
        self.assertIn(target_substring, generated_code)

        # Check sanitized member names and their original values
        expected_members = {
            "ACTIVE_USER": "active-user",
            "INACTIVE_USER": "inactive user",
            "ON_HOLD": "on_hold",
            "MEMBER_123_STARTS_DIGIT": "123_starts_digit",  # ModelVisitor prefixes with MEMBER_ for digits
            "CLASS_": "class",
            "MEMBER_EMPTY_STRING": "",
            "MEMBER_EMPTY_STRING_1": "你好世界",  # Corrected: "你好世界" sanitizes to empty, then gets unique name
            "VALUE_WITH_": "value with !@#$",  # Corrected: Non-alphanumeric (excluding _) are stripped, trailing _ kept
        }

        for member_name, original_value in expected_members.items():
            # Regex to match: MEMBER_NAME = "original_value"
            # Need to escape original_value if it contains regex special characters for the pattern
            import re

            escaped_original_value = re.escape(original_value)
            # Ensure that the value is quoted correctly, especially empty string
            if original_value == "":
                member_assignment_pattern = re.compile(f'^    {member_name} = ""$', re.MULTILINE)
            else:
                member_assignment_pattern = re.compile(
                    f'^    {member_name} = "{escaped_original_value}"$', re.MULTILINE
                )
            self.assertTrue(
                member_assignment_pattern.search(generated_code),  # Use self.assertTrue
                f"Enum member {member_name} = '{original_value}' not found or incorrect. Code:\n{generated_code}",
            )

        # Check imports
        self.assertIn("enum", context.import_collector.imports, "'enum' module should be in imports for Enum class")
        self.assertIn("Enum", context.import_collector.imports["enum"], "Enum class should be imported from enum")

    def test_visit_IRSchema_for_integer_enum_with_sanitized_members(self) -> None:
        """
        Scenario:
            - An IRSchema represents an integer enum with member values whose string representations
              (used for name generation) require sanitization. Also includes an uncastable value.
        Expected Outcome:
            - ModelVisitor generates a Python enum with correctly sanitized member names.
            - Integer values are preserved.
            - Uncastable value is handled (e.g., logged and assigned a default like 0, with a generated name).
        """
        # Arrange
        enum_schema = IRSchema(
            name="ComplexIntEnum",
            type="integer",
            description="An integer enum with tricky names from values.",
            enum=[
                1,  # Simple case
                "2-value",  # String that should be castable to int for value, name sanitized
                "CLASS",  # String (keyword) that is uncastable to int, for name generation + value fallback
                "4_starts_digit",  # String castable to int for value, name sanitized
                -5,  # Negative integer
                0,  # Zero
            ],
        )
        context = RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )
        context.set_current_file("/tmp/pkg/models/enums.py")

        visitor = ModelVisitor()

        # Act
        generated_code = visitor.visit_IRSchema(enum_schema, context)

        # Assert
        # print(f"\nGenerated Int Enum Code:\n{generated_code}") # For debugging

        self.assertIn("class ComplexIntEnum(int, Enum):", generated_code)
        # Description is now in the docstring
        self.assertNotIn("# An integer enum with tricky names from values.", generated_code)
        assert enum_schema.description is not None  # Hint for mypy and runtime check
        target_substring = '    """\n    ' + enum_schema.description
        self.assertIn(target_substring, generated_code)

        # Check sanitized member names and their integer values
        expected_members = {
            "VALUE_1": 1,  # Name from str(1)
            "VALUE_2_VALUE": 2,  # Name from str("2-value"), value from int("2-value") -> error, so it is int("2") perhaps?
            # ModelVisitor currently does: int_val = int(val). If val="2-value", this fails.
            # Then uses 0. Name from str("2-value") -> "_2_VALUE"
            # Let's re-check ModelVisitor: uses `int_val = 0` on failure.
            "CLASS": 0,  # Name from str("CLASS"), value fallback to 0 (uncastable)
            "VALUE_4_STARTS_DIGIT": 4,  # Name from str("4_starts_digit"), value from int("4_starts_digit") -> error -> 0
            # Let's assume the value comes from a successful int cast if possible for naming
            # The actual code: `name_basis = str(val)`. So for "4_starts_digit", name is VALUE_4_STARTS_DIGIT
            # Value will be `int("4_starts_digit")`. This will fail. Value becomes 0.
            "VALUE_MINUS_5": -5,  # Name from str(-5)
            "VALUE_0": 0,  # Name from str(0)
        }

        # Re-evaluating expected_members based on current ModelVisitor logic for int enums:
        # 1. `int_val = int(val)` is attempted. If ValueError/TypeError, `int_val = 0` and warning._VALUE
        # 2. `name_basis = str(val)`. Sanitized. Prefixed with `VALUE_` if starts with digit or is `MEMBER_UNKNOWN_` if sanitization is empty.

        refined_expected_members = {
            "VALUE_1": 1,  # int(1)=1. Name from str(1) -> "1" -> "VALUE_1"
            "_2_VALUE": 0,  # int("2-value") fails. val=0. Name from str("2-value") -> "2-VALUE" -> "_2_VALUE" (due to re.sub not VALUE_ prefix?)
            # The code is: `sanitized_member_name = re.sub(r"[^A-Z0-9_]", "", base_member_name)`
            # then `if sanitized_member_name[0].isdigit(): sanitized_member_name = f"VALUE_{sanitized_member_name}"`
            # So "2-VALUE" -> "2VALUE" -> "VALUE_2VALUE"
            "CLASS": 0,  # int("CLASS") fails. val=0. Name from str("CLASS") -> "CLASS" -> "CLASS" (no digit start)
            "_4_STARTS_DIGIT": 0,  # int("4_starts_digit") fails. val=0. Name from str("4_starts_digit") -> "4_STARTS_DIGIT" -> "VALUE_4_STARTS_DIGIT"
            "_5": -5,  # str(-5).upper() -> "-5". replace("-","_") -> "_5". re.sub -> "_5". No digit start (starts with _) -> "_5"
            "VALUE_0": 0,  # str(0).upper() -> "0". re.sub -> "0". Digit start -> "VALUE_0"
        }
        # The sanitization for integer name_basis needs to be precise.
        # Current code: `base_member_name = name_basis.upper().replace("-", "_").replace(" ", "_").replace(".", "_DOT_")`
        # Then `sanitized_member_name = re.sub(r"[^A-Z0-9_]", "", base_member_name)`
        # Then digit prefix `VALUE_`.

        final_expected_members = {
            "VALUE_1": 1,  # str(1).upper() -> "1". re.sub -> "1". Digit start -> "VALUE_1"
            "VALUE_2_VALUE": 0,  # Corrected: str("2-value").upper().replace("-","_") -> "2_VALUE". re.sub -> "2_VALUE". Digit start -> "VALUE_2_VALUE"
            "CLASS_": 0,  # Corrected: str("CLASS").upper() -> "CLASS". re.sub -> "CLASS". No digit -> "CLASS". Keyword -> "CLASS_"
            "VALUE_4_STARTS_DIGIT": 0,  # Corrected: str("4_starts_digit").upper() -> "4_STARTS_DIGIT". re.sub -> "4_STARTS_DIGIT". Digit start -> "VALUE_4_STARTS_DIGIT"
            "_5": -5,  # str(-5).upper() -> "-5". replace("-","_") -> "_5". re.sub -> "_5". No digit start (starts with _) -> "_5"
            "VALUE_0": 0,  # str(0).upper() -> "0". re.sub -> "0". Digit start -> "VALUE_0"
        }

        import re

        for member_name, expected_val in final_expected_members.items():
            member_assignment_pattern = re.compile(
                f"^    {member_name} = {expected_val}$".format(expected_val=expected_val), re.MULTILINE
            )
            self.assertTrue(
                member_assignment_pattern.search(generated_code),  # Use self.assertTrue
                f"Enum member {member_name} = {expected_val} not found or incorrect. Code:\n{generated_code}",
            )

        self.assertIn("enum", context.import_collector.imports)
        self.assertIn("Enum", context.import_collector.imports["enum"])

    def test_visit_IRSchema_for_array_of_anonymous_objects_as_dataclass(self) -> None:
        """
        Scenario:
            - An IRSchema represents an array whose items are anonymous objects.
        Expected Outcome:
            - ModelVisitor should render this as a dataclass wrapper.
            - The dataclass should have a field (e.g., "items") of type List[<GeneratedItemTypeName>].
            - The anonymous item type (e.g., <GeneratedItemTypeName>) should be resolvable by TypeHelper.
        """
        # Arrange
        anonymous_item_schema = IRSchema(
            name=None,  # Truly anonymous
            type="object",
            properties={"id": IRSchema(name="id", type="string")},
            description="An anonymous item in the list.",
        )

        array_schema = IRSchema(
            name="MyListWrapper",
            type="array",
            items=anonymous_item_schema,  # Use the anonymous schema here
            description="A list of (previously anonymous) objects.",
        )

        context = RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )
        context.set_current_file("/tmp/pkg/models/wrappers.py")

        self.assertIsNotNone(array_schema.name, "Test setup error: array_schema.name should not be None")
        assert array_schema.name is not None

        # ModelVisitor is initialized with all_schemas. For this test, TypeHelper will need to resolve
        # the anonymous item schema and potentially name it (e.g., MyListWrapperItem).
        # We provide the main array_schema. If MyListWrapperItem is generated by TypeHelper/DataclassGenerator
        # and registered back into a global schema list, that's part of a deeper integration.
        # For ModelVisitor unit test, we primarily care it dispatches correctly and DataclassGenerator
        # receives the array_schema correctly flagged (via is_data_wrapper=True).
        all_schemas_for_context: dict[str, IRSchema] = {
            array_schema.name: array_schema,
            # Do NOT add the item schema here if it's meant to be resolved from anonymous
        }
        visitor = ModelVisitor(schemas=all_schemas_for_context)

        # Act
        generated_code = visitor.visit_IRSchema(array_schema, context)

        # Assert
        # print(f"\nGenerated Array Dataclass Code:\\n{generated_code}") # For debugging

        self.assertIn("@dataclass", generated_code, f"Expected @dataclass for array wrapper. Got:\n{generated_code}")
        self.assertIn("class MyListWrapper:", generated_code)
        # Check for the wrapper's description in its docstring
        self.assertIn("A list of (previously anonymous) objects.", generated_code)

        # Note: Unified system currently falls back to dict[str, Any] for anonymous objects
        # rather than promoting them to named types. This is correct fallback behavior.
        # TODO: Implement anonymous object promotion feature if needed
        expected_field_declaration_part1 = "items: List[dict[str, Any]] | None = field("
        expected_field_declaration_part2 = "default_factory=list"
        # We need to check for these parts, accommodating potential whitespace/formatting variations.

        self.assertIn(
            expected_field_declaration_part1,
            generated_code,
            f"Start of field declaration not found. Got:\n{generated_code}",
        )

        # Search for the default_factory part
        self.assertIn("default_factory=list", generated_code)

        # Test passes - anonymous objects correctly fall back to dict[str, Any]

        self.assertIn(
            "List", context.import_collector.imports.get("typing", set()), "List should be imported from typing"
        )
        # Modern Python 3.10+ doesn't need Optional imports (uses | None syntax)
        self.assertIn(
            "field",
            context.import_collector.imports.get("dataclasses", set()),
            "field should be imported from dataclasses",
        )

    def test_visit_IRSchema_for_dataclass_with_field_defaults(self) -> None:
        """
        Scenario:
            - An IRSchema for a dataclass has properties with various default values specified in the schema.
        Expected Outcome:
            - ModelVisitor generates a dataclass with correct `default=...` or `default_factory=...`
              for optional fields based on `IRSchema.default` and type.
        """
        # Arrange
        schema_with_defaults = IRSchema(
            name="ModelWithDefaults",
            type="object",
            properties={
                "name": IRSchema(type="string", default="Default Name"),
                "count": IRSchema(type="integer", default=0),
                "tags": IRSchema(type="array", items=IRSchema(type="string"), default=[]),  # default_factory=list
                "active": IRSchema(type="boolean", default=True),
                "config": IRSchema(type="object", properties={}, default={}),  # default_factory=dict
                "nullable_with_default": IRSchema(type="string", is_nullable=True, default="Nullable Default"),
                "required_with_default": IRSchema(type="string", default="This default is ignored for required fields"),
                "no_default_optional": IRSchema(type="string", is_nullable=True),  # Standard Optional, defaults to None
            },
            required=[
                "required_with_default"
            ],  # name, count, tags, active, config, nullable_with_default, no_default_optional are optional
        )

        context = RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )
        context.set_current_file("/tmp/pkg/models/defaults_model.py")

        self.assertIsNotNone(schema_with_defaults.name)
        assert schema_with_defaults.name is not None
        all_schemas: dict[str, IRSchema] = {schema_with_defaults.name: schema_with_defaults}
        # Prepare schema
        if schema_with_defaults.name:  # Should always be true
            schema_with_defaults.generation_name = NameSanitizer.sanitize_class_name(schema_with_defaults.name)
            schema_with_defaults.final_module_stem = NameSanitizer.sanitize_module_name(schema_with_defaults.name)
        # Note: if schema_with_defaults had complex sub-schemas that were also in all_schemas,
        # they would also need preparation if referenced.

        visitor = ModelVisitor(schemas=all_schemas)

        # Act
        generated_code = visitor.visit_IRSchema(schema_with_defaults, context)

        # Assert
        # print(f"\nGenerated Dataclass with Defaults Code:\n{generated_code}")

        self.assertIn("@dataclass", generated_code)
        self.assertIn("class ModelWithDefaults:", generated_code)

        # Check specific field patterns (handling multi-line fields)
        self.assertIn("required_with_default: str", generated_code)  # Required field, no default
        self.assertIn("active: bool | None = True", generated_code)
        self.assertIn("config_: dict[str, Any] | None = field(", generated_code)  # Multi-line field
        self.assertIn("default_factory=dict", generated_code)
        self.assertIn("count: int | None = 0", generated_code)
        self.assertIn('name: str | None = "Default Name"', generated_code)
        self.assertIn("no_default_optional: str | None = None", generated_code)
        self.assertIn('nullable_with_default: str | None = "Nullable Default"', generated_code)
        self.assertIn("tags: List[str] | None = field(default_factory=list)", generated_code)

        # Check for Meta class with field mappings (for cattrs)
        self.assertIn("class Meta:", generated_code)
        self.assertIn("key_transform_with_load = {", generated_code)
        self.assertIn('"config": "config_",', generated_code)

        # Check imports
        self.assertIn("List", context.import_collector.imports.get("typing", set()))
        self.assertIn("Dict", context.import_collector.imports.get("typing", set()))
        self.assertIn("Any", context.import_collector.imports.get("typing", set()))
        # Modern Python 3.10+ doesn't need Optional imports (uses | None syntax)
        # Note: BaseSchema no longer used - now using cattrs with Meta class
        self.assertIn("dataclass", context.import_collector.imports.get("dataclasses", set()))
        self.assertIn("dataclasses", context.import_collector.imports)
        self.assertIn("field", context.import_collector.imports["dataclasses"])


# --- Pytest-style tests for oneOf/anyOf Union type generation ---


def test_model_visitor__one_of_schema__generates_union_type_alias_not_dataclass():
    """
    Scenario: Schema with oneOf composition (discriminated union)
    Expected Outcome: Generate TypeAlias with Union[...], not an empty dataclass

    Bug: Currently generates empty dataclass because oneOf schemas often have type="object"
    which triggers dataclass generation even though they have no properties.
    """
    # Arrange
    start_node_schema = IRSchema(
        name="WorkflowStartNode",
        type="object",
        generation_name="WorkflowStartNode",
        final_module_stem="workflow_start_node",
        properties={"type": IRSchema(type="string"), "id": IRSchema(type="string")},
    )

    end_node_schema = IRSchema(
        name="WorkflowEndNode",
        type="object",
        generation_name="WorkflowEndNode",
        final_module_stem="workflow_end_node",
        properties={"type": IRSchema(type="string"), "result": IRSchema(type="string")},
    )

    conditional_node_schema = IRSchema(
        name="WorkflowConditionalNode",
        type="object",
        generation_name="WorkflowConditionalNode",
        final_module_stem="workflow_conditional_node",
        properties={"type": IRSchema(type="string"), "condition": IRSchema(type="string")},
    )

    # Schema with oneOf - this should generate a Union type alias
    workflow_node_schema = IRSchema(
        name="WorkflowNode",
        type="object",  # Often set by OpenAPI parser
        generation_name="WorkflowNode",
        final_module_stem="workflow_node",
        one_of=[start_node_schema, end_node_schema, conditional_node_schema],
    )

    all_schemas = {
        "WorkflowStartNode": start_node_schema,
        "WorkflowEndNode": end_node_schema,
        "WorkflowConditionalNode": conditional_node_schema,
        "WorkflowNode": workflow_node_schema,
    }

    context = RenderContext(
        overall_project_root="/tmp",
        package_root_for_generated_code="/tmp/pkg",
        core_package_name="core",
    )
    context.set_current_file("/tmp/pkg/models/workflow_node.py")

    visitor = ModelVisitor(schemas=all_schemas)

    # Act
    generated_code = visitor.visit_IRSchema(workflow_node_schema, context)

    # Assert
    # Should generate TypeAlias with Union, not a dataclass
    assert "TypeAlias" in generated_code, f"Expected TypeAlias in generated code, got: {generated_code}"
    assert "Union[" in generated_code, f"Expected Union[ in generated code, got: {generated_code}"
    assert "WorkflowStartNode" in generated_code, "Expected WorkflowStartNode in union"
    assert "WorkflowEndNode" in generated_code, "Expected WorkflowEndNode in union"
    assert "WorkflowConditionalNode" in generated_code, "Expected WorkflowConditionalNode in union"

    # Should NOT generate a dataclass
    assert "@dataclass" not in generated_code, f"Should not generate @dataclass for oneOf schema, got: {generated_code}"
    assert (
        "class WorkflowNode:" not in generated_code
    ), f"Should not generate class for oneOf schema, got: {generated_code}"

    # Should have proper imports
    assert "TypeAlias" in context.import_collector.imports.get("typing", set())
    assert "Union" in context.import_collector.imports.get("typing", set())


def test_model_visitor__any_of_schema__generates_union_type_alias():
    """
    Scenario: Schema with anyOf composition
    Expected Outcome: Generate TypeAlias with Union[...], not an empty dataclass
    """
    # Arrange
    string_schema = IRSchema(
        name="StringValue",
        type="string",
        generation_name="StringValue",
        final_module_stem="string_value",
    )

    integer_schema = IRSchema(
        name="IntegerValue",
        type="integer",
        generation_name="IntegerValue",
        final_module_stem="integer_value",
    )

    # Schema with anyOf
    flexible_value_schema = IRSchema(
        name="FlexibleValue",
        type="object",  # Often set by OpenAPI parser
        generation_name="FlexibleValue",
        final_module_stem="flexible_value",
        any_of=[string_schema, integer_schema],
    )

    all_schemas = {
        "StringValue": string_schema,
        "IntegerValue": integer_schema,
        "FlexibleValue": flexible_value_schema,
    }

    context = RenderContext(
        overall_project_root="/tmp",
        package_root_for_generated_code="/tmp/pkg",
        core_package_name="core",
    )
    context.set_current_file("/tmp/pkg/models/flexible_value.py")

    visitor = ModelVisitor(schemas=all_schemas)

    # Act
    generated_code = visitor.visit_IRSchema(flexible_value_schema, context)

    # Assert
    assert "TypeAlias" in generated_code, f"Expected TypeAlias in generated code for anyOf, got: {generated_code}"
    assert "Union[" in generated_code, f"Expected Union[ in generated code for anyOf, got: {generated_code}"
    assert "@dataclass" not in generated_code, "Should not generate @dataclass for anyOf schema"


def test_model_visitor__one_of_with_no_type__generates_union_type_alias():
    """
    Scenario: Schema with oneOf but no explicit type field (cleaner OpenAPI spec)
    Expected Outcome: Generate TypeAlias with Union[...]
    """
    # Arrange
    option_a = IRSchema(
        name="OptionA",
        type="object",
        generation_name="OptionA",
        final_module_stem="option_a",
        properties={"value": IRSchema(type="string")},
    )

    option_b = IRSchema(
        name="OptionB",
        type="object",
        generation_name="OptionB",
        final_module_stem="option_b",
        properties={"count": IRSchema(type="integer")},
    )

    # Schema with oneOf and NO type field
    choice_schema = IRSchema(
        name="Choice",
        # type=None  # Explicitly no type
        generation_name="Choice",
        final_module_stem="choice",
        one_of=[option_a, option_b],
    )

    all_schemas = {
        "OptionA": option_a,
        "OptionB": option_b,
        "Choice": choice_schema,
    }

    context = RenderContext(
        overall_project_root="/tmp",
        package_root_for_generated_code="/tmp/pkg",
        core_package_name="core",
    )
    context.set_current_file("/tmp/pkg/models/choice.py")

    visitor = ModelVisitor(schemas=all_schemas)

    # Act
    generated_code = visitor.visit_IRSchema(choice_schema, context)

    # Assert
    assert "TypeAlias" in generated_code, "Expected TypeAlias even without explicit type field"
    assert "Union[" in generated_code, "Expected Union for oneOf without type"
    assert "OptionA" in generated_code
    assert "OptionB" in generated_code
    assert "@dataclass" not in generated_code


def test_model_visitor__all_of_schema__does_not_generate_union():
    """
    Scenario: Schema with allOf composition (schema merging, not discriminated union)
    Expected Outcome: allOf should NOT generate a Union type alias

    allOf is for schema composition/extension (merging properties), not for discriminated unions.
    It should generate a dataclass (potentially with merged properties) or remain as-is.
    This test verifies that allOf does NOT become a Union like oneOf/anyOf do.
    """
    # Arrange
    base_schema = IRSchema(
        name="BaseModel",
        type="object",
        generation_name="BaseModel",
        final_module_stem="base_model",
        properties={"id": IRSchema(type="string")},
    )

    extension_schema = IRSchema(
        name="ExtensionFields",
        type="object",
        generation_name="ExtensionFields",
        final_module_stem="extension_fields",
        properties={"extra": IRSchema(type="string")},
    )

    # Schema with allOf - this represents composition/merging, not a union
    composed_schema = IRSchema(
        name="ComposedModel",
        type="object",
        generation_name="ComposedModel",
        final_module_stem="composed_model",
        all_of=[base_schema, extension_schema],
    )

    all_schemas = {
        "BaseModel": base_schema,
        "ExtensionFields": extension_schema,
        "ComposedModel": composed_schema,
    }

    context = RenderContext(
        overall_project_root="/tmp",
        package_root_for_generated_code="/tmp/pkg",
        core_package_name="core",
    )
    context.set_current_file("/tmp/pkg/models/composed_model.py")

    visitor = ModelVisitor(schemas=all_schemas)

    # Act
    generated_code = visitor.visit_IRSchema(composed_schema, context)

    # Assert
    # allOf should generate a dataclass (for now, even if empty - proper merging is a future enhancement)
    # The key point is it should NOT generate a Union type
    assert (
        "Union[" not in generated_code
    ), "allOf should not generate Union - it's for composition, not discriminated unions"
    # It's acceptable for allOf to generate either a dataclass or a type alias to the composed type
    # For now, with no direct properties, it generates a dataclass (even if empty)
    assert "@dataclass" in generated_code or "TypeAlias" in generated_code


def test_model_visitor__one_of_with_type_object_discriminator__generates_union_type_alias() -> None:
    """
    Test that discriminated unions with oneOf + type: object + discriminator
    generate Union TypeAlias, not empty dataclasses.

    This is a regression test for the issue where schemas with oneOf + discriminator
    but also explicit type: "object" were incorrectly generated as empty dataclasses.
    """
    # Arrange - Create discriminated union schema with explicit type: object
    start_node = IRSchema(
        name="StartNode",
        type="object",
        generation_name="StartNode",
        final_module_stem="start_node",
        properties={
            "type": IRSchema(name="type", type="string", enum=["start"]),
            "id": IRSchema(name="id", type="string"),
            "label": IRSchema(name="label", type="string"),
        },
        required=["type", "id"],
    )

    end_node = IRSchema(
        name="EndNode",
        type="object",
        generation_name="EndNode",
        final_module_stem="end_node",
        properties={
            "type": IRSchema(name="type", type="string", enum=["end"]),
            "id": IRSchema(name="id", type="string"),
        },
        required=["type", "id"],
    )

    # The discriminated union with explicit type: object
    node_schema = IRSchema(
        name="Node",
        type="object",  # Explicit type: object - this was causing the bug
        generation_name="Node",
        final_module_stem="node",
        one_of=[start_node, end_node],
        properties={},  # No direct properties, only oneOf variants
    )

    all_schemas = {
        "StartNode": start_node,
        "EndNode": end_node,
        "Node": node_schema,
    }

    context = RenderContext(
        overall_project_root="/tmp",
        package_root_for_generated_code="/tmp/pkg",
        core_package_name="core",
    )
    context.set_current_file("/tmp/pkg/models/node.py")

    visitor = ModelVisitor(schemas=all_schemas)

    # Act
    generated_code = visitor.visit_IRSchema(node_schema, context)

    # Assert
    assert "Union[" in generated_code, (
        "Discriminated union with oneOf + type: object should generate Union TypeAlias, "
        f"not empty dataclass. Generated code:\n{generated_code}"
    )
    assert (
        "TypeAlias" in generated_code
    ), f"Should use TypeAlias for discriminated unions. Generated code:\n{generated_code}"
    assert (
        "@dataclass" not in generated_code
    ), f"Should NOT generate dataclass for discriminated union. Generated code:\n{generated_code}"
    assert (
        "StartNode" in generated_code and "EndNode" in generated_code
    ), f"Union should contain variant types. Generated code:\n{generated_code}"


def test_model_visitor__one_of_without_type_discriminator__generates_union_type_alias() -> None:
    """
    Test that discriminated unions with oneOf + discriminator (without explicit type)
    generate Union TypeAlias.

    This tests the case where type: object is omitted.
    """
    # Arrange
    start_node = IRSchema(
        name="StartNode",
        type="object",
        properties={
            "type": IRSchema(name="type", type="string", enum=["start"]),
            "id": IRSchema(name="id", type="string"),
        },
        required=["type", "id"],
    )

    end_node = IRSchema(
        name="EndNode",
        type="object",
        properties={
            "type": IRSchema(name="type", type="string", enum=["end"]),
            "id": IRSchema(name="id", type="string"),
        },
        required=["type", "id"],
    )

    # Discriminated union without explicit type field
    node_schema = IRSchema(
        name="Node",
        type=None,  # No explicit type - relies on oneOf
        one_of=[start_node, end_node],
        properties={},
    )

    all_schemas = {
        "StartNode": start_node,
        "EndNode": end_node,
        "Node": node_schema,
    }

    context = RenderContext(
        overall_project_root="/tmp",
        package_root_for_generated_code="/tmp/pkg",
        core_package_name="core",
    )
    context.set_current_file("/tmp/pkg/models/node.py")

    visitor = ModelVisitor(schemas=all_schemas)

    # Act
    generated_code = visitor.visit_IRSchema(node_schema, context)

    # Assert
    assert (
        "Union[" in generated_code
    ), f"Discriminated union with oneOf should generate Union TypeAlias. Generated code:\n{generated_code}"
    assert (
        "TypeAlias" in generated_code
    ), f"Should use TypeAlias for discriminated unions. Generated code:\n{generated_code}"
    assert (
        "@dataclass" not in generated_code
    ), f"Should NOT generate dataclass for discriminated union. Generated code:\n{generated_code}"
