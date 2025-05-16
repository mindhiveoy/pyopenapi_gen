"""
Defines the ParsingContext dataclass used to manage state during OpenAPI schema parsing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Set, Tuple

if TYPE_CHECKING:
    from pyopenapi_gen import IRSchema
    # from pyopenapi_gen.core.utils import NameSanitizer # If needed later

logger = logging.getLogger(__name__)


@dataclass
class ParsingContext:
    """Manages shared state and context during the schema parsing process."""

    raw_spec_schemas: Mapping[str, Any] = field(default_factory=dict)
    raw_spec_components: Mapping[str, Any] = field(default_factory=dict)
    parsed_schemas: Dict[str, IRSchema] = field(default_factory=dict)
    visited_refs: Set[str] = field(default_factory=set)
    global_schema_names: Set[str] = field(default_factory=set)
    package_root_name: Optional[str] = None
    # name_sanitizer: NameSanitizer = field(default_factory=NameSanitizer) # Decided to instantiate where needed for now
    collected_warnings: List[str] = field(default_factory=list)  # For collecting warnings from helpers

    # Cycle detection
    currently_parsing: Set[str] = field(default_factory=set)  # Track schemas currently being parsed
    recursion_depth: int = field(default=0)
    max_recursion_depth: int = field(default=0)
    cycle_detected: bool = field(default=False)
    parsing_path: List[str] = field(default_factory=list)  # Path of schemas being parsed

    def enter_schema(self, name: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Track entry into parsing a schema to detect cycles.

        Args:
            name: The name of the schema being parsed

        Returns:
            Tuple[bool, Optional[str]]: (is_cycle_detected, cycle_path_if_detected)
            - If cycle detected, returns (True, cycle path string)
            - If no cycle, returns (False, None)
        """
        self.recursion_depth += 1
        self.max_recursion_depth = max(self.max_recursion_depth, self.recursion_depth)

        # Track only named schemas for cycle detection
        if name:
            # Check if this schema is already being parsed (cycle)
            if name in self.currently_parsing:
                cycle_path = " -> ".join(self.parsing_path + [name])
                self.cycle_detected = True
                logger.warning(f"CYCLE DETECTED: {cycle_path}")
                return True, cycle_path

            self.currently_parsing.add(name)
            self.parsing_path.append(name)

        return False, None

    def exit_schema(self, name: Optional[str]) -> None:
        """
        Track exit from parsing a schema.

        Args:
            name: The name of the schema that was being parsed
        """
        self.recursion_depth -= 1

        if name:
            if name in self.currently_parsing:
                self.currently_parsing.remove(name)

            # Only remove from path if it's the last element (handles recursive calls correctly)
            if self.parsing_path and self.parsing_path[-1] == name:
                self.parsing_path.pop()
