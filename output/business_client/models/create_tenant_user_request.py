from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateTenantUserRequest:
    """
    Data model for CreateTenantUserRequest

    Attributes:
        name (str): User's full name
        email (str): User's email address
        password (str): User's password (min 6 characters)
        role (str): User's role
        image (Optional[str]): URL to user's profile image
    """

    name: str
    email: str
    password: str
    role: str
    image: Optional[str] = None
