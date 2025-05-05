from dataclasses import dataclass, field
from typing import List
from .job_execution import JobExecution
from .pagination_meta import PaginationMeta


@dataclass
class JobExecutionListResponse:
    """
    Paginated job execution list with optional included relations

    Attributes:
        data (List[JobExecution]): No description provided.
        meta (PaginationMeta): Pagination metadata for list responses. Provides information about result set size and navigation.
    """

    meta: PaginationMeta
