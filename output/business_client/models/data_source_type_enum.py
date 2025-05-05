from enum import Enum


class DataSourceTypeEnum(Enum):
    """Enum for DataSource.type"""

    FILE_STORAGE = "fileStorage"
    WEB_SCRAPER = "webScraper"
    WORD_PRESS_SITE = "wordPressSite"
