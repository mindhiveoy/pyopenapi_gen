import json
from enum import Enum, unique

__all__ = ["JobUpdateTypeEnum"]


@unique
class JobUpdateTypeEnum(str, Enum):
    """Type of job"""

    WEB_SCRAPER = "webScraper"
    WORD_PRESS_SITE = "wordPressSite"
    FILE_STORAGE = "fileStorage"
    AGENT_REPORT = "agentReport"

    @classmethod
    def from_json(cls, json_str: str) -> "JobUpdateTypeEnum":
        """Create an instance from a JSON string"""
        return JobUpdateTypeEnum(json.loads(json_str))
