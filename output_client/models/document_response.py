from dataclasses import dataclass

from .document import Document


@dataclass
class DocumentResponse:
    """
    Document response with data wrapper

    Attributes:
        data (Document): Document model representing content units for AI knowledge retrieval and processing.
    """

    data: Document
