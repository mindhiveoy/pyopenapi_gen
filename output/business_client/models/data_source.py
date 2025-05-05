from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from .data_source_interval_type_enum import DataSourceIntervalTypeEnum
from .data_source_type_enum import DataSourceTypeEnum


@dataclass
class DataSource:
    """
    Data source model for managing different types of knowledge sources. Manages content repositories, their configurations, and integration settings for AI access.

    Attributes:
        type (DataSourceTypeEnum): No description provided.
        interval_type (DataSourceIntervalTypeEnum): No description provided.
        id (str): No description provided.
        name (str): No description provided.
        description (Optional[str]): No description provided.
        tenant_id (Optional[str]): No description provided.
        vector_database_id (Optional[str]): No description provided.
        vector_index_id (Optional[str]): No description provided.
        embed_model_id (Optional[str]): No description provided.
        interval_value (int): No description provided.
        target_urls (List[str]): No description provided.
        config (Dict[str, Any]): Source-specific configuration options for connection and processing parameters
        created_at (datetime): No description provided.
        updated_at (datetime): No description provided.
    """

    type: DataSourceTypeEnum
    interval_type: DataSourceIntervalTypeEnum
    id: str
    name: str
    description: Optional[str]
    tenant_id: Optional[str]
    vector_database_id: Optional[str]
    vector_index_id: Optional[str]
    embed_model_id: Optional[str]
    interval_value: int
    created_at: datetime
    updated_at: datetime
