from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class UserUpdate:
    name: Optional[str] = None  # User's display name
    email: Optional[str] = None  # User's email address
    password: Optional[str] = None  # User's password
    role: Optional[str] = None  # User's role
