from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class CleanDocumentRequest:
    """
    Schema for cleaning and validating document content
    """

    content: str = field(default_factory=str)  # Document content to clean and validate
    options: Optional[Optional[Dict[str, Any]]] = None  # Cleaning options
