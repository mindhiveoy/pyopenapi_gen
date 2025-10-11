"""
Unit tests for DataclassGenerator BaseSchema functionality.

Scenario: Test the DataclassGenerator's ability to generate dataclasses with
BaseSchema support when field name mapping is required.

Expected Outcome: Generated dataclasses include BaseSchema inheritance and
field mapping configuration for fields that require name sanitization.
"""

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer
from pyopenapi_gen.visit.model.dataclass_generator import DataclassGenerator


class TestDataclassGeneratorBaseSchema:
    """Test DataclassGenerator BaseSchema functionality."""

    def test_generate__camel_case_fields__generates_base_schema_dataclass(self) -> None:
        """
        Scenario: Generate dataclass with camelCase field names requiring mapping.
        Expected Outcome: Dataclass with BaseSchema inheritance and field mappings.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="User",
            type="object",
            properties={
                "firstName": IRSchema(name="firstName", type="string", description="First name"),
                "lastName": IRSchema(name="lastName", type="string", description="Last name"),
                "emailAddress": IRSchema(name="emailAddress", type="string", description="Email address"),
            },
            required=["firstName", "lastName"],
        )

        # Act
        result = generator.generate(schema, "User", context)

        # Assert
        assert "class User(BaseSchema):" in result
        assert "with automatic JSON field mapping" in result
        assert "class Meta:" in result
        assert "key_transform_with_load = {" in result
        assert '"emailAddress": "email_address",' in result
        assert '"firstName": "first_name",' in result
        assert '"lastName": "last_name",' in result

    def test_generate__reserved_keyword_fields__generates_base_schema_dataclass(self) -> None:
        """
        Scenario: Generate dataclass with reserved keyword field names.
        Expected Outcome: Dataclass with BaseSchema inheritance and mappings for reserved words.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="Data",
            type="object",
            properties={
                "id": IRSchema(name="id", type="string", description="Identifier"),
                "class": IRSchema(name="class", type="string", description="Classification"),
                "type": IRSchema(name="type", type="string", description="Type information"),
            },
            required=["id", "class"],
        )

        # Act
        result = generator.generate(schema, "Data", context)

        # Assert
        assert "class Data(BaseSchema):" in result
        assert '"class": "class_",' in result
        assert '"id": "id_",' in result
        assert '"type": "type_",' in result

    def test_generate__no_field_mapping_needed__generates_base_schema_dataclass(self) -> None:
        """
        Scenario: Generate dataclass with field names that don't require mapping.
        Expected Outcome: BaseSchema dataclass for better DX but no Meta class since no mappings needed.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="Simple",
            type="object",
            properties={
                "name": IRSchema(name="name", type="string", description="Name"),
                "status": IRSchema(name="status", type="string", description="Status"),
                "value": IRSchema(name="value", type="integer", description="Value"),
            },
            required=["name"],
        )

        # Act
        result = generator.generate(schema, "Simple", context)

        # Assert
        assert "class Simple(BaseSchema):" in result
        assert "with automatic JSON field mapping" in result
        assert "key_transform_with_load" not in result  # No Meta class when no mappings needed

    def test_generate__mixed_fields__generates_base_schema_for_mapped_fields_only(self) -> None:
        """
        Scenario: Generate dataclass with mix of fields requiring and not requiring mapping.
        Expected Outcome: BaseSchema dataclass with mappings only for fields that need it.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="Mixed",
            type="object",
            properties={
                "name": IRSchema(name="name", type="string", description="Name"),
                "firstName": IRSchema(name="firstName", type="string", description="First name"),
                "status": IRSchema(name="status", type="string", description="Status"),
                "id": IRSchema(name="id", type="string", description="Identifier"),
            },
            required=["name", "firstName"],
        )

        # Act
        result = generator.generate(schema, "Mixed", context)

        # Assert
        assert "class Mixed(BaseSchema):" in result
        assert '"firstName": "first_name",' in result
        assert '"id": "id_",' in result
        # name and status shouldn't appear in mappings since they don't need mapping
        assert (
            "'name':" not in result.split("key_transform_with_load")[1] if "key_transform_with_load" in result else True
        )
        assert (
            "'status':" not in result.split("key_transform_with_load")[1]
            if "key_transform_with_load" in result
            else True
        )

    def test_generate__enhanced_field_documentation__includes_mapping_info(self) -> None:
        """
        Scenario: Generate dataclass with field mappings.
        Expected Outcome: Field documentation includes mapping information.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="User",
            type="object",
            properties={
                "firstName": IRSchema(name="firstName", type="string", description="User's first name"),
                "id": IRSchema(name="id", type="string"),  # No description
            },
            required=["firstName", "id"],
        )

        # Act
        result = generator.generate(schema, "User", context)

        # Assert
        # Should enhance existing descriptions
        assert "User's first name (maps from 'firstName')" in result
        # Should add mapping info for fields without description
        assert "Maps from 'id'" in result

    def test_generate__array_type_dataclass__uses_base_schema_for_consistency(self) -> None:
        """
        Scenario: Generate dataclass for array type (wrapper style).
        Expected Outcome: BaseSchema dataclass for consistency, but no Meta class since no field mappings.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(name="UserList", type="array", items=IRSchema(name="User", type="object", properties={}))

        # Act
        result = generator.generate(schema, "UserList", context)

        # Assert
        assert "class UserList(BaseSchema):" in result
        assert "with automatic JSON field mapping" in result
        # Array wrapper shouldn't have field mappings Meta class
        assert "key_transform_with_load" not in result

    def test_generate__adds_correct_imports_for_base_schema(self) -> None:
        """
        Scenario: Generate dataclass requiring BaseSchema.
        Expected Outcome: Proper imports are added to context.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(
            name="User",
            type="object",
            properties={"firstName": IRSchema(name="firstName", type="string")},
            required=["firstName"],
        )

        # Act
        generator.generate(schema, "User", context)

        # Assert
        imports = context.import_collector.imports
        assert "dataclasses" in imports
        assert "dataclass" in imports["dataclasses"]
        assert "core.schemas" in imports
        assert "BaseSchema" in imports["core.schemas"]

    def test_generate__no_properties__generates_empty_base_schema_dataclass(self) -> None:
        """
        Scenario: Generate dataclass with no properties.
        Expected Outcome: Empty BaseSchema dataclass for consistency.
        """
        # Arrange
        renderer = PythonConstructRenderer()
        generator = DataclassGenerator(renderer, {})
        context = RenderContext()

        schema = IRSchema(name="Empty", type="object", properties={}, required=[])

        # Act
        result = generator.generate(schema, "Empty", context)

        # Assert
        assert "class Empty(BaseSchema):" in result
        assert "with automatic JSON field mapping" in result
        assert "pass" in result or "No properties defined in schema" in result
        # Should not have Meta class since no field mappings
        assert "key_transform_with_load" not in result
