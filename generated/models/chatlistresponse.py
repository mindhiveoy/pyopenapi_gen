from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatListResponse:
    data: Dict[str, Any] = field(default_factory=dict)  #
    meta: Dict[str, Any] = field(default_factory=dict)  #
