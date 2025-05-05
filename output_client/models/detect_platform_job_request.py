from dataclasses import dataclass
from typing import Optional


@dataclass
class DetectPlatformJobRequest:
    """
    Data model for DetectPlatformJobRequest

    Attributes:
        url (Optional[str]): URL of the website to detect platform for
    """

    url: Optional[str] = None
