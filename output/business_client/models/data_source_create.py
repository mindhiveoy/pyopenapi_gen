from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from .data_source_create_interval_type_enum import DataSourceCreateIntervalTypeEnum
from .data_source_create_type_enum import DataSourceCreateTypeEnum


@dataclass
class DataSourceCreate:
    """
    Schema for creating a new DataSource

    Attributes:
        name (str): No description provided.
        type (DataSourceCreateTypeEnum): No description provided.
        interval_type (DataSourceCreateIntervalTypeEnum): No description provided.
        interval_value (int): No description provided.
        description (Optional[str]): No description provided.
        tenant_id (Optional[str]): No description provided.
        vector_database_id (Optional[str]): No description provided.
        vector_index_id (Optional[str]): No description provided.
        embed_model_id (Optional[str]): No description provided.
        config (Optional[Dict[str, Any]]): Source-specific configuration options for connection and processing parameters
        target_urls (Optional[List[str]]): No description provided.
    """

    name: str
    type: DataSourceCreateTypeEnum
    interval_type: DataSourceCreateIntervalTypeEnum
    interval_value: int
    description: Optional[str] = None
    tenant_id: Optional[str] = None
    vector_database_id: Optional[str] = None
    vector_index_id: Optional[str] = None
    embed_model_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    target_urls: Optional[List[str]] = None
