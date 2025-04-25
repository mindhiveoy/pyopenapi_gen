from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class UpdateFoundationModelRequest:
    name: str = field(default_factory=str)  # Display name for the foundation model
    internalName: str = field(
        default_factory=str
    )  # Internal name for the foundation model
    type: str = field(default_factory=str)  # Type of the foundation model
    description: Optional[str] = None  # Description of the foundation model
    contextWindow: int = field(
        default_factory=str
    )  # Context window size for the foundation model
    maxOutput: Optional[int] = None  # Maximum output size for the foundation model
    config: Optional[Dict[str, Any]] = None  # Configuration for the foundation model
