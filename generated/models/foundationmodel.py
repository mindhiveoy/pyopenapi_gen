from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FoundationModel:
    """
    Foundation model definition for AI capabilities, including configuration
    options and supported features.
    """

    id: Optional[str] = None  # Unique identifier for the model
    name: Optional[str] = None  # Human-readable name for the model
    provider: Optional[str] = None  # AI provider (e.g., OpenAI, Anthropic, Cohere)
    type: Optional[FoundationModelType] = (
        None  # Foundation model types for different AI tasks
    )
    version: Optional[Optional[str]] = None  # Version identifier of the model
    contextWindow: Optional[Optional[int]] = (
        None  # Maximum token context window size supported
    )
    maxOutputTokens: Optional[Optional[int]] = (
        None  # Maximum number of tokens the model can generate in one completion
    )
    features: Optional[List[str]] = None  # Special capabilities supported by this model
    defaultSettings: Optional[Dict[str, Any]] = (
        None  # Default configuration settings for the model
    )
    active: Optional[bool] = None  # Whether this model is currently available for use
    description: Optional[str] = (
        None  # Detailed description of the model capabilities and best use cases
    )
    createdAt: Optional[datetime] = None  # Creation timestamp
    updatedAt: Optional[datetime] = None  # Last update timestamp
