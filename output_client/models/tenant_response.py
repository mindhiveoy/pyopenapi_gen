from dataclasses import dataclass


@dataclass
class TenantResponse:
    """
    Data model for TenantResponse

    Attributes:
        data (Dict[str, Any]): Tenant model for multi-tenant architecture. Represents an organization with its own users, agents, and resources. Core entity for tenant isolation and resource management.
    """
