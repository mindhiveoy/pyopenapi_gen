"""Tests for unified type service."""

from unittest.mock import Mock, patch
import pytest

from pyopenapi_gen import IROperation, IRResponse, IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.types.contracts.types import ResolvedType
from pyopenapi_gen.types.services.type_service import UnifiedTypeService


class TestUnifiedTypeService:
    """Test the unified type service."""
    
    @pytest.fixture
    def mock_context(self):
        """Mock render context."""
        context = Mock(spec=RenderContext)
        context.add_import = Mock()
        context.add_conditional_import = Mock()
        return context
    
    @pytest.fixture
    def service(self):
        """Type service instance."""
        return UnifiedTypeService({}, {})
    
    def test_resolve_schema_type__string_schema__returns_str(self, service, mock_context) -> None:
        """
        Scenario: Resolving string schema
        Expected Outcome: Returns str type
        """
        # Arrange
        schema = IRSchema(type="string")
        
        with patch.object(service.schema_resolver, 'resolve_schema') as mock_resolve:
            mock_resolve.return_value = ResolvedType(python_type="str")
            
            # Act
            result = service.resolve_schema_type(schema, mock_context)
            
            # Assert
            assert result == "str"
            mock_resolve.assert_called_once()
    
    def test_resolve_schema_type__optional_schema__returns_optional_type(self, service, mock_context) -> None:
        """
        Scenario: Resolving optional schema
        Expected Outcome: Returns Optional[Type] format
        """
        # Arrange
        schema = IRSchema(type="string")
        
        with patch.object(service.schema_resolver, 'resolve_schema') as mock_resolve:
            mock_resolve.return_value = ResolvedType(python_type="str", is_optional=True)
            
            # Act
            result = service.resolve_schema_type(schema, mock_context, required=False)
            
            # Assert
            assert result == "Optional[str]"
    
    def test_resolve_schema_type__forward_ref__returns_quoted_type(self, service, mock_context) -> None:
        """
        Scenario: Resolving forward reference schema
        Expected Outcome: Returns quoted type
        """
        # Arrange
        schema = IRSchema(name="User")
        
        with patch.object(service.schema_resolver, 'resolve_schema') as mock_resolve:
            mock_resolve.return_value = ResolvedType(python_type="User", is_forward_ref=True)
            
            # Act
            result = service.resolve_schema_type(schema, mock_context)
            
            # Assert
            assert result == '"User"'
    
    def test_resolve_operation_response_type__operation_with_response__returns_type(self, service, mock_context) -> None:
        """
        Scenario: Resolving operation response type
        Expected Outcome: Returns resolved response type
        """
        # Arrange
        operation = IROperation(
            operation_id="getUsers",
            method="GET",
            path="/users",
            summary="Get users",
            description="Get all users",
            responses=[]
        )
        
        with patch.object(service.response_resolver, 'resolve_operation_response') as mock_resolve:
            mock_resolve.return_value = ResolvedType(python_type="List[User]")
            
            # Act
            result = service.resolve_operation_response_type(operation, mock_context)
            
            # Assert
            assert result == "List[User]"
            mock_resolve.assert_called_once()
    
    def test_resolve_response_type__specific_response__returns_type(self, service, mock_context) -> None:
        """
        Scenario: Resolving specific response type
        Expected Outcome: Returns resolved type
        """
        # Arrange
        response = IRResponse(status_code="200", description="Success", content={})
        
        with patch.object(service.response_resolver, 'resolve_specific_response') as mock_resolve:
            mock_resolve.return_value = ResolvedType(python_type="User")
            
            # Act
            result = service.resolve_response_type(response, mock_context)
            
            # Assert
            assert result == "User"
            mock_resolve.assert_called_once()
    
    def test_format_resolved_type__optional_not_already_wrapped__adds_optional(self, service) -> None:
        """
        Scenario: Formatting optional type that's not already wrapped
        Expected Outcome: Wraps in Optional[]
        """
        # Arrange
        resolved = ResolvedType(python_type="str", is_optional=True)
        
        # Act
        result = service._format_resolved_type(resolved)
        
        # Assert
        assert result == "Optional[str]"
    
    def test_format_resolved_type__optional_already_wrapped__no_double_wrap(self, service) -> None:
        """
        Scenario: Formatting type that's already wrapped in Optional
        Expected Outcome: Doesn't double-wrap
        """
        # Arrange
        resolved = ResolvedType(python_type="Optional[str]", is_optional=True)
        
        # Act
        result = service._format_resolved_type(resolved)
        
        # Assert
        assert result == "Optional[str]"
    
    def test_format_resolved_type__forward_ref_not_quoted__adds_quotes(self, service) -> None:
        """
        Scenario: Formatting forward reference that's not quoted
        Expected Outcome: Adds quotes
        """
        # Arrange
        resolved = ResolvedType(python_type="User", is_forward_ref=True)
        
        # Act
        result = service._format_resolved_type(resolved)
        
        # Assert
        assert result == '"User"'
    
    def test_format_resolved_type__forward_ref_already_quoted__no_double_quote(self, service) -> None:
        """
        Scenario: Formatting forward reference that's already quoted
        Expected Outcome: Doesn't double-quote
        """
        # Arrange
        resolved = ResolvedType(python_type='"User"', is_forward_ref=True)
        
        # Act
        result = service._format_resolved_type(resolved)
        
        # Assert
        assert result == '"User"'