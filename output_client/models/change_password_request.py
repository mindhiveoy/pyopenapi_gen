from dataclasses import dataclass


@dataclass
class ChangePasswordRequest:
    """
    Data model for ChangePasswordRequest

    Attributes:
        user_id (str): The ID of the user whose password is being changed
        new_password (str): The new password to set
    """

    user_id: str
    new_password: str
