from dataclasses import dataclass
from typing import Optional


@dataclass
class UpdateTenantUserRequest:
    """
    Data model for UpdateTenantUserRequest

    Attributes:
        name (Optional[str]): User's full name
        email (Optional[str]): User's email address
        password (Optional[str]): New password (min 6 characters)
    """

    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
