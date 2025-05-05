import json
from enum import Enum, unique

__all__ = ["DataSourceUpdateIntervalTypeEnum"]


@unique
class DataSourceUpdateIntervalTypeEnum(str, Enum):
    """Enum for DataSourceUpdate.intervalType"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEB_HOOK = "webHook"

    @classmethod
    def from_json(cls, json_str: str) -> "DataSourceUpdateIntervalTypeEnum":
        """Create an instance from a JSON string"""
        return DataSourceUpdateIntervalTypeEnum(json.loads(json_str))
