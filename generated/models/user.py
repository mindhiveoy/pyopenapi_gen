from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    """
    User model for authentication and authorization. Represents system users
    with their credentials and permissions. Supports multiple authentication
    methods including OAuth and WebAuthn.
    """

    id: Optional[str] = None  # Unique identifier for the user
    email: Optional[str] = (
        None  # User's email address for authentication and communication
    )
    name: Optional[str] = None  # User's display name
    role: Optional[str] = (
        None  # User's role and permission level. Standard users have basic tenant permissions, admins have elevated tenant management permissions, and system users have unrestricted access across all tenants.
    )
    tenantId: Optional[Optional[str]] = (
        None  # Reference to the associated tenant organization
    )
    createdAt: Optional[datetime] = None  # Creation timestamp
    updatedAt: Optional[datetime] = None  # Last update timestamp
