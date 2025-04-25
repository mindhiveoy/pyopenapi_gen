from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TenantListResponse:
    """
    Paginated tenant list with optional included relations
    """

    data: Optional[List[Tenant]] = None  #
    meta: Optional[PaginationMeta] = (
        None  # Pagination metadata for list responses. Provides information about result set size and navigation.
    )
