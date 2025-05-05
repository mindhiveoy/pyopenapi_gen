from enum import Enum


class DataSourceIntervalTypeEnum(Enum):
    """Enum for DataSource.intervalType"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEB_HOOK = "webHook"
