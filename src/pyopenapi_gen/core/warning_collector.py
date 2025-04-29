"""Warning collector for the IR layer.

This module provides utilities to collect actionable warnings
for incomplete metadata in the IR (e.g., missing tags, descriptions).
"""

from dataclasses import dataclass
from typing import List

from pyopenapi_gen import IRSpec

__all__ = ["WarningReport", "WarningCollector"]


@dataclass
class WarningReport:
    """Structured warning with a code, human message, and remediation hint."""

    code: str
    message: str
    hint: str


class WarningCollector:
    """Collects warnings about missing or incomplete information in IRSpec."""

    def __init__(self) -> None:
        self.warnings: List[WarningReport] = []

    def collect(self, spec: IRSpec) -> List[WarningReport]:
        """Walks an IRSpec and accumulates warnings."""
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
