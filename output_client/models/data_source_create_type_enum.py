import json
from enum import Enum, unique

__all__ = ["DataSourceCreateTypeEnum"]


@unique
class DataSourceCreateTypeEnum(str, Enum):
    """Enum for DataSourceCreate.type"""

    FILE_STORAGE = "fileStorage"
    WEB_SCRAPER = "webScraper"
    WORD_PRESS_SITE = "wordPressSite"

    @classmethod
    def from_json(cls, json_str: str) -> "DataSourceCreateTypeEnum":
        """Create an instance from a JSON string"""
        return DataSourceCreateTypeEnum(json.loads(json_str))
