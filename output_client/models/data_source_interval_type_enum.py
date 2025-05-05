import json
from enum import Enum, unique

__all__ = ["DataSourceIntervalTypeEnum"]


@unique
class DataSourceIntervalTypeEnum(str, Enum):
    """Enum for DataSource.intervalType"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEB_HOOK = "webHook"

    @classmethod
    def from_json(cls, json_str: str) -> "DataSourceIntervalTypeEnum":
        """Create an instance from a JSON string"""
        return DataSourceIntervalTypeEnum(json.loads(json_str))
