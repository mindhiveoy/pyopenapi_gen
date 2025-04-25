from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class IndexDocumentRequest:
    document: Optional[Dict[str, Any]] = None  #
    datasource: Optional[Dict[str, Any]] = None  #
