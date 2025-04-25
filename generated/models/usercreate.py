from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class UserCreate:
    name: Optional[str] = None  # User's display name
    email: str = field(default_factory=str)  # User's email address
    password: str = field(default_factory=str)  # User's password
    role: Optional[str] = None  # User's role
    tenantId: str = field(default_factory=str)  # ID of the tenant this user belongs to
