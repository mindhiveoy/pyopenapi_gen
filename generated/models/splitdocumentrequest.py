from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class SplitDocumentRequest:
    content: Optional[str] = None  #
    config: Optional[Dict[str, Any]] = None  #
