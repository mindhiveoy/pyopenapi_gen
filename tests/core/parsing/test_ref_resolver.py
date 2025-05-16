from unittest.mock import MagicMock  # For monkeypatch type hint

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.ref_resolver import _resolve_schema_ref

# Import _parse_schema from its new location


class TestResolveSchemaRef:
    def test_resolve_ref__simple_direct_resolution__returns_parsed_schema(self) -> None:
        """
        Scenario:
            - A $ref points to an existing schema in raw_spec_schemas.
            - The schema has not been parsed yet.
        Expected Outcome:
            - _resolve_schema_ref should parse the referenced schema.
            - The parsed schema should be stored in context.parsed_schemas.
            - The parsed schema should be returned.
        """
        # Arrange
        raw_spec = {"Pet": {"type": "object", "properties": {"name": {"type": "string"}}}}
        context = ParsingContext(raw_spec_schemas=raw_spec)
        ref_value = "#/components/schemas/Pet"

        result_schema = _resolve_schema_ref(ref_value, "TestSchema", context)

        assert result_schema.name == "Pet"
        assert not result_schema._from_unresolved_ref
        assert "Pet" in context.parsed_schemas
        assert context.parsed_schemas["Pet"].properties["name"].type == "string"

    def test_resolve_ref__already_parsed__returns_cached_schema(self) -> None:
        """
        Scenario:
            - A $ref points to a schema that is already in context.parsed_schemas.
        Expected Outcome:
            - _resolve_schema_ref should return the cached IRSchema directly.
        """
        # Arrange
        cached_pet_schema = IRSchema(name="Pet", type="object", properties={"id": IRSchema(name=None, type="integer")})
        context = ParsingContext(
            raw_spec_schemas={"Pet": {}},
            parsed_schemas={"Pet": cached_pet_schema},
        )
        ref_value = "#/components/schemas/Pet"

        result_schema = _resolve_schema_ref(ref_value, "TestSchema", context)

        assert result_schema is cached_pet_schema
        assert result_schema.name == "Pet"

    def test_resolve_ref__circular_dependency__returns_placeholder_schema(self) -> None:
        """
        Scenario:
            - Schema 'A' refers to 'B', and 'B' refers back to 'A'.
            - _resolve_schema_ref is called for 'A'.
        Expected Outcome:
            - When resolving 'B's ref to 'A', it should detect the cycle.
            - It should return a placeholder IRSchema(name="A") for the circular ref.
        """
        # Arrange
        raw_spec = {
            "A": {"type": "object", "properties": {"b_ref": {"$ref": "#/components/schemas/B"}}},
            "B": {"type": "object", "properties": {"a_ref": {"$ref": "#/components/schemas/A"}}},
        }
        context = ParsingContext(raw_spec_schemas=raw_spec)
        context.visited_refs.add("A")

        ref_to_A_from_B = "#/components/schemas/A"
        result_schema = _resolve_schema_ref(ref_to_A_from_B, "B", context)

        assert result_schema.name == "A"
        assert not result_schema.properties  # Cycle placeholder is basic
        # For a cycle, _from_unresolved_ref should ideally be False, or it's a true unresolved ref.
        # The current _resolve_schema_ref returns a basic IRSchema(name=ref_name) for cycles.
        assert not result_schema._from_unresolved_ref

    def test_resolve_ref__unresolvable_ref__returns_unresolved_placeholder(self) -> None:
        """
        Scenario:
            - A $ref points to a schema name that does not exist in raw_spec_schemas.
        Expected Outcome:
            - _resolve_schema_ref should return an IRSchema marked as _from_unresolved_ref=True.
            - A warning should be added to context.collected_warnings.
        """
        # Arrange
        context = ParsingContext(raw_spec_schemas={})
        ref_value = "#/components/schemas/NonExistent"

        result_schema = _resolve_schema_ref(ref_value, "TestSchema", context)

        assert result_schema.name == "NonExistent"
        assert result_schema._from_unresolved_ref is True
        assert len(context.collected_warnings) >= 1
        assert "Could not resolve $ref" in context.collected_warnings[-1]

    def test_resolve_ref__non_component_ref__returns_unresolved_placeholder(self) -> None:
        """
        Scenario:
            - A $ref points to a path not under #/components/schemas/.
        Expected Outcome:
            - _resolve_schema_ref should treat it as unresolvable.
            - It should return an IRSchema marked as _from_unresolved_ref=True.
            - A warning should be added to context.collected_warnings.
        """
        # Arrange
        context = ParsingContext(raw_spec_schemas={})
        ref_value = "#/paths/somePath/get/responses/200"

        result_schema = _resolve_schema_ref(ref_value, "TestSchema", context)

        assert result_schema._from_unresolved_ref is True
        assert result_schema.name == "TestSchema"  # Name comes from current_schema_name_for_context
        assert len(context.collected_warnings) >= 1
        assert "Unsupported or invalid $ref format" in context.collected_warnings[-1]

    def test_resolve_ref__integration_with_parse_schema__parses_correctly(self, monkeypatch: MagicMock) -> None:
        """
        Scenario:
            - _resolve_schema_ref is called for a valid, unparsed schema.
        Expected Outcome:
            - It should internally call _parse_schema to do the actual parsing.
            - The result from _parse_schema should be returned and cached.
        """
        # Arrange
        raw_spec_dict = {"MyModel": {"type": "object", "properties": {"id": {"type": "integer"}}}}
        context = ParsingContext(raw_spec_schemas=raw_spec_dict)
        ref_value = "#/components/schemas/MyModel"

        resolved_schema = _resolve_schema_ref(ref_value, "TestCaller", context)

        assert resolved_schema.name == "MyModel"
        assert not resolved_schema._from_unresolved_ref
        assert "MyModel" in context.parsed_schemas
        assert context.parsed_schemas["MyModel"].properties["id"].type == "integer"
