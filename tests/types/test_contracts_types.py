"""Tests for types.contracts.types module."""

import pytest
from pyopenapi_gen.types.contracts.types import TypeResolutionError, ResolvedType


class TestTypeResolutionError:
    """Test suite for TypeResolutionError."""

    def test_type_resolution_error__basic_creation__works(self):
        """Scenario: Create basic TypeResolutionError.
        
        Expected Outcome: Exception is created successfully.
        """
        # Act
        error = TypeResolutionError("Test error message")
        
        # Assert
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_type_resolution_error__empty_message__works(self):
        """Scenario: Create TypeResolutionError with empty message.
        
        Expected Outcome: Exception is created successfully.
        """
        # Act
        error = TypeResolutionError()
        
        # Assert
        assert isinstance(error, Exception)


class TestResolvedType:
    """Test suite for ResolvedType."""

    def test_resolved_type__basic_creation__works(self):
        """Scenario: Create basic ResolvedType.
        
        Expected Outcome: Instance is created with defaults.
        """
        # Act
        resolved = ResolvedType(python_type="str")
        
        # Assert
        assert resolved.python_type == "str"
        assert resolved.needs_import is False
        assert resolved.import_module is None
        assert resolved.import_name is None
        assert resolved.is_optional is False
        assert resolved.is_forward_ref is False
        assert resolved.was_unwrapped is False

    def test_resolved_type__with_import__works(self):
        """Scenario: Create ResolvedType with import info.
        
        Expected Outcome: Instance is created successfully.
        """
        # Act
        resolved = ResolvedType(
            python_type="User",
            needs_import=True,
            import_module="myapp.models",
            import_name="User"
        )
        
        # Assert
        assert resolved.python_type == "User"
        assert resolved.needs_import is True
        assert resolved.import_module == "myapp.models"
        assert resolved.import_name == "User"

    def test_resolved_type__needs_import_without_module__raises_error(self):
        """Scenario: Create ResolvedType with needs_import but no module.
        
        Expected Outcome: ValueError is raised.
        """
        # Expected Outcome: ValueError is raised
        with pytest.raises(ValueError, match="needs_import=True requires import_module"):
            ResolvedType(
                python_type="User",
                needs_import=True,
                import_name="User"
                # Missing import_module
            )

    def test_resolved_type__needs_import_without_name__raises_error(self):
        """Scenario: Create ResolvedType with needs_import but no name.
        
        Expected Outcome: ValueError is raised.
        """
        # Expected Outcome: ValueError is raised  
        with pytest.raises(ValueError, match="needs_import=True requires import_name"):
            ResolvedType(
                python_type="User",
                needs_import=True,
                import_module="myapp.models"
                # Missing import_name
            )

    def test_resolved_type__all_flags_true__works(self):
        """Scenario: Create ResolvedType with all boolean flags set.
        
        Expected Outcome: Instance is created with all flags.
        """
        # Act
        resolved = ResolvedType(
            python_type="Optional[User]",
            needs_import=True,
            import_module="myapp.models", 
            import_name="User",
            is_optional=True,
            is_forward_ref=True,
            was_unwrapped=True
        )
        
        # Assert
        assert resolved.is_optional is True
        assert resolved.is_forward_ref is True
        assert resolved.was_unwrapped is True
        assert resolved.needs_import is True