from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class ElaborateSearchPhraseRequest:
    searchPhrase: str = field(
        default_factory=str
    )  # The search phrase to be elaborated.
    instructions: str = field(
        default_factory=str
    )  # AI instructions for the search process.
