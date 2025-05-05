from dataclasses import dataclass
from typing import Optional


@dataclass
class PaginationMeta:
    """
    Pagination metadata for list responses. Provides information about result set size and navigation.

    Attributes:
        total (Optional[int]): Total number of items available
        page (Optional[int]): Current page number (1-based)
        page_size (Optional[int]): Number of items per page
        total_pages (Optional[int]): Total number of pages available
    """

    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    total_pages: Optional[int] = None
