import json
from enum import Enum, unique

__all__ = ["JobTypeEnum"]


@unique
class JobTypeEnum(str, Enum):
    """Type of the job"""

    WEB_SCRAPER = "webScraper"
    WORD_PRESS_SITE = "wordPressSite"
    FILE_STORAGE = "fileStorage"
    AGENT_REPORT = "agentReport"

    @classmethod
    def from_json(cls, json_str: str) -> "JobTypeEnum":
        """Create an instance from a JSON string"""
        return JobTypeEnum(json.loads(json_str))
