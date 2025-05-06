"""
Warning collector for the IR layer.

This module provides utilities to collect actionable warnings for incomplete
metadata in the IR (Intermediate Representation) objects, such as missing tags,
descriptions, or other quality issues in the OpenAPI spec that may lead to
suboptimal generated code.
"""

from dataclasses import dataclass
from typing import List

from pyopenapi_gen import IRSpec

__all__ = ["WarningReport", "WarningCollector"]


@dataclass
class WarningReport:
    """
    Structured warning with a code, human-readable message, and remediation hint.
    
    Attributes:
        code: A machine-readable warning code (e.g., "missing_tags")
        message: A human-readable description of the warning
        hint: A suggestion for how to fix or improve the issue
    """

    code: str
    message: str
    hint: str


class WarningCollector:
    """
    Collects warnings about missing or incomplete information in an IRSpec.
    
    This class analyzes an IRSpec object and identifies potential issues or
    missing information that might lead to lower quality generated code or
    documentation. It provides actionable warnings with hints for improvement.
    
    Attributes:
        warnings: List of collected WarningReport objects
    """

    def __init__(self) -> None:
        """Initialize a new WarningCollector with an empty warning list."""
        self.warnings: List[WarningReport] = []

    def collect(self, spec: IRSpec) -> List[WarningReport]:
        """
        Analyze an IRSpec and collect warnings about potential issues.
        
        This method traverses the IRSpec and checks for common issues like
        missing tags, descriptions, or other metadata that would improve
        the quality of the generated code.
        
        Args:
            spec: The IRSpec object to analyze
            
        Returns:
            A list of WarningReport objects describing identified issues
        """
        # Operations without tags
        for op in spec.operations:
            if not op.tags:
                self.warnings.append(
                    WarningReport(
                        code="missing_tags",
                        message=f"Operation '{op.operation_id}' has no tags.",
                        hint="Add tags to operations in the OpenAPI spec.",
                    )
                )
            # Missing summary and description
            if not op.summary and not op.description:
                self.warnings.append(
                    WarningReport(
                        code="missing_description",
                        message=f"Operation '{op.operation_id}' missing summary/description.",
                        hint="Provide a summary or description for the operation.",
                    )
                )
        return self.warnings
