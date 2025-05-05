from dataclasses import dataclass


@dataclass
class DataSourceResponse:
    """
    Data model for DataSourceResponse

    Attributes:
        data (Dict[str, Any]): Data source model for managing different types of knowledge sources. Manages content repositories, their configurations, and integration settings for AI access.
    """
