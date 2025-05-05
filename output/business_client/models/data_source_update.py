from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from .data_source_update_interval_type_enum import DataSourceUpdateIntervalTypeEnum
from .data_source_update_type_enum import DataSourceUpdateTypeEnum


@dataclass
class DataSourceUpdate:
    """
    Schema for updating an existing DataSource

    Attributes:
        name (Optional[str]): No description provided.
        description (Optional[str]): No description provided.
        type (Optional[DataSourceUpdateTypeEnum]): No description provided.
        config (Optional[Dict[str, Any]]): Source-specific configuration options for connection and processing parameters
        vector_database_id (Optional[str]): No description provided.
        vector_index_id (Optional[str]): No description provided.
        embed_model_id (Optional[str]): No description provided.
        interval_type (Optional[DataSourceUpdateIntervalTypeEnum]): No description provided.
        interval_value (Optional[int]): No description provided.
        target_urls (Optional[List[str]]): No description provided.
    """

    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[DataSourceUpdateTypeEnum] = None
    config: Optional[Dict[str, Any]] = None
    vector_database_id: Optional[str] = None
    vector_index_id: Optional[str] = None
    embed_model_id: Optional[str] = None
    interval_type: Optional[DataSourceUpdateIntervalTypeEnum] = None
    interval_value: Optional[int] = None
    target_urls: Optional[List[str]] = None
