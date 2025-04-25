from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class UpdateAgentDataSourceRequest:
    description: Optional[str] = None  #
    instructions: Optional[str] = None  #
    config: Optional[Dict[str, Any]] = None  #
