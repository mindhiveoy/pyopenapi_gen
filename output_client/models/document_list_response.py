from dataclasses import dataclass

from .pagination_meta import PaginationMeta


@dataclass
class DocumentListResponse:
    """
    Paginated document list response

    Attributes:
        data (List[Document]): No description provided.
        meta (PaginationMeta): Pagination metadata for list responses. Provides information about result set size and navigation.
    """

    meta: PaginationMeta
