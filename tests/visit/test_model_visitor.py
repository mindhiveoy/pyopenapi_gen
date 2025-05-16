import os  # For path manipulation

# from pyopenapi_gen.model.ir_schema import IRSchema, IRSchemaType # Old incorrect import
from pyopenapi_gen import IRSchema  # Corrected import
from pyopenapi_gen.context.render_context import RenderContext

# CodeWriter is not directly used by the test calling ModelVisitor, but ModelVisitor uses
# PythonConstructRenderer which uses CodeWriter from pyopenapi_gen.utils.code_writer import
# CodeWriter
from pyopenapi_gen.visit.model_visitor import ModelVisitor

# from pyopenapi_gen.utils.log_utils import setup_logging # This path is incorrect, removing for now

# Setup logging for tests if needed
# setup_logging(level="DEBUG")


class TestModelVisitor:
    def test_clean_field_type(self):
        """
        Scenario:
            - Test the clean_field_type method of ModelVisitor
            - Provide various type strings with invalid None parameters
            
        Expected Outcome:
            - The method should correctly clean the type strings
            - It should handle different patterns of invalid None parameters
        """
        # Arrange
        model_visitor = ModelVisitor()
        
        # Test cases
        test_cases = [
            # Input type string, Expected output
            ("Dict[str, Any, None]", "Dict[str, Any]"),
            ("List[str, None]", "List[str]"),
            ("Optional[int, None]", "Optional[int]"),
            ("Union[str, int, None]", "Union[str, int, None]"),  # This is valid, should be unchanged
            ("Dict[str, List[str, None]]", "Dict[str, List[str]]"),
            ("List[Dict[str, Any, None]]", "List[Dict[str, Any]]"),
            ("Optional[Dict[str, Any, None]]", "Optional[Dict[str, Any]]"),
        ]
        
        # Act & Assert
        for input_type, expected_output in test_cases:
            result = model_visitor.clean_field_type(input_type)
            assert result == expected_output, f"Failed to clean '{input_type}' correctly"

    def test_model_visitor_handles_openapi_31_nullable_types(self):
        """
        Scenario:
            - Create a schema with a property that uses OpenAPI 3.1 style nullable types
            - Generate a model using the ModelVisitor
            
        Expected Outcome:
            - The ModelVisitor should generate the model with proper Optional types
            - Invalid None parameters should be cleaned from the type annotations
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
                    is_nullable=True,  # This should be rendered as Optional[Dict[str, Any]]
                )
            }
        )
        
        context = RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )
        
        visitor = ModelVisitor()
        
        # Mock the TypeHelper to return a type with invalid None parameter
        # (normally this would come from the schema parser)
        from unittest.mock import patch
        
        with patch('pyopenapi_gen.helpers.type_helper.TypeHelper.get_python_type_for_schema', 
                  return_value="Dict[str, Any, None]"):  # Return invalid type
            # Act
            result = visitor.visit_IRSchema(schema, context)
            
            # Assert
            assert "config: Optional[Dict[str, Any]]" in result, \
                "Failed to clean type with invalid None parameter"
            assert "Dict[str, Any, None]" not in result, \
                "Invalid type with None parameter was not cleaned"

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
            additional_properties=True,  # Allows Dict[str, Any] behavior if TypeHelper maps this
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
        assert ads_name is not None, "AgentDataSource schema name should not be None for this test"

        all_schemas_for_context = {
            ads_name: agent_data_source_schema,  # Now ads_name is confirmed str
            "DataSource": IRSchema(name="DataSource", type="object", description="A data source object"),
        }
        model_visitor = ModelVisitor(schemas=all_schemas_for_context)

        generated_code = model_visitor.visit_IRSchema(agent_data_source_schema, context)

        # Assertions (mostly unchanged from previous correct version)
        assert "class AgentDataSource:" in generated_code
        assert "@dataclass" in generated_code
        assert "    agentId: str" in generated_code
        assert "    dataSourceId: str" in generated_code
        assert "    description: Optional[str]" in generated_code
        assert "    instructions: Optional[str]" in generated_code
        assert (
            "    config: Optional[Dict[str, Any]]" in generated_code
        )  # TypeHelper makes object with additionalProps to Dict[str,Any]
        assert "    createdAt: datetime" in generated_code
        assert "    updatedAt: datetime" in generated_code
        assert "    dataSource: Optional[DataSource]" in generated_code

        generated_imports = context.import_collector.get_import_statements(
            current_module_dot_path=context.get_current_module_dot_path(),
            package_root=context.package_root_for_generated_code,
            core_package_name_for_absolute_treatment=context.core_package_name,
        )

        typing_import_found = any(
            ("from typing import Optional, Dict, Any" in imp)
            or ("from typing import Any, Dict, Optional" in imp)
            or ("from typing import Dict, Any, Optional" in imp)
            for imp in generated_imports
        )
        assert typing_import_found, "Expected 'from typing import Optional, Dict, Any' (or permutation)"
        assert "from datetime import datetime" in generated_imports

        found_data_source_import = False
        for imp_statement in generated_imports:
            if "import DataSource" in imp_statement and imp_statement.startswith("from ."):
                found_data_source_import = True
                break
        assert found_data_source_import, (
            "Expected relative import for DataSource (e.g. from .data_source import DataSource)"
        )
