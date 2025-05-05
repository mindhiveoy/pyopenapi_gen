from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class CleanDocumentRequest:
    """
    Schema for cleaning and validating document content

    Attributes:
        content (str): Document content to clean and validate
        options (Optional[Dict[str, Any]]): Cleaning options
    """

    content: str
    options: Optional[Dict[str, Any]] = None
