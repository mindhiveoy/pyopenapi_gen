"""
Utility for extracting variable names from URL templates.
"""

import re
from typing import Set


def extract_url_variables(url: str) -> Set[str]:
    """
    Extract all variable names (e.g., 'foo' from '{foo}') from a URL template.
    Returns a set of variable names as strings.
    """
    return set(re.findall(r"{([^}]+)}", url))
