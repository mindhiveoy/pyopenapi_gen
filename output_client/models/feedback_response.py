from dataclasses import dataclass


@dataclass
class FeedbackResponse:
    """
    Data model for FeedbackResponse

    Attributes:
        data (Dict[str, Any]): Feedback model for capturing user evaluations of AI responses for quality improvement.
    """
