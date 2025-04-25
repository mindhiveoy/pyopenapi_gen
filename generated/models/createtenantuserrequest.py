from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class CreateTenantUserRequest:
    name: str = field(default_factory=str)  # User's full name
    email: str = field(default_factory=str)  # User's email address
    password: str = field(default_factory=str)  # User's password (min 6 characters)
    role: str = field(default_factory=str)  # User's role
    image: Optional[str] = None  # URL to user's profile image
