
from dataclasses import dataclass
from typing import Optional

@dataclass
class ClientConfig:
    base_url: str
    timeout: Optional[float] = 30.0
