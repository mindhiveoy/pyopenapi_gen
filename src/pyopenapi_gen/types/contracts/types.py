"""Core types for type resolution."""

from dataclasses import dataclass
from typing import Optional


class TypeResolutionError(Exception):
    """Raised when type resolution fails."""
    pass


@dataclass
class ResolvedType:
    """Result of type resolution."""
    
    python_type: str
    needs_import: bool = False
    import_module: Optional[str] = None
    import_name: Optional[str] = None
    is_optional: bool = False
    is_forward_ref: bool = False
    was_unwrapped: bool = False
    
    def __post_init__(self) -> None:
        """Validate resolved type data."""
        if self.needs_import and not self.import_module:
            raise ValueError("needs_import=True requires import_module")
        if self.needs_import and not self.import_name:
            raise ValueError("needs_import=True requires import_name")