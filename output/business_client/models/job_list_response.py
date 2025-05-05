from dataclasses import dataclass, field
from typing import List
from .job import Job
from .pagination_meta import PaginationMeta


@dataclass
class JobListResponse:
    """
    Paginated job list with optional included relations

    Attributes:
        data (List[Job]): No description provided.
        meta (PaginationMeta): Pagination metadata for list responses. Provides information about result set size and navigation.
    """

    meta: PaginationMeta
