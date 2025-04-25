from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class ChangePasswordRequest:
    userId: str = field(
        default_factory=str
    )  # The ID of the user whose password is being changed
    newPassword: str = field(default_factory=str)  # The new password to set
