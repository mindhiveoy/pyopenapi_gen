import json
from enum import Enum, unique

__all__ = ["DataSourceTypeEnum"]


@unique
class DataSourceTypeEnum(str, Enum):
    """Enum for DataSource.type"""

    FILE_STORAGE = "fileStorage"
    WEB_SCRAPER = "webScraper"
    WORD_PRESS_SITE = "wordPressSite"

    @classmethod
    def from_json(cls, json_str: str) -> "DataSourceTypeEnum":
        """Create an instance from a JSON string"""
        return DataSourceTypeEnum(json.loads(json_str))
