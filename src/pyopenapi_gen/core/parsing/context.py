"""
Defines the ParsingContext dataclass used to manage state during OpenAPI schema parsing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Set, Tuple

if TYPE_CHECKING:
    from pyopenapi_gen import IRSchema
    # from pyopenapi_gen.core.utils import NameSanitizer # If needed later

logger = logging.getLogger(__name__)


@dataclass
class ParsingContext:
    """Manages shared state and context during the schema parsing process."""

    raw_spec_schemas: Dict[str, Mapping[str, Any]] = field(default_factory=dict)
    raw_spec_components: Mapping[str, Any] = field(default_factory=dict)
    parsed_schemas: Dict[str, IRSchema] = field(default_factory=dict)
    visited_refs: Set[str] = field(default_factory=set)
    global_schema_names: Set[str] = field(default_factory=set)
    package_root_name: Optional[str] = None
    # name_sanitizer: NameSanitizer = field(default_factory=NameSanitizer) # Decided to instantiate where needed for now
    collected_warnings: List[str] = field(default_factory=list)  # For collecting warnings from helpers

    # Cycle detection
    currently_parsing: List[str] = field(default_factory=list)
    recursion_depth: int = 0
    cycle_detected: bool = False

    def __post_init__(self) -> None:
        # Initialize logger for the context instance if needed, or rely on module logger
        self.logger = logger  # or logging.getLogger(f"{__name__}.ParsingContext")

    def enter_schema(self, schema_name: Optional[str]) -> Tuple[bool, Optional[str]]:
        self.recursion_depth += 1

        if schema_name is None:
            return False, None

        # Named cycle detection using ordered list currently_parsing
        if schema_name in self.currently_parsing:
            self.cycle_detected = True
            try:
                start_index = self.currently_parsing.index(schema_name)
                # Path is from the first occurrence of schema_name to the current end of stack
                cycle_path_list = self.currently_parsing[start_index:]
            except ValueError:  # Should not happen
                cycle_path_list = list(self.currently_parsing)  # Fallback

            cycle_path_list.append(schema_name)  # Add the re-entrant schema_name to show the loop
            cycle_path_str = " -> ".join(cycle_path_list)

            self.logger.warning(f"CYCLE DETECTED: {cycle_path_str}")
            return True, cycle_path_str

        self.currently_parsing.append(schema_name)
        return False, None

    def exit_schema(self, schema_name: Optional[str]) -> None:
        if self.recursion_depth == 0:
            self.logger.error("Cannot exit schema: recursion depth would go below zero.")
            return

        self.recursion_depth -= 1
        if schema_name is not None:
            if self.currently_parsing and self.currently_parsing[-1] == schema_name:
                self.currently_parsing.pop()
            elif (
                schema_name in self.currently_parsing
            ):  # Not last on stack but present: indicates mismatched enter/exit or error
                self.logger.error(
                    f"Exiting schema '{schema_name}' which is not at the top of the parsing stack. "
                    f"Stack: {self.currently_parsing}. This indicates an issue."
                )
                # Attempt to remove it to prevent it being stuck, though this is a recovery attempt.
                try:
                    self.currently_parsing.remove(schema_name)
                except ValueError:
                    pass  # Should not happen if it was in the list.
            # If schema_name is None, or (it's not None and not in currently_parsing), do nothing to currently_parsing.
            # The latter case could be if exit_schema is called for a schema_name that wasn't pushed
            # (e.g., after yielding a placeholder, where the original enter_schema didn't add it because it was already a cycle).

    def reset_for_new_parse(self) -> None:
        self.recursion_depth = 0
        self.cycle_detected = False
        self.currently_parsing.clear()
        self.parsed_schemas.clear()

    def get_current_path_for_logging(self) -> str:
        """Helper to get a string representation of the current parsing path for logs."""
        return " -> ".join(self.currently_parsing)
