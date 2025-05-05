from enum import Enum


class DataSourceCreateIntervalTypeEnum(Enum):
    """Enum for DataSourceCreate.intervalType"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEB_HOOK = "webHook"
