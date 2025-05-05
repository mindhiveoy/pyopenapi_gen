from dataclasses import dataclass


@dataclass
class ElaborateSearchPhraseRequest:
    """
    Data model for ElaborateSearchPhraseRequest

    Attributes:
        search_phrase (str): The search phrase to be elaborated.
        instructions (str): AI instructions for the search process.
    """

    search_phrase: str
    instructions: str
