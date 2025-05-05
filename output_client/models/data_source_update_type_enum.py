import json
from enum import Enum, unique

__all__ = ["DataSourceUpdateTypeEnum"]


@unique
class DataSourceUpdateTypeEnum(str, Enum):
    """Enum for DataSourceUpdate.type"""

    FILE_STORAGE = "fileStorage"
    WEB_SCRAPER = "webScraper"
    WORD_PRESS_SITE = "wordPressSite"

    @classmethod
    def from_json(cls, json_str: str) -> "DataSourceUpdateTypeEnum":
        """Create an instance from a JSON string"""
        return DataSourceUpdateTypeEnum(json.loads(json_str))
