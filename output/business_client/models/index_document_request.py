from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class IndexDocumentRequest:
    """
    Data model for IndexDocumentRequest

    Attributes:
        document (Optional[Any]): No description provided.
        datasource (Optional[Dict[str, Any]]): No description provided.
    """

    document: Optional[Any] = None
    datasource: Optional[Dict[str, Any]] = None
