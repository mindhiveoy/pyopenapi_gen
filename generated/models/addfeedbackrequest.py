from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class AddFeedbackRequest:
    rating: str = field(default_factory=str)  # The feedback rating
