from enum import Enum


class JobUpdateTypeEnum(Enum):
    """Type of job"""

    WEB_SCRAPER = "webScraper"
    WORD_PRESS_SITE = "wordPressSite"
    FILE_STORAGE = "fileStorage"
    AGENT_REPORT = "agentReport"
