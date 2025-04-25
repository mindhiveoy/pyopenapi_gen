from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class GetSystemHealthStatusResponse:
    uptime: Optional[float] = None  #
    timestamp: Optional[float] = None  #
    status: Optional[str] = None  #
    services: Optional[Dict[str, Any]] = None  #
