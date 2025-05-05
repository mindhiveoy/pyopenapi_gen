from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class FeedbackResponse:
    """
    Data model for FeedbackResponse

    Attributes:
        data (Dict[str, Any]): Feedback model for capturing user evaluations of AI responses for quality improvement.
    """
