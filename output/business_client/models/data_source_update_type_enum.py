from enum import Enum


class DataSourceUpdateTypeEnum(Enum):
    """Enum for DataSourceUpdate.type"""

    FILE_STORAGE = "fileStorage"
    WEB_SCRAPER = "webScraper"
    WORD_PRESS_SITE = "wordPressSite"
