from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class PaginationMeta:
    """
    Pagination metadata for list responses. Provides information about
    result set size and navigation.
    """

    total: Optional[int] = None  # Total number of items available
    page: Optional[int] = None  # Current page number (1-based)
    pageSize: Optional[int] = None  # Number of items per page
    totalPages: Optional[int] = None  # Total number of pages available
