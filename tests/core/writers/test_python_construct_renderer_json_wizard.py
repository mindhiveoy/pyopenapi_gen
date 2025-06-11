"""
Unit tests for PythonConstructRenderer JSON Wizard functionality.

Scenario: Test the PythonConstructRenderer's ability to generate dataclasses
with JSONWizard inheritance and field mapping configuration.

Expected Outcome: Generated code includes JSONWizard inheritance and proper
field mapping configuration when needed.
"""

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer


class TestPythonConstructRendererJsonWizard:
    """Test PythonConstructRenderer JSON Wizard functionality."""

    def test_render_dataclass__no_field_mappings__generates_standard_dataclass(self):
        """
        Scenario: Render a dataclass without any field mappings.
        Expected Outcome: Standard dataclass without JSONWizard inheritance.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        context = RenderContext()
        fields = [
            ("name", "str", None, "User name"),
            ("age", "int", None, "User age"),
            ("email", "Optional[str]", "None", "User email"),
        ]

        # Act
        result = renderer.render_dataclass(
            class_name="User", fields=fields, description="User information", context=context
        )

        # Assert
        assert "class User:" in result
        assert "JSONWizard" not in result
        assert "key_transform_with_load" not in result
        assert "@dataclass" in result
        assert "name: str" in result
        assert "age: int" in result
        assert "email: Optional[str] = None" in result

    def test_render_dataclass__with_field_mappings__generates_json_wizard_dataclass(self):
        """
        Scenario: Render a dataclass with field mappings.
        Expected Outcome: Dataclass with JSONWizard inheritance and Meta class.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        context = RenderContext()
        fields = [
            ("first_name", "str", None, "First name (maps from 'firstName')"),
            ("last_name", "str", None, "Last name (maps from 'lastName')"),
            ("id_", "str", None, "User ID (maps from 'id')"),
        ]
        field_mappings = {"firstName": "first_name", "lastName": "last_name", "id": "id_"}

        # Act
        result = renderer.render_dataclass(
            class_name="User",
            fields=fields,
            description="User information",
            context=context,
            field_mappings=field_mappings,
        )

        # Assert
        assert "class User(JSONWizard):" in result
        assert "with automatic JSON field mapping" in result
        assert "class _(JSONWizard.Meta):" in result
        assert "key_transform_with_load = {" in result
        assert "'firstName': 'first_name'," in result
        assert "'id': 'id_'," in result
        assert "'lastName': 'last_name'," in result

    def test_render_dataclass__empty_field_mappings__generates_standard_dataclass(self):
        """
        Scenario: Render a dataclass with empty field mappings dict.
        Expected Outcome: Standard dataclass without JSONWizard inheritance.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        context = RenderContext()
        fields = [("name", "str", None, "User name")]
        field_mappings = {}

        # Act
        result = renderer.render_dataclass(
            class_name="User",
            fields=fields,
            description="User information",
            context=context,
            field_mappings=field_mappings,
        )

        # Assert
        assert "class User:" in result
        assert "JSONWizard" not in result
        assert "key_transform_with_load" not in result

    def test_render_dataclass__with_field_mappings__adds_proper_imports(self):
        """
        Scenario: Render a dataclass with field mappings and check imports.
        Expected Outcome: Both dataclass and JSONWizard imports are added.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        context = RenderContext()
        fields = [("first_name", "str", None, "First name")]
        field_mappings = {"firstName": "first_name"}

        # Act
        renderer.render_dataclass(
            class_name="User",
            fields=fields,
            description="User information",
            context=context,
            field_mappings=field_mappings,
        )

        # Assert
        imports = context.import_collector.imports
        assert "dataclasses" in imports
        assert "dataclass" in imports["dataclasses"]
        assert "dataclass_wizard" in imports
        assert "JSONWizard" in imports["dataclass_wizard"]

    def test_render_dataclass__no_field_mappings__only_dataclass_import(self):
        """
        Scenario: Render a standard dataclass and check imports.
        Expected Outcome: Only dataclass import is added, no JSONWizard import.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        context = RenderContext()
        fields = [("name", "str", None, "User name")]

        # Act
        renderer.render_dataclass(class_name="User", fields=fields, description="User information", context=context)

        # Assert
        imports = context.import_collector.imports
        assert "dataclasses" in imports
        assert "dataclass" in imports["dataclasses"]
        assert "dataclass_wizard" not in imports

    def test_render_dataclass__sorted_field_mappings__generates_deterministic_output(self):
        """
        Scenario: Render a dataclass with unsorted field mappings.
        Expected Outcome: Mappings are sorted in the output for consistency.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        context = RenderContext()
        fields = [("z_field", "str", None, None), ("a_field", "str", None, None)]
        field_mappings = {"zField": "z_field", "aField": "a_field"}

        # Act
        result = renderer.render_dataclass(
            class_name="Test", fields=fields, description="Test class", context=context, field_mappings=field_mappings
        )

        # Assert
        # Find the position of the two mappings
        a_field_pos = result.find("'aField': 'a_field',")
        z_field_pos = result.find("'zField': 'z_field',")

        # aField should come before zField (alphabetical order)
        assert a_field_pos < z_field_pos
        assert a_field_pos != -1
        assert z_field_pos != -1

    def test_render_dataclass__no_fields__generates_empty_class_without_json_wizard(self):
        """
        Scenario: Render a dataclass with no fields.
        Expected Outcome: Empty dataclass with pass statement, no JSONWizard.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        context = RenderContext()

        # Act
        result = renderer.render_dataclass(class_name="Empty", fields=[], description="Empty class", context=context)

        # Assert
        assert "class Empty:" in result
        assert "pass" in result or "No properties defined in schema" in result
        assert "JSONWizard" not in result

    def test_render_dataclass__single_field_mapping__generates_meta_class(self):
        """
        Scenario: Render a dataclass with a single field mapping.
        Expected Outcome: Meta class is generated even for single mapping.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        context = RenderContext()
        fields = [("user_id", "str", None, "User ID")]
        field_mappings = {"userId": "user_id"}

        # Act
        result = renderer.render_dataclass(
            class_name="User", fields=fields, description="User class", context=context, field_mappings=field_mappings
        )

        # Assert
        assert "class User(JSONWizard):" in result
        assert "class _(JSONWizard.Meta):" in result
        assert "'userId': 'user_id'," in result
