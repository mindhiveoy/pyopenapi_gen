from dataclasses import dataclass
from .success_success_enum import SuccessSuccessEnum


@dataclass
class Success:
    """
    Data model for Success

    Attributes:
        success (SuccessSuccessEnum): No description provided.
    """

    success: SuccessSuccessEnum
