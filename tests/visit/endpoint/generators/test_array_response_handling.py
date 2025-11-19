"""
Tests for array response handling in EndpointResponseHandlerGenerator.

These tests verify that array type aliases with dataclass items use proper deserialisation
instead of simple type casting.
"""

from unittest.mock import MagicMock

import pytest

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.ir import IROperation, IRResponse, IRSchema
from pyopenapi_gen.types.strategies.response_strategy import ResponseStrategy
from pyopenapi_gen.visit.endpoint.generators.response_handler_generator import (
    EndpointResponseHandlerGenerator,
)


class TestArrayResponseHandling:
    """Test array response handling with type aliases and dataclasses."""

    @pytest.fixture
    def render_context_mock(self):
        """Mock render context."""
        context = MagicMock(spec=RenderContext)
        context.import_collector = MagicMock()
        context.import_collector._current_file_module_dot_path = "some.dummy.path"
        context.name_sanitizer = MagicMock()
        context.core_package_name = "test_client.core"
        return context

    @pytest.fixture
    def code_writer_mock(self):
        """Mock code writer."""
        return MagicMock(spec=CodeWriter)

    def test_array_type_alias_with_dataclass_items__uses_proper_deserialisation(
        self, render_context_mock, code_writer_mock
    ):
        """
        Scenario: Response type is an array type alias (e.g., AgentListResponse = List[AgentListResponseItem])
                  where AgentListResponseItem is a dataclass with properties.
        Expected Outcome: Generated code uses list comprehension with .from_dict() for each item,
                         NOT cast(AgentListResponse, response.json()).
        """
        # Arrange
        # Create item schema (dataclass with properties)
        item_schema = IRSchema(
            type="object",
            name="AgentListResponseItem",
            properties={
                "id_": IRSchema(type="string", name="id"),
                "name": IRSchema(type="string", name="name"),
                "created_at": IRSchema(type="string", format="date-time", name="createdAt"),
            },
            required=["id", "name"],
        )

        # Create array type alias schema
        array_schema = IRSchema(
            type="array",
            name="AgentListResponse",
            items=item_schema,
        )

        # Create operation with array response
        operation = IROperation(
            operation_id="list_agents",
            summary="List agents",
            description="Retrieve list of agents.",
            method=HTTPMethod.GET,
            path="/agents",
            tags=["agents"],
            parameters=[],
            request_body=None,
            responses=[
                IRResponse(
                    status_code="200",
                    description="Successful response",
                    content={"application/json": array_schema},
                )
            ],
        )

        strategy = ResponseStrategy(
            return_type="AgentListResponse",
            response_schema=array_schema,
            is_streaming=False,
            response_ir=operation.responses[0],
        )

        # Set up schemas dict for the generator
        schemas = {
            "AgentListResponse": array_schema,
            "AgentListResponseItem": item_schema,
        }
        generator = EndpointResponseHandlerGenerator(schemas=schemas)

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        # Should use list comprehension with .from_dict()
        assert "[structure_from_dict(item, AgentListResponseItem) for item in response.json()]" in written_code

        # Should NOT use cast()
        assert "cast(AgentListResponse, response.json())" not in written_code

    def test_array_type_alias_with_primitive_items__uses_cast(self, render_context_mock, code_writer_mock):
        """
        Scenario: Response type is List[str] or similar primitive array.
        Expected Outcome: Generated code uses cast() since primitives don't need deserialisation.
        """
        # Arrange
        # Create array schema with primitive items
        array_schema = IRSchema(
            type="array",
            name="StringListResponse",
            items=IRSchema(type="string"),
        )

        operation = IROperation(
            operation_id="list_strings",
            summary="List strings",
            description="Retrieve list of strings.",
            method=HTTPMethod.GET,
            path="/strings",
            tags=["strings"],
            parameters=[],
            request_body=None,
            responses=[
                IRResponse(
                    status_code="200",
                    description="Successful response",
                    content={"application/json": array_schema},
                )
            ],
        )

        strategy = ResponseStrategy(
            return_type="StringListResponse",
            response_schema=array_schema,
            is_streaming=False,
            response_ir=operation.responses[0],
        )

        # Set up schemas dict
        schemas = {
            "StringListResponse": array_schema,
        }
        generator = EndpointResponseHandlerGenerator(schemas=schemas)

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        # Should use cast() for primitive arrays
        assert "cast(StringListResponse, response.json())" in written_code

        # Should NOT use list comprehension
        assert ".from_dict(item) for item in" not in written_code

    def test_dataclass_response__uses_from_dict(self, render_context_mock, code_writer_mock):
        """
        Scenario: Response type is a direct dataclass (not an array).
        Expected Outcome: Generated code uses .from_dict(response.json()).
        """
        # Arrange
        dataclass_schema = IRSchema(
            type="object",
            name="AgentResponse",
            properties={
                "id_": IRSchema(type="string", name="id"),
                "name": IRSchema(type="string", name="name"),
            },
            required=["id", "name"],
        )

        operation = IROperation(
            operation_id="get_agent",
            summary="Get agent",
            description="Retrieve single agent.",
            method=HTTPMethod.GET,
            path="/agents/{id}",
            tags=["agents"],
            parameters=[],
            request_body=None,
            responses=[
                IRResponse(
                    status_code="200",
                    description="Successful response",
                    content={"application/json": dataclass_schema},
                )
            ],
        )

        strategy = ResponseStrategy(
            return_type="AgentResponse",
            response_schema=dataclass_schema,
            is_streaming=False,
            response_ir=operation.responses[0],
        )

        schemas = {
            "AgentResponse": dataclass_schema,
        }
        generator = EndpointResponseHandlerGenerator(schemas=schemas)

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        # Should use structure_from_dict() for dataclass
        assert "structure_from_dict(response.json(), AgentResponse)" in written_code

        # Should NOT use cast()
        assert "cast(AgentResponse" not in written_code

    def test_is_dataclass_type__object_schema__returns_true(self):
        """
        Scenario: Check if a schema with type="object" is recognised as a dataclass.
        Expected Outcome: _is_dataclass_type() returns True.
        """
        # Arrange
        schema = IRSchema(
            type="object",
            name="User",
            properties={"name": IRSchema(type="string")},
        )
        schemas = {"User": schema}
        generator = EndpointResponseHandlerGenerator(schemas=schemas)

        # Act
        result = generator._is_dataclass_type("User")

        # Assert
        assert result is True

    def test_is_dataclass_type__primitive_type__returns_false(self):
        """
        Scenario: Check if a primitive type is recognised as NOT a dataclass.
        Expected Outcome: _is_dataclass_type() returns False for primitives.
        """
        # Arrange
        generator = EndpointResponseHandlerGenerator(schemas={})

        # Act & Assert
        assert generator._is_dataclass_type("str") is False
        assert generator._is_dataclass_type("int") is False
        assert generator._is_dataclass_type("bool") is False
        assert generator._is_dataclass_type("List") is False
        assert generator._is_dataclass_type("Dict") is False

    def test_extract_array_item_type__list_generic__extracts_item_type(self):
        """
        Scenario: Extract item type from List[ItemType] format.
        Expected Outcome: Returns "ItemType".
        """
        # Arrange
        generator = EndpointResponseHandlerGenerator(schemas={})

        # Act
        result = generator._extract_array_item_type("List[AgentListResponseItem]")

        # Assert
        assert result == "AgentListResponseItem"

    def test_extract_array_item_type__type_alias__extracts_from_schema(self):
        """
        Scenario: Extract item type from a type alias schema.
        Expected Outcome: Returns the item schema's name.
        """
        # Arrange
        item_schema = IRSchema(type="object", name="AgentListResponseItem", properties={})
        array_schema = IRSchema(type="array", name="AgentListResponse", items=item_schema)

        schemas = {
            "AgentListResponse": array_schema,
            "AgentListResponseItem": item_schema,
        }
        generator = EndpointResponseHandlerGenerator(schemas=schemas)

        # Act
        result = generator._extract_array_item_type("AgentListResponse")

        # Assert
        assert result == "AgentListResponseItem"

    def test_should_use_cattrs_structure__array_alias_with_dataclass_items__returns_true(self):
        """
        Scenario: Check if array type alias with dataclass items should use cattrs structure.
        Expected Outcome: _should_use_cattrs_structure() returns True (items need deserialisation).
        """
        # Arrange
        item_schema = IRSchema(type="object", name="Item", properties={"id": IRSchema(type="string")})
        array_schema = IRSchema(type="array", name="ItemList", items=item_schema)

        schemas = {
            "ItemList": array_schema,
            "Item": item_schema,
        }
        generator = EndpointResponseHandlerGenerator(schemas=schemas)

        # Act
        result = generator._should_use_cattrs_structure("ItemList")

        # Assert
        assert result is True

    def test_should_use_cattrs_structure__array_alias_with_primitive_items__returns_false(self):
        """
        Scenario: Check if array type alias with primitive items should use cattrs structure.
        Expected Outcome: _should_use_cattrs_structure() returns False (primitives use cast).
        """
        # Arrange
        array_schema = IRSchema(type="array", name="StringList", items=IRSchema(type="string"))

        schemas = {
            "StringList": array_schema,
        }
        generator = EndpointResponseHandlerGenerator(schemas=schemas)

        # Act
        result = generator._should_use_cattrs_structure("StringList")

        # Assert
        assert result is False

    def test_get_cattrs_deserialization_code__list_of_dataclass__generates_list_comprehension(self):
        """
        Scenario: Generate deserialisation code for List[DataclassModel].
        Expected Outcome: Returns list comprehension with structure_from_dict() for each item.
        """
        # Arrange
        generator = EndpointResponseHandlerGenerator(schemas={})

        # Act
        result = generator._get_cattrs_deserialization_code("List[AgentListResponseItem]", "response.json()")

        # Assert
        assert result == "[structure_from_dict(item, AgentListResponseItem) for item in response.json()]"
