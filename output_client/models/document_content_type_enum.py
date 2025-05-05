import json
from enum import Enum, unique

__all__ = ["DocumentContentTypeEnum"]


@unique
class DocumentContentTypeEnum(str, Enum):
    """Format of the document content (e.g., text, markdown, html)"""

    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"

    @classmethod
    def from_json(cls, json_str: str) -> "DocumentContentTypeEnum":
        """Create an instance from a JSON string"""
        return DocumentContentTypeEnum(json.loads(json_str))
