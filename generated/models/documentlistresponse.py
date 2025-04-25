from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DocumentListResponse:
    """
    Paginated document list response
    """

    data: List[Document] = field(default_factory=list)  #
    meta: PaginationMeta = field(
        default_factory=dict
    )  # Pagination metadata for list responses. Provides information about result set size and navigation.
