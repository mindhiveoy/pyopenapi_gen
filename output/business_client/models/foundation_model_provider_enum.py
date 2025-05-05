from enum import Enum


class FoundationModelProviderEnum(Enum):
    """AI provider (e.g., OpenAI, Anthropic, Cohere)"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    GOOGLE = "google"
    MISTRAL = "mistral"
    META = "meta"
    CUSTOM = "custom"
