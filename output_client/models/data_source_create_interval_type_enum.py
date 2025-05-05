import json
from enum import Enum, unique

__all__ = ["DataSourceCreateIntervalTypeEnum"]


@unique
class DataSourceCreateIntervalTypeEnum(str, Enum):
    """Enum for DataSourceCreate.intervalType"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEB_HOOK = "webHook"

    @classmethod
    def from_json(cls, json_str: str) -> "DataSourceCreateIntervalTypeEnum":
        """Create an instance from a JSON string"""
        return DataSourceCreateIntervalTypeEnum(json.loads(json_str))
