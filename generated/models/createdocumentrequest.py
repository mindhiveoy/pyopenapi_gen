from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class CreateDocumentRequest:
    file: Optional[bytes] = None  #
    data: Optional[str] = None  # JSON string with additional metadata
