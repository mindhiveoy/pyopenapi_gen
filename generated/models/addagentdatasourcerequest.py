from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class AddAgentDataSourceRequest:
    dataSourceId: str = field(default_factory=str)  #
    description: Optional[str] = None  #
    instructions: Optional[str] = None  #
    config: Optional[Dict[str, Any]] = None  #
