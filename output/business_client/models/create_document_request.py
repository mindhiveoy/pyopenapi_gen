from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateDocumentRequest:
    """
    Data model for CreateDocumentRequest

    Attributes:
        file (Optional[str]): No description provided.
        data (Optional[str]): JSON string with additional metadata
    """

    file: Optional[str] = None
    data: Optional[str] = None
