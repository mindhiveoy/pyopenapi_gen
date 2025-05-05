from dataclasses import dataclass


@dataclass
class AddFeedbackRequest:
    """
    Data model for AddFeedbackRequest

    Attributes:
        rating (str): The feedback rating
    """

    rating: str
