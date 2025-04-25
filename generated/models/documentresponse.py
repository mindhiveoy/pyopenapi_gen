from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DocumentResponse:
    """
    Document response with data wrapper
    """

    data: Document = field(
        default_factory=dict
    )  # Document model representing content units for AI knowledge retrieval and processing.
