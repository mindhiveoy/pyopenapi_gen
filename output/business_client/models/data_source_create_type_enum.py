from enum import Enum


class DataSourceCreateTypeEnum(Enum):
    """Enum for DataSourceCreate.type"""

    FILE_STORAGE = "fileStorage"
    WEB_SCRAPER = "webScraper"
    WORD_PRESS_SITE = "wordPressSite"
