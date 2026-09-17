"""
Text Cleaning Utilities
-----------------------
Performs light, non-destructive text normalization for recall text.

IMPORTANT:
- No semantic changes (Targeted filler removal only)
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
    - Remove conversational padding/filler
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

    # 1. Lowercase
    text = text.lower()

    # 2. Remove conversational padding (Disfluencies that inflate SBERT scores)
    # Target common phrases MCI/Healthy patients use to stall or preface answers.
    fillers = [
        r"\bwell\b",
        r"\blet me think\b",
        r"\blet'?s see\b",
        r"\bi remember( that)?\b",
        r"\bi believe( that)?\b",
        r"\bi think( that)?\b",
        r"\boh\b",
        r"\bum\b",
        r"\buh\b",
        r"\byes\b"
    ]
    filler_pattern = re.compile(r'|'.join(fillers))
    text = filler_pattern.sub("", text)

    # 3. Clean up orphaned punctuation (e.g., if "Well, " becomes ", ")
    text = re.sub(r"^[,\.\s]+", "", text)  # Strip leading commas/periods
    text = re.sub(r"\s+,\s+", " ", text)   # Clean middle hanging commas
    text = re.sub(r"\s+\.\s+", ". ", text) # Fix spaced periods

    # 4. Replace newlines and tabs with space
    text = re.sub(r"[\n\t]", " ", text)

    # 5. Remove repeated punctuation (e.g., "!!", "??", "..")
    text = re.sub(r"[!?\.]{2,}", ".", text)

    # 6. Normalize multiple spaces
    text = re.sub(r"\s{2,}", " ", text)

    # 7. Strip leading/trailing spaces
    text = text.strip()

    return text