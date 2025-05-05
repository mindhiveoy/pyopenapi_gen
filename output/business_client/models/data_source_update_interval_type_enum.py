from enum import Enum


class DataSourceUpdateIntervalTypeEnum(Enum):
    """Enum for DataSourceUpdate.intervalType"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEB_HOOK = "webHook"
