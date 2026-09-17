"""
Sentence Splitter
-----------------
Splits cleaned recall text into sentences for IU scoring.

IMPORTANT:
- Uses conservative sentence boundaries
- Preserves meaning
- Avoids aggressive NLP transformations
"""

import re
from typing import List


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using punctuation boundaries.

    Args:
        text (str): Cleaned recall text

    Returns:
        List[str]: List of sentence strings
    """
    if not isinstance(text, str):
        raise ValueError("Input to split_into_sentences must be a string")

    # Split on sentence-ending punctuation followed by space
    sentences = re.split(r"(?<=[.!?])\s+", text)

    # Remove empty or very short fragments
    sentences = [
        s.strip()
        for s in sentences
        if s and len(s.strip()) > 2
    ]

    return sentences