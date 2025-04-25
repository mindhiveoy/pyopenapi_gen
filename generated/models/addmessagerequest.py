from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class AddMessageRequest:
    message: str = field(default_factory=str)  # The message content
    role: str = field(default_factory=str)  # The role of the message sender
