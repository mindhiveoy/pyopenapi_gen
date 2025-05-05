import json
from enum import Enum, unique

__all__ = ["FoundationModelProviderEnum"]


@unique
class FoundationModelProviderEnum(str, Enum):
    """AI provider (e.g., OpenAI, Anthropic, Cohere)"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    GOOGLE = "google"
    MISTRAL = "mistral"
    META = "meta"
    CUSTOM = "custom"

    @classmethod
    def from_json(cls, json_str: str) -> "FoundationModelProviderEnum":
        """Create an instance from a JSON string"""
        return FoundationModelProviderEnum(json.loads(json_str))
