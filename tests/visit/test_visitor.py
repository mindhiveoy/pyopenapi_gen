"""Tests for visit.visitor module."""

import pytest
from unittest.mock import Mock
from typing import Any

from pyopenapi_gen.visit.visitor import Visitor, Registry
from pyopenapi_gen.context.render_context import RenderContext


class MockNode:
    """Mock node class for testing."""

    def __init__(self, name: str):
        self.name = name


class AnotherMockNode:
    """Another mock node class for testing."""

    def __init__(self, value: int):
        self.value = value


class TestVisitor(Visitor[MockNode, str]):
    """Test visitor implementation."""

    def visit_MockNode(self, node: MockNode, context: RenderContext) -> str:
        """Visit MockNode and return its name."""
        return f"visited_{node.name}"


class TestVisitorBase:
    """Test suite for base Visitor functionality."""

    def test_visitor__visit_with_specific_method__calls_correct_method(self):
        """Scenario: Visit node with specific visitor method.

        Expected Outcome: Specific visitor method is called.
        """
        # Arrange
        visitor = TestVisitor()
        node = MockNode("test")
        context = Mock(spec=RenderContext)

        # Act
        result = visitor.visit(node, context)

        # Assert
        assert result == "visited_test"

    def test_visitor__visit_without_specific_method__calls_generic_visit(self):
        """Scenario: Visit node without specific visitor method.

        Expected Outcome: generic_visit is called and raises NotImplementedError.
        """
        # Arrange
        visitor = TestVisitor()
        node = AnotherMockNode(42)  # No visit_AnotherMockNode method
        context = Mock(spec=RenderContext)

        # Expected Outcome: NotImplementedError is raised
        with pytest.raises(NotImplementedError, match="No visit_AnotherMockNode method defined"):
            visitor.visit(node, context)

    def test_visitor__generic_visit__raises_not_implemented_error(self):
        """Scenario: Call generic_visit directly.

        Expected Outcome: NotImplementedError is raised with correct message.
        """
        # Arrange
        visitor = Visitor()
        node = MockNode("test")
        context = Mock(spec=RenderContext)

        # Expected Outcome: NotImplementedError is raised
        with pytest.raises(NotImplementedError, match="No visit_MockNode method defined"):
            visitor.generic_visit(node, context)


class TestRegistry:
    """Test suite for Registry functionality."""

    def test_registry__init__creates_empty_registry(self):
        """Scenario: Initialize new registry.

        Expected Outcome: Registry is empty.
        """
        # Act
        registry = Registry[MockNode, str]()

        # Assert
        assert registry.get_visitor(MockNode) is None

    def test_registry__register_visitor__stores_visitor(self):
        """Scenario: Register visitor for node type.

        Expected Outcome: Visitor is stored and retrievable.
        """
        # Arrange
        registry = Registry[MockNode, str]()

        def test_visitor(node: MockNode, context: RenderContext) -> str:
            return f"handled_{node.name}"

        # Act
        registry.register(MockNode, test_visitor)

        # Assert
        retrieved = registry.get_visitor(MockNode)
        assert retrieved is test_visitor

    def test_registry__get_visitor_unregistered_type__returns_none(self):
        """Scenario: Get visitor for unregistered node type.

        Expected Outcome: None is returned.
        """
        # Arrange
        registry = Registry[MockNode, str]()

        # Act
        result = registry.get_visitor(MockNode)

        # Assert
        assert result is None

    def test_registry__register_multiple_types__stores_all(self):
        """Scenario: Register visitors for multiple node types.

        Expected Outcome: All visitors are stored correctly.
        """
        # Arrange
        registry = Registry[Any, str]()

        def test_visitor(node: MockNode, context: RenderContext) -> str:
            return f"test_{node.name}"

        def another_visitor(node: AnotherMockNode, context: RenderContext) -> str:
            return f"another_{node.value}"

        # Act
        registry.register(MockNode, test_visitor)
        registry.register(AnotherMockNode, another_visitor)

        # Assert
        assert registry.get_visitor(MockNode) is test_visitor
        assert registry.get_visitor(AnotherMockNode) is another_visitor

    def test_registry__register_same_type_twice__overwrites_previous(self):
        """Scenario: Register visitor for same type twice.

        Expected Outcome: Second registration overwrites first.
        """
        # Arrange
        registry = Registry[MockNode, str]()

        def first_visitor(node: MockNode, context: RenderContext) -> str:
            return "first"

        def second_visitor(node: MockNode, context: RenderContext) -> str:
            return "second"

        # Act
        registry.register(MockNode, first_visitor)
        registry.register(MockNode, second_visitor)

        # Assert
        retrieved = registry.get_visitor(MockNode)
        assert retrieved is second_visitor
        assert retrieved is not first_visitor

    def test_registry__functional_test__visitors_work_correctly(self):
        """Scenario: End-to-end test of registry functionality.

        Expected Outcome: Registered visitors work as expected.
        """
        # Arrange
        registry = Registry[MockNode, str]()
        context = Mock(spec=RenderContext)

        def visitor_func(node: MockNode, context: RenderContext) -> str:
            return f"processed_{node.name}"

        registry.register(MockNode, visitor_func)
        node = MockNode("example")

        # Act
        visitor_func = registry.get_visitor(MockNode)
        result = visitor_func(node, context) if visitor_func else None

        # Assert
        assert result == "processed_example"
