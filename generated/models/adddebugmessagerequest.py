from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class AddDebugMessageRequest:
    messages: List[Dict[str, Any]] = field(
        default_factory=list
    )  # Array of debug messages
