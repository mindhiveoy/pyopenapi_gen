from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class UpdateTenantUserRequest:
    name: Optional[str] = None  # User's full name
    email: Optional[str] = None  # User's email address
    password: Optional[str] = None  # New password (min 6 characters)
