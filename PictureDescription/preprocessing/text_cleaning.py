"""
Text Cleaning
-------------
Minimal, safe text normalization for picture description tasks.

IMPORTANT:
- This does NOT correct grammar
- This does NOT remove repetitions
- This DOES preserve diagnostic speech patterns
"""

import re


def clean_text(text: str) -> str:
    """
    Clean ASR text for downstream utterance segmentation.

    Args:
        text (str): Raw ASR output

    Returns:
        str: Lightly cleaned text
    """
    if not text or not text.strip():
        return ""

    # Lowercase for consistency
    text = text.lower()

    # Normalize common ASR artifacts
    text = re.sub(r"\[.*?\]", "", text)  # remove [noise], [laughter], etc.

    # Normalize punctuation
    text = re.sub(r"[!?]", ".", text)
    text = re.sub(r"\.{2,}", ".", text)

    # Remove non-speech symbols
    text = re.sub(r"[^a-z0-9.,:'\-\s]", "", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()