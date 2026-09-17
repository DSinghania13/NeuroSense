"""
Text Cleaning Utilities
-----------------------
Performs light, non-destructive text normalization for recall text.

IMPORTANT:
- No semantic changes
- No stopword removal
- No lemmatization
- No paraphrasing
"""

import re


def clean_text(text: str) -> str:
    """
    Clean recall text while preserving meaning.

    Operations:
    - Lowercasing
    - Normalize whitespace
    - Remove extra punctuation noise
    - Preserve sentence structure

    Args:
        text (str): Raw recall text

    Returns:
        str: Cleaned text
    """
    if not isinstance(text, str):
        raise ValueError("Input to clean_text must be a string")

    # Lowercase
    text = text.lower()

    # Replace newlines and tabs with space
    text = re.sub(r"[\n\t]", " ", text)

    # Remove repeated punctuation (e.g., "!!", "??")
    text = re.sub(r"[!?]{2,}", ".", text)

    # Normalize multiple spaces
    text = re.sub(r"\s{2,}", " ", text)

    # Strip leading/trailing spaces
    text = text.strip()

    return text