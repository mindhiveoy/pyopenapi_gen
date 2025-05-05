from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class FoundationModelResponse:
    """
    Data model for FoundationModelResponse

    Attributes:
        data (Dict[str, Any]): Foundation model definition for AI capabilities, including configuration options and supported features.
    """
