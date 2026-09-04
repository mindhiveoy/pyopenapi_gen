"""
Unit tests for PythonConstructRenderer dataclass functionality with cattrs.

Scenario: Test the PythonConstructRenderer's ability to generate dataclasses
with field mapping configuration for cattrs serialization.

Expected Outcome: Generated code uses standard dataclasses with Meta classes
for field mapping configuration when needed.
"""

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer
from pyopenapi_gen.ir import IRDiscriminator


class TestPythonConstructRendererBaseSchema:
    """Test PythonConstructRenderer BaseSchema functionality."""

    def test_render_dataclass__no_field_mappings__generates_base_schema_dataclass(self) -> None:
        """
        Scenario: Render a dataclass without any field mappings.
        Expected Outcome: BaseSchema dataclass without Meta class.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        context = RenderContext()
        fields = [
            ("name", "str", None, "User name"),
            ("age", "int", None, "User age"),
            ("email", "str | None", "None", "User email"),
        ]

        # Act
        result = renderer.render_dataclass(
            class_name="User", fields=fields, description="User information", context=context
        )

        # Assert
        assert "class User:" in result
        assert "key_transform_with_load" not in result  # No Meta class when no mappings
        assert "@dataclass" in result
        assert "name: str" in result
        assert "age: int" in result
        assert "email: str | None = None" in result

    def test_render_dataclass__with_field_mappings__generates_base_schema_dataclass(self) -> None:
        """
        Scenario: Render a dataclass with field mappings.
        Expected Outcome: Dataclass with BaseSchema inheritance and Meta class.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        context = RenderContext()
        fields = [
            ("first_name", "str", None, "First name (maps from 'firstName')"),
            ("last_name", "str", None, "Last name (maps from 'lastName')"),
            ("id_", "str", None, "User ID (maps from 'id')"),
        ]
        field_mappings: dict[str, str] = {"firstName": "first_name", "lastName": "last_name", "id": "id_"}

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
        assert "class Meta:" in result
        assert "key_transform_with_load = {" in result
        assert '"firstName": "first_name",' in result
        assert '"id": "id_",' in result
        assert '"lastName": "last_name",' in result

    def test_render_dataclass__empty_field_mappings__generates_base_schema_dataclass(self) -> None:
        """
        Scenario: Render a dataclass with empty field mappings dict.
        Expected Outcome: BaseSchema dataclass without Meta class.
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
        assert "key_transform_with_load" not in result  # No Meta class for empty mappings

    def test_render_dataclass__with_field_mappings__adds_proper_imports(self) -> None:
        """
        Scenario: Render a dataclass with field mappings and check imports.
        Expected Outcome: dataclass import is added.
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

    def test_render_dataclass__no_field_mappings__includes_dataclass_import(self) -> None:
        """
        Scenario: Render a dataclass without field mappings and check imports.
        Expected Outcome: dataclass import is added.
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

    def test_render_dataclass__sorted_field_mappings__generates_deterministic_output(self) -> None:
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
        a_field_pos = result.find('"aField": "a_field",')
        z_field_pos = result.find('"zField": "z_field",')

        # aField should come before zField (alphabetical order)
        assert a_field_pos < z_field_pos
        assert a_field_pos != -1
        assert z_field_pos != -1

    def test_render_dataclass__no_fields__generates_empty_class_with_base_schema(self) -> None:
        """
        Scenario: Render a dataclass with no fields.
        Expected Outcome: Empty BaseSchema dataclass with pass statement.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        context = RenderContext()

        # Act
        result = renderer.render_dataclass(class_name="Empty", fields=[], description="Empty class", context=context)

        # Assert
        assert "class Empty:" in result
        assert "pass" in result or "No properties defined in schema" in result

    def test_render_dataclass__single_field_mapping__generates_meta_class(self) -> None:
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
        assert "class User:" in result
        assert "class Meta:" in result
        assert '"userId": "user_id",' in result


class TestPythonConstructRendererDiscriminator:
    """Test PythonConstructRenderer discriminator rendering uses sanitized class names."""

    def test_render_alias__discriminator_with_acronym_schema_name__uses_sanitized_class_name(self) -> None:
        """
        Scenario: Render a union alias with a discriminator whose mapping references a schema
        name containing an uppercase acronym (e.g. WorkflowPromptAINode).

        Expected Outcome: The generated discriminator metadata and get_mapping() import both
        use the sanitized Python class name WorkflowPromptAiNode, never the raw OpenAPI name.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        context = RenderContext()
        discriminator = IRDiscriminator(
            property_name="type",
            mapping={"promptAI": "#/components/schemas/WorkflowPromptAINode"},
        )

        # Act
        result = renderer.render_alias(
            alias_name="WorkflowNode",
            target_type="Union[WorkflowPromptAiNode]",
            description=None,
            context=context,
            discriminator=discriminator,
        )

        # Assert - sanitized name must be used everywhere, raw name must not appear
        assert "WorkflowPromptAiNode" in result
        assert "WorkflowPromptAINode" not in result

    def test_render_alias__discriminator_mapping_data__uses_sanitized_class_name(self) -> None:
        """
        Scenario: The _mapping_data tuple in the generated discriminator class should
        store the sanitized Python class name, not the raw OpenAPI schema name.

        Expected Outcome: _mapping_data contains WorkflowPromptAiNode, not WorkflowPromptAINode.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        context = RenderContext()
        discriminator = IRDiscriminator(
            property_name="type",
            mapping={"promptAI": "#/components/schemas/WorkflowPromptAINode"},
        )

        # Act
        result = renderer.render_alias(
            alias_name="WorkflowNode",
            target_type="Union[WorkflowPromptAiNode]",
            description=None,
            context=context,
            discriminator=discriminator,
        )

        # Assert
        assert '("promptAI", "WorkflowPromptAiNode")' in result

    def test_render_alias__discriminator_get_mapping_import__uses_sanitized_class_name(self) -> None:
        """
        Scenario: The get_mapping() method should import the sanitized class name so
        the import resolves against the actual generated module.

        Expected Outcome: import statement uses WorkflowPromptAiNode.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        context = RenderContext()
        discriminator = IRDiscriminator(
            property_name="type",
            mapping={"promptAI": "#/components/schemas/WorkflowPromptAINode"},
        )

        # Act
        result = renderer.render_alias(
            alias_name="WorkflowNode",
            target_type="Union[WorkflowPromptAiNode]",
            description=None,
            context=context,
            discriminator=discriminator,
        )

        # Assert
        assert "from .workflow_prompt_ai_node import WorkflowPromptAiNode" in result
