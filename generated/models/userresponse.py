from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UserResponse:
    """
    User response with optional included relations
    """

    data: Optional[User] = (
        None  # User model for authentication and authorization. Represents system users with their credentials and permissions. Supports multiple authentication methods including OAuth and WebAuthn.
    )
