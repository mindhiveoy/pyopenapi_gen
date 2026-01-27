"""Tests for automatic dataclass to dictionary serialization in generated clients.

Scenario: Generated clients should automatically convert dataclass inputs to dictionaries
for API calls without requiring manual conversion by the developer.

Expected Outcome: Dataclass instances passed as request bodies should be seamlessly
converted to dictionaries before being sent in HTTP requests.
"""

import dataclasses
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

import pytest

from pyopenapi_gen.core.utils import DataclassSerializer


@dataclasses.dataclass
class SimpleUser:
    """Simple user dataclass for testing."""

    name: str
    email: str
    age: int


@dataclasses.dataclass
class NestedUser:
    """User with nested dataclass for testing."""

    name: str
    profile: "UserProfile"


@dataclasses.dataclass
class UserProfile:
    """User profile dataclass for testing."""

    bio: str
    avatar_url: str | None = None


@dataclasses.dataclass
class ComplexData:
    """Complex dataclass with various types for testing."""

    id: int
    tags: List[str]
    metadata: dict[str, Any]
    created_at: datetime
    is_active: bool
    optional_field: str | None = None


class Status(Enum):
    """Status enum for testing."""

    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"


class Priority(Enum):
    """Priority enum with integer values for testing."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclasses.dataclass
class Task:
    """Task dataclass with enum fields for testing."""

    title: str
    status: Status
    priority: Priority


@dataclasses.dataclass
class Project:
    """Project dataclass with nested enum-containing dataclass for testing."""

    name: str
    main_task: Task
    backup_status: Status | None = None


class TestDataclassSerializer:
    """Test the DataclassSerializer utility that should be added to core.utils."""

    def test_serialize_simple_dataclass__converts_to_dict__returns_proper_structure(self) -> None:
        """
        Scenario: Serialize a simple dataclass with basic types
        Expected Outcome: Returns a dictionary with all field values preserved
        """
        # Arrange
        user = SimpleUser(name="John Doe", email="john@example.com", age=30)

        # Act
        result = DataclassSerializer.serialize(user)

        # Assert
        expected = {"name": "John Doe", "email": "john@example.com", "age": 30}
        assert result == expected
        assert isinstance(result, dict)

    def test_serialize_nested_dataclass__converts_recursively__returns_proper_structure(self) -> None:
        """
        Scenario: Serialize a dataclass with nested dataclass fields
        Expected Outcome: Recursively converts nested dataclasses to dictionaries
        """
        # Arrange
        profile = UserProfile(bio="Software developer", avatar_url="https://example.com/avatar.jpg")
        user = NestedUser(name="Jane Doe", profile=profile)

        # Act
        result = DataclassSerializer.serialize(user)

        # Assert
        expected = {
            "name": "Jane Doe",
            "profile": {"bio": "Software developer", "avatar_url": "https://example.com/avatar.jpg"},
        }
        assert result == expected

    def test_serialize_dataclass_with_optional_none__excludes_none_values__returns_clean_dict(self) -> None:
        """
        Scenario: Serialize a dataclass with None optional fields
        Expected Outcome: None values are excluded from the resulting dictionary
        """
        # Arrange
        profile = UserProfile(bio="Developer")  # avatar_url is None by default
        user = NestedUser(name="Bob", profile=profile)

        # Act
        result = DataclassSerializer.serialize(user)

        # Assert
        expected = {"name": "Bob", "profile": {"bio": "Developer"}}
        assert result == expected
        assert "avatar_url" not in result["profile"]

    def test_serialize_complex_dataclass__handles_various_types__returns_serialized_dict(self) -> None:
        """
        Scenario: Serialize a dataclass with lists, dicts, dates, and optional fields
        Expected Outcome: All supported types are properly serialized
        """
        # Arrange
        created_at = datetime(2023, 1, 15, 10, 30, 0)
        data = ComplexData(
            id=123,
            tags=["python", "api"],
            metadata={"version": "1.0", "debug": True},
            created_at=created_at,
            is_active=True,
            optional_field="test",
        )

        # Act
        result = DataclassSerializer.serialize(data)

        # Assert
        expected = {
            "id": 123,
            "tags": ["python", "api"],
            "metadata": {"version": "1.0", "debug": True},
            "created_at": "2023-01-15T10:30:00",  # ISO format
            "is_active": True,
            "optional_field": "test",
        }
        assert result == expected

    def test_serialize_list_of_dataclasses__converts_all_items__returns_list_of_dicts(self) -> None:
        """
        Scenario: Serialize a list containing dataclass instances
        Expected Outcome: Each dataclass in the list is converted to a dictionary
        """
        # Arrange
        users = [
            SimpleUser(name="Alice", email="alice@test.com", age=25),
            SimpleUser(name="Bob", email="bob@test.com", age=35),
        ]

        # Act
        result = DataclassSerializer.serialize(users)

        # Assert
        expected = [
            {"name": "Alice", "email": "alice@test.com", "age": 25},
            {"name": "Bob", "email": "bob@test.com", "age": 35},
        ]
        assert result == expected

    def test_serialize_dict_with_dataclass_values__converts_values__preserves_structure(self) -> None:
        """
        Scenario: Serialize a dictionary containing dataclass values
        Expected Outcome: Dataclass values are converted while preserving dictionary structure
        """
        # Arrange
        data = {
            "user1": SimpleUser(name="Alice", email="alice@test.com", age=25),
            "user2": SimpleUser(name="Bob", email="bob@test.com", age=35),
            "count": 2,
        }

        # Act
        result = DataclassSerializer.serialize(data)

        # Assert
        expected = {
            "user1": {"name": "Alice", "email": "alice@test.com", "age": 25},
            "user2": {"name": "Bob", "email": "bob@test.com", "age": 35},
            "count": 2,
        }
        assert result == expected

    def test_serialize_non_dataclass__returns_unchanged__preserves_original_value(self) -> None:
        """
        Scenario: Serialize non-dataclass values (strings, dicts, lists, etc.)
        Expected Outcome: Values are returned unchanged
        """
        # Arrange & Act & Assert
        assert DataclassSerializer.serialize("string") == "string"
        assert DataclassSerializer.serialize(123) == 123
        assert DataclassSerializer.serialize({"key": "value"}) == {"key": "value"}
        assert DataclassSerializer.serialize([1, 2, 3]) == [1, 2, 3]
        assert DataclassSerializer.serialize(None) is None

    def test_serialize_datetime__converts_to_iso_string__returns_iso_format(self) -> None:
        """
        Scenario: Serialize datetime objects
        Expected Outcome: Datetime is converted to ISO format string
        """
        # Arrange
        dt = datetime(2023, 5, 15, 14, 30, 45)

        # Act
        result = DataclassSerializer.serialize(dt)

        # Assert
        assert result == "2023-05-15T14:30:45"
        assert isinstance(result, str)

    def test_serialize_empty_dataclass__returns_empty_dict__handles_edge_case(self) -> None:
        """
        Scenario: Serialize a dataclass with no fields
        Expected Outcome: Returns an empty dictionary
        """

        # Arrange
        @dataclasses.dataclass
        class EmptyClass:
            pass

        empty_obj = EmptyClass()

        # Act
        result = DataclassSerializer.serialize(empty_obj)

        # Assert
        assert result == {}
        assert isinstance(result, dict)

    def test_serialize_enum_string_value__converts_to_value__returns_string(self) -> None:
        """
        Scenario: Serialize an enum instance with string value
        Expected Outcome: Returns the enum's underlying value (string)
        """
        # Arrange
        status = Status.ACTIVE

        # Act
        result = DataclassSerializer.serialize(status)

        # Assert
        assert result == "active"
        assert isinstance(result, str)

    def test_serialize_enum_integer_value__converts_to_value__returns_integer(self) -> None:
        """
        Scenario: Serialize an enum instance with integer value
        Expected Outcome: Returns the enum's underlying value (integer)
        """
        # Arrange
        priority = Priority.HIGH

        # Act
        result = DataclassSerializer.serialize(priority)

        # Assert
        assert result == 3
        assert isinstance(result, int)

    def test_serialize_dataclass_with_enum_fields__converts_enums_to_values__returns_proper_dict(self) -> None:
        """
        Scenario: Serialize a dataclass containing enum fields
        Expected Outcome: Enum fields are converted to their underlying values
        """
        # Arrange
        task = Task(title="Implement feature", status=Status.ACTIVE, priority=Priority.HIGH)

        # Act
        result = DataclassSerializer.serialize(task)

        # Assert
        expected = {"title": "Implement feature", "status": "active", "priority": 3}
        assert result == expected

    def test_serialize_nested_dataclass_with_enums__converts_recursively__returns_proper_structure(self) -> None:
        """
        Scenario: Serialize nested dataclasses containing enum fields
        Expected Outcome: All enum fields at all nesting levels are converted to values
        """
        # Arrange
        task = Task(title="Main task", status=Status.COMPLETED, priority=Priority.CRITICAL)
        project = Project(name="API Project", main_task=task, backup_status=Status.PENDING)

        # Act
        result = DataclassSerializer.serialize(project)

        # Assert
        expected = {
            "name": "API Project",
            "main_task": {"title": "Main task", "status": "completed", "priority": 4},
            "backup_status": "pending",
        }
        assert result == expected

    def test_serialize_list_with_enum_values__converts_all_enums__returns_list_of_values(self) -> None:
        """
        Scenario: Serialize a list containing enum instances
        Expected Outcome: Each enum in the list is converted to its underlying value
        """
        # Arrange
        statuses = [Status.PENDING, Status.ACTIVE, Status.COMPLETED]

        # Act
        result = DataclassSerializer.serialize(statuses)

        # Assert
        expected = ["pending", "active", "completed"]
        assert result == expected

    def test_serialize_dict_with_enum_values__converts_enum_values__preserves_keys(self) -> None:
        """
        Scenario: Serialize a dictionary with enum values
        Expected Outcome: Enum values are converted while dictionary keys are preserved
        """
        # Arrange
        status_map = {"current": Status.ACTIVE, "previous": Status.PENDING, "target": Status.COMPLETED}

        # Act
        result = DataclassSerializer.serialize(status_map)

        # Assert
        expected = {"current": "active", "previous": "pending", "target": "completed"}
        assert result == expected

    def test_serialize_dataclass_with_optional_enum_none__excludes_none_value__returns_clean_dict(self) -> None:
        """
        Scenario: Serialize a dataclass with optional enum field set to None
        Expected Outcome: None enum field is excluded from the result
        """
        # Arrange
        task = Task(title="Simple task", status=Status.PENDING, priority=Priority.LOW)
        project = Project(name="Simple project", main_task=task)  # backup_status is None

        # Act
        result = DataclassSerializer.serialize(project)

        # Assert
        expected = {
            "name": "Simple project",
            "main_task": {"title": "Simple task", "status": "pending", "priority": 1},
        }
        assert result == expected
        assert "backup_status" not in result

    def test_serialize_mixed_dataclass_with_enums_and_complex_types__handles_all_types__returns_complete_dict(
        self,
    ) -> None:
        """
        Scenario: Serialize a dataclass containing enums, dates, lists, and nested structures
        Expected Outcome: All types including enums are properly serialized
        """

        # Arrange
        @dataclasses.dataclass
        class ComplexTask:
            title: str
            status: Status
            priority: Priority
            created_at: datetime
            tags: List[str]
            metadata: dict[str, Any]

        created_at = datetime(2023, 6, 15, 9, 30, 0)
        task = ComplexTask(
            title="Complex task",
            status=Status.ACTIVE,
            priority=Priority.HIGH,
            created_at=created_at,
            tags=["urgent", "api"],
            metadata={"version": "2.0", "retries": 3},
        )

        # Act
        result = DataclassSerializer.serialize(task)

        # Assert
        expected = {
            "title": "Complex task",
            "status": "active",
            "priority": 3,
            "created_at": "2023-06-15T09:30:00",
            "tags": ["urgent", "api"],
            "metadata": {"version": "2.0", "retries": 3},
        }
        assert result == expected


class TestGeneratedClientDataclassIntegration:
    """Test that generated client code properly integrates dataclass serialization."""

    def test_json_body_serialization__converts_dataclass_automatically__sends_proper_dict(self) -> None:
        """
        Scenario: Generated endpoint method receives dataclass as body parameter
        Expected Outcome: Dataclass is automatically converted to dictionary for JSON serialization
        """
        # This test verifies the expected behavior in generated code
        # The actual implementation will be in the generators

        # Arrange - simulate what generated code should do
        user = SimpleUser(name="Test User", email="test@example.com", age=25)

        # Act - simulate the conversion that should happen in generated code
        from pyopenapi_gen.core.utils import DataclassSerializer

        json_body = DataclassSerializer.serialize(user)

        # Assert
        expected = {"name": "Test User", "email": "test@example.com", "age": 25}
        assert json_body == expected
        assert isinstance(json_body, dict)

    def test_form_data_serialization__flattens_dataclass_fields__creates_form_data(self) -> None:
        """
        Scenario: Generated endpoint method receives dataclass for form data
        Expected Outcome: Dataclass fields are flattened into form data dictionary
        """
        # Arrange
        user = SimpleUser(name="Form User", email="form@example.com", age=30)

        # Act - simulate what should happen in generated code for form data
        from pyopenapi_gen.core.utils import DataclassSerializer

        form_data = DataclassSerializer.serialize(user)

        # Assert
        expected = {"name": "Form User", "email": "form@example.com", "age": 30}
        assert form_data == expected

    def test_nested_dataclass_serialization__handles_complex_structures__preserves_hierarchy(self) -> None:
        """
        Scenario: Generated endpoint method receives nested dataclass structures
        Expected Outcome: Complex nested structures are properly serialized
        """
        # Arrange
        profile = UserProfile(bio="Complex user", avatar_url="https://example.com/avatar.jpg")
        user = NestedUser(name="Complex User", profile=profile)

        # Act
        from pyopenapi_gen.core.utils import DataclassSerializer

        json_body = DataclassSerializer.serialize(user)

        # Assert
        expected = {
            "name": "Complex User",
            "profile": {"bio": "Complex user", "avatar_url": "https://example.com/avatar.jpg"},
        }
        assert json_body == expected


class TestDataclassSerializationErrorHandling:
    """Test error handling in dataclass serialization."""

    def test_serialize_circular_reference__handles_gracefully__avoids_infinite_recursion(self) -> None:
        """
        Scenario: Attempt to serialize dataclass with circular references
        Expected Outcome: Handles gracefully without infinite recursion and produces JSON-safe output
        """
        import json

        @dataclasses.dataclass
        class Node:
            name: str
            parent: Optional["Node"] = None

        # Arrange - create circular reference
        parent = Node(name="parent")
        child = Node(name="child", parent=parent)
        parent.parent = child  # Create circular reference

        # Act & Assert - should not cause infinite recursion
        from pyopenapi_gen.core.utils import DataclassSerializer

        try:
            result = DataclassSerializer.serialize(parent)
            # Should handle this gracefully
            assert isinstance(result, dict)
            assert result["name"] == "parent"

            # CRITICAL: Must be JSON serializable (no dataclass instances in output)
            json_str = json.dumps(result)
            assert json_str is not None

            # Verify circular ref was handled (should be None or dict, not dataclass)
            if "parent" in result:
                nested = result["parent"]
                assert isinstance(nested, (dict, type(None))), f"Nested value must be dict or None, got {type(nested)}"
                # Ensure it's not a dataclass instance
                assert not dataclasses.is_dataclass(nested), "Must not be dataclass instance"
        except RecursionError:
            pytest.fail("DataclassSerializer should handle circular references gracefully")

    def test_serialize_deep_circular__multiple_paths__json_safe(self) -> None:
        """
        Scenario: Complex circular structures with multiple reference paths
        Expected Outcome: All paths handled correctly and result is JSON-safe
        """
        import json

        from pyopenapi_gen.core.utils import DataclassSerializer

        @dataclasses.dataclass
        class Person:
            name: str
            friend: Optional["Person"] = None
            spouse: Optional["Person"] = None

        # Arrange - create complex circular structure
        alice = Person(name="Alice")
        bob = Person(name="Bob")
        charlie = Person(name="Charlie")

        alice.friend = bob
        bob.friend = charlie
        charlie.friend = alice  # Circular path via friend
        alice.spouse = bob
        bob.spouse = alice  # Another circular path via spouse

        # Act
        result = DataclassSerializer.serialize(alice)

        # Assert - must be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None
        assert result["name"] == "Alice"

        # Verify nested structures are dicts or None, not dataclass instances
        if "friend" in result and result["friend"] is not None:
            assert isinstance(result["friend"], dict)
            assert not dataclasses.is_dataclass(result["friend"])
        if "spouse" in result and result["spouse"] is not None:
            assert isinstance(result["spouse"], dict)
            assert not dataclasses.is_dataclass(result["spouse"])

    def test_serialize_self_reference__handles_gracefully(self) -> None:
        """
        Scenario: Dataclass with self-reference
        Expected Outcome: Handles gracefully and produces JSON-safe output
        """
        import json

        from pyopenapi_gen.core.utils import DataclassSerializer

        @dataclasses.dataclass
        class SelfRef:
            value: int
            me: Optional["SelfRef"] = None

        # Arrange - create self-reference
        obj = SelfRef(value=42)
        obj.me = obj  # Self-reference

        # Act
        result = DataclassSerializer.serialize(obj)

        # Assert - must be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None
        assert result["value"] == 42

        # Self-reference should be None (circular)
        if "me" in result:
            assert result["me"] is None

    def test_serialize_with_custom_cattrs_hook__circular_refs__respects_hook_and_json_safe(self) -> None:
        """
        Scenario: Dataclass with custom cattrs hook and circular references
        Expected Outcome: Custom hook is respected AND result is JSON-safe

        Note: Custom hooks should handle their own structure flattening but let
        DataclassSerializer handle nested dataclasses to avoid infinite recursion.
        """
        import json
        from typing import Any

        from pyopenapi_gen.core.cattrs_converter import converter
        from pyopenapi_gen.core.utils import DataclassSerializer

        @dataclasses.dataclass
        class PropertiesWithData:
            _data: dict[str, str] = dataclasses.field(default_factory=dict)
            parent: Optional["PropertiesWithData"] = None

        # Register custom hook (simulates generated code for additionalProperties)
        # Hook should flatten _data but leave nested dataclasses for our wrapper to handle
        def unstructure_hook(instance: PropertiesWithData) -> dict[str, Any]:
            result = dict(instance._data)  # Flatten _data
            # Leave parent as-is for DataclassSerializer to handle
            if instance.parent is not None:
                result["parent"] = instance.parent  # Don't recurse, let wrapper handle it
            return result

        converter.register_unstructure_hook(PropertiesWithData, unstructure_hook)

        try:
            # Arrange - create circular structure
            parent = PropertiesWithData(_data={"key": "parent"})
            child = PropertiesWithData(_data={"key": "child"}, parent=parent)
            parent.parent = child  # Circular

            # Act
            result = DataclassSerializer.serialize(parent)

            # Assert - hook was used (no _data in output)
            assert "_data" not in result, "Custom hook should flatten _data"
            assert "key" in result
            assert result["key"] == "parent"

            # CRITICAL: Must be JSON serializable even with custom hook
            json_str = json.dumps(result)
            assert json_str is not None

            # Verify nested structures don't contain _data field or dataclass instances
            if "parent" in result and result["parent"] is not None:
                assert isinstance(result["parent"], dict)
                assert "_data" not in result["parent"], "Nested hook should also flatten _data"
                assert not dataclasses.is_dataclass(result["parent"])
        finally:
            # Clean up hook to avoid affecting other tests
            if hasattr(converter, "_unstructure_func"):
                converter._unstructure_func.clear_cache()

    def test_serialize_with_custom_types__handles_unknown_types__falls_back_gracefully(self) -> None:
        """
        Scenario: Serialize dataclass with custom types that can't be serialized
        Expected Outcome: Falls back gracefully for unknown types
        """

        class CustomType:
            def __init__(self, value: str) -> None:
                self.value = value

        @dataclasses.dataclass
        class WithCustomType:
            name: str
            custom: CustomType

        # Arrange
        obj = WithCustomType(name="test", custom=CustomType("custom_value"))

        # Act
        from pyopenapi_gen.core.utils import DataclassSerializer

        result = DataclassSerializer.serialize(obj)

        # Assert - should handle custom types (likely by calling str() or repr())
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert "custom" in result


class TestDataclassSerializationBinaryTypes:
    """Test bytes and bytearray serialisation to base64."""

    def test_serialize_bytes__plain_bytes__returns_base64_encoded_string(self) -> None:
        """
        Scenario: Serialize bytes directly
        Expected Outcome: Returns base64-encoded ASCII string
        """
        import base64

        # Arrange
        pdf_bytes = b"%PDF-1.7\n\nThis is test PDF content"

        # Act
        result = DataclassSerializer.serialize(pdf_bytes)

        # Assert
        expected = base64.b64encode(pdf_bytes).decode("ascii")
        assert result == expected
        assert isinstance(result, str)

    def test_serialize_bytes__bytearray__returns_base64_encoded_string(self) -> None:
        """
        Scenario: Serialize bytearray directly
        Expected Outcome: Returns base64-encoded ASCII string
        """
        import base64

        # Arrange
        data = bytearray(b"Hello, World!")

        # Act
        result = DataclassSerializer.serialize(data)

        # Assert
        expected = base64.b64encode(bytes(data)).decode("ascii")
        assert result == expected
        assert isinstance(result, str)

    def test_serialize_bytes__in_dataclass_field__returns_base64_encoded_string(self) -> None:
        """
        Scenario: Serialize a dataclass containing a bytes field
        Expected Outcome: Bytes field is converted to base64-encoded string
        """
        import base64

        # Arrange
        @dataclasses.dataclass
        class Document:
            name: str
            binary: bytes

        doc_content = b"%PDF-1.7\n\nDocument content here"
        doc = Document(name="test.pdf", binary=doc_content)

        # Act
        result = DataclassSerializer.serialize(doc)

        # Assert
        expected_binary = base64.b64encode(doc_content).decode("ascii")
        assert result == {"name": "test.pdf", "binary": expected_binary}
        assert isinstance(result["binary"], str)

    def test_serialize_bytes__in_list__returns_base64_encoded_strings(self) -> None:
        """
        Scenario: Serialize a list containing bytes values
        Expected Outcome: Each bytes value is converted to base64-encoded string
        """
        import base64

        # Arrange
        data_list = [b"first", b"second", b"third"]

        # Act
        result = DataclassSerializer.serialize(data_list)

        # Assert
        expected = [base64.b64encode(b).decode("ascii") for b in data_list]
        assert result == expected

    def test_serialize_bytes__roundtrip_decode__matches_original(self) -> None:
        """
        Scenario: Verify that serialised bytes can be decoded back
        Expected Outcome: Decoded bytes match the original input
        """
        import base64

        # Arrange
        original_bytes = b"%PDF-1.7\n\nThis is test PDF content with special chars: \x00\x01\x02"

        # Act
        serialized = DataclassSerializer.serialize(original_bytes)
        decoded = base64.b64decode(serialized)

        # Assert
        assert decoded == original_bytes

    def test_serialize_bytes__optional_none__excludes_from_output(self) -> None:
        """
        Scenario: Serialize a dataclass with optional bytes field set to None
        Expected Outcome: None bytes field is excluded from the result
        """

        # Arrange
        @dataclasses.dataclass
        class DocumentOptional:
            name: str
            binary: bytes | None = None

        doc = DocumentOptional(name="empty.txt")

        # Act
        result = DataclassSerializer.serialize(doc)

        # Assert
        assert result == {"name": "empty.txt"}
        assert "binary" not in result

    def test_serialize_bytes__empty_bytes__returns_empty_base64(self) -> None:
        """
        Scenario: Serialize empty bytes
        Expected Outcome: Returns empty base64 string
        """
        import base64

        # Arrange
        empty_bytes = b""

        # Act
        result = DataclassSerializer.serialize(empty_bytes)

        # Assert
        expected = base64.b64encode(empty_bytes).decode("ascii")
        assert result == expected
        assert result == ""


class TestDataclassSerializerCattrsIntegration:
    """Test that DataclassSerializer respects cattrs unstructure hooks."""

    def test_serialize_with_custom_cattrs_hook__uses_hook__returns_unstructured_data(self) -> None:
        """
        Scenario: Serialize a dataclass that has a custom cattrs unstructure hook registered
        Expected Outcome: Uses the cattrs hook instead of manual field iteration,
                         avoiding exposure of internal fields like _data
        """
        from pyopenapi_gen.core.cattrs_converter import converter
        from pyopenapi_gen.core.utils import DataclassSerializer

        # Arrange - simulate generated type with _data field and custom hooks
        @dataclasses.dataclass
        class FieldDescriptor:
            type: str
            description: str | None = None

        @dataclasses.dataclass
        class PropertiesWithInternalData:
            """Simulates WorkflowAgentOutputSchemaProperties pattern."""

            _data: dict[str, FieldDescriptor] = dataclasses.field(default_factory=dict)

        # Register custom cattrs hooks (simulating generated code)
        def unstructure_hook(instance: PropertiesWithInternalData) -> dict[str, Any]:
            """Should return flat dict without _data wrapper."""
            return {key: converter.unstructure(value) for key, value in instance._data.items()}

        def structure_hook(data: dict[str, Any], _: type) -> PropertiesWithInternalData:
            """Should accept flat dict and create _data internally."""
            structured = {key: converter.structure(value, FieldDescriptor) for key, value in data.items()}
            return PropertiesWithInternalData(_data=structured)

        converter.register_unstructure_hook(PropertiesWithInternalData, unstructure_hook)
        converter.register_structure_hook(PropertiesWithInternalData, structure_hook)

        # Create instance with _data
        props = PropertiesWithInternalData(
            _data={
                "userId": FieldDescriptor(type="string", description="User ID"),
                "count": FieldDescriptor(type="number", description="Count"),
            }
        )

        # Act
        result = DataclassSerializer.serialize(props)

        # Assert - should NOT expose _data field, should use cattrs hook
        expected = {
            "userId": {"type": "string", "description": "User ID"},
            "count": {"type": "number", "description": "Count"},
        }
        assert result == expected
        assert "_data" not in result, "Internal _data field should not be exposed when cattrs hook exists"

        # Verify round-trip works
        from pyopenapi_gen.core.cattrs_converter import structure_from_dict

        restored = structure_from_dict(result, PropertiesWithInternalData)
        assert "userId" in restored._data
        assert "count" in restored._data

    def test_serialize_without_custom_hook__uses_manual_iteration__exposes_all_fields(self) -> None:
        """
        Scenario: Serialize a dataclass WITHOUT custom cattrs hooks
        Expected Outcome: Falls back to manual field iteration as before
        """
        from pyopenapi_gen.core.utils import DataclassSerializer

        # Arrange - regular dataclass without custom hooks
        @dataclasses.dataclass
        class RegularDataclass:
            name: str
            _internal: str = "private"

        instance = RegularDataclass(name="test", _internal="value")

        # Act
        result = DataclassSerializer.serialize(instance)

        # Assert - should expose all fields including _internal
        expected = {"name": "test", "_internal": "value"}
        assert result == expected

    def test_serialize_nested_with_cattrs_hooks__recursively_applies_hooks__returns_correct_structure(self) -> None:
        """
        Scenario: Serialize nested dataclasses where some have custom cattrs hooks
        Expected Outcome: Correctly applies hooks at each level of nesting
        """
        from pyopenapi_gen.core.cattrs_converter import converter
        from pyopenapi_gen.core.utils import DataclassSerializer

        # Arrange
        @dataclasses.dataclass
        class Inner:
            _data: dict[str, str] = dataclasses.field(default_factory=dict)

        @dataclasses.dataclass
        class Outer:
            name: str
            properties: Inner

        # Register hook for Inner only
        def unstructure_inner(instance: Inner) -> dict[str, str]:
            return dict(instance._data)

        converter.register_unstructure_hook(Inner, unstructure_inner)

        # Create nested structure
        inner = Inner(_data={"key1": "value1", "key2": "value2"})
        outer = Outer(name="test", properties=inner)

        # Act
        result = DataclassSerializer.serialize(outer)

        # Assert
        expected = {"name": "test", "properties": {"key1": "value1", "key2": "value2"}}
        assert result == expected
        assert "_data" not in result["properties"]

    def test_serialize_uses_relative_import__works_in_generated_code__no_import_error(self) -> None:
        """
        Scenario: Verify DataclassSerializer uses relative import to cattrs_converter
        Expected Outcome: Import works regardless of package name (regression test for hardcoded import bug)

        This is a regression test for the bug where line 398 had:
            from pyopenapi_gen.core.cattrs_converter import converter
        which failed in generated code (e.g., pyapis package).

        The fix uses relative import:
            from .cattrs_converter import unstructure_to_dict
        """
        from pyopenapi_gen.core.utils import DataclassSerializer

        # Arrange - simple dataclass
        @dataclasses.dataclass
        class TestData:
            field: str

        obj = TestData(field="value")

        # Act - this should work without ImportError
        try:
            result = DataclassSerializer.serialize(obj)
            # Assert
            assert result == {"field": "value"}
            # Test passed - relative import works
        except ImportError as e:
            pytest.fail(f"DataclassSerializer should use relative import, got ImportError: {e}")
