from enum import Enum


class AgentStatusEnum(Enum):
    """Current operational status of the agent"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
