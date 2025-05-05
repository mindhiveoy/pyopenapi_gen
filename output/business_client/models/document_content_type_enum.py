from enum import Enum


class DocumentContentTypeEnum(Enum):
    """Format of the document content (e.g., text, markdown, html)"""

    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
