"""
Defines the ParsingContext dataclass used to manage state during OpenAPI schema parsing.
"""

from __future__ import annotations

import logging
import os
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

        # Initialize unified cycle detection context
        # Import here to avoid circular imports
        from .unified_cycle_detection import UnifiedCycleContext

        # Get max depth from environment or default
        max_depth = int(os.environ.get("PYOPENAPI_MAX_DEPTH", 150))

        self.unified_cycle_context = UnifiedCycleContext(
            parsed_schemas=self.parsed_schemas, max_depth=max_depth  # Share the same parsed_schemas dict
        )

    def unified_enter_schema(self, schema_name: Optional[str]) -> Any:
        """Enter schema using unified cycle detection system."""
        from .unified_cycle_detection import unified_enter_schema

        result = unified_enter_schema(schema_name, self.unified_cycle_context)

        # Update legacy fields for backward compatibility
        self.recursion_depth = self.unified_cycle_context.recursion_depth
        self.cycle_detected = self.unified_cycle_context.cycle_detected
        self.currently_parsing = self.unified_cycle_context.schema_stack.copy()

        return result

    def unified_exit_schema(self, schema_name: Optional[str]) -> None:
        """Exit schema using unified cycle detection system."""
        from .unified_cycle_detection import unified_exit_schema

        unified_exit_schema(schema_name, self.unified_cycle_context)

        # Update legacy fields for backward compatibility
        self.recursion_depth = self.unified_cycle_context.recursion_depth
        self.currently_parsing = self.unified_cycle_context.schema_stack.copy()

    def clear_cycle_state(self) -> None:
        """Clear both legacy and unified cycle detection state."""
        # Clear legacy state
        self.currently_parsing.clear()
        self.recursion_depth = 0
        self.cycle_detected = False

        # Clear unified context state
        self.unified_cycle_context.schema_stack.clear()
        self.unified_cycle_context.schema_states.clear()
        self.unified_cycle_context.recursion_depth = 0
        self.unified_cycle_context.detected_cycles.clear()
        self.unified_cycle_context.depth_exceeded_schemas.clear()
        self.unified_cycle_context.cycle_detected = False

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

    def get_parsed_schemas_for_emitter(self) -> Dict[str, IRSchema]:
        # ---- START RESTORE ----
        return {
            name: schema
            for name, schema in self.parsed_schemas.items()
            if not getattr(schema, "_is_circular_ref", False)
            and not getattr(schema, "_from_unresolved_ref", False)
            and not getattr(schema, "_max_depth_exceeded_marker", False)
        }
        # ---- END RESTORE ----

    def is_schema_parsed(self, schema_name: str) -> bool:
        """Check if a schema with the given name has been parsed.

        Contracts:
            Preconditions:
                - schema_name is a valid string
            Postconditions:
                - Returns True if the schema exists in parsed_schemas, False otherwise
        """
        assert isinstance(schema_name, str), "schema_name must be a string"
        return schema_name in self.parsed_schemas

    def get_parsed_schema(self, schema_name: str) -> Optional["IRSchema"]:
        """Get a parsed schema by its name.

        Contracts:
            Preconditions:
                - schema_name is a valid string
            Postconditions:
                - Returns the IRSchema if it exists, None otherwise
        """
        assert isinstance(schema_name, str), "schema_name must be a string"
        return self.parsed_schemas.get(schema_name)
