from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class DetectPlatformJobRequest:
    url: Optional[str] = None  # URL of the website to detect platform for
