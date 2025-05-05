from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional
from .foundation_model_provider_enum import FoundationModelProviderEnum
from .foundation_model_type import FoundationModelType


@dataclass
class FoundationModel:
    """
    Foundation model definition for AI capabilities, including configuration options and supported features.

    Attributes:
        id (Optional[str]): Unique identifier for the model
        name (Optional[str]): Human-readable name for the model
        provider (Optional[FoundationModelProviderEnum]): AI provider (e.g., OpenAI, Anthropic, Cohere)
        type (Optional[FoundationModelType]): No description provided.
        version (Optional[str]): Version identifier of the model
        context_window (Optional[int]): Maximum token context window size supported
        max_output_tokens (Optional[int]): Maximum number of tokens the model can generate in one completion
        features (Optional[List[str]]): Special capabilities supported by this model
        default_settings (Optional[Any]): Default configuration settings for the model
        active (Optional[bool]): Whether this model is currently available for use
        description (Optional[str]): Detailed description of the model capabilities and best use cases
        created_at (Optional[datetime]): Creation timestamp
        updated_at (Optional[datetime]): Last update timestamp
    """

    id: Optional[str] = None
    name: Optional[str] = None
    provider: Optional[FoundationModelProviderEnum] = None
    type: Optional[FoundationModelType] = None
    version: Optional[str] = None
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    features: Optional[List[str]] = None
    default_settings: Optional[Any] = None
    active: Optional[bool] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
