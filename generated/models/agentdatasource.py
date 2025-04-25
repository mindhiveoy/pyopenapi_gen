from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class AgentDataSource:
    id: str = field(
        default_factory=str
    )  # Unique identifier for the agent-datasource mapping
    agentId: str = field(default_factory=str)  # Reference to the associated agent
    dataSourceId: str = field(
        default_factory=str
    )  # Reference to the associated data source
    description: Optional[str] = (
        None  # Purpose and context of this data source for the agent
    )
    instructions: Optional[str] = None  # Usage instructions for the agent
    config: Optional[Dict[str, Any]] = None  # Source-specific configuration options
