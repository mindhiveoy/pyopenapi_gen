from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SplitDocumentRequest:
    """
    Data model for SplitDocumentRequest

    Attributes:
        content (Optional[str]): No description provided.
        config (Optional[Dict[str, Any]]): No description provided.
    """

    content: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
