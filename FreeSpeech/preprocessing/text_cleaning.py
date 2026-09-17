"""
Text Cleaning (Free Speech)
---------------------------
Minimal, clinically safe normalization.

IMPORTANT:
✔ Preserves disfluency (uh, um, repetitions)
✔ Preserves pauses (...)

DOES NOT:
✖ Remove fillers
✖ Remove repetitions
✖ Correct grammar
"""

import re


def clean_text(text: str) -> str:
    """
    Light cleaning for Free Speech pipeline.

    Args:
        text (str): Raw ASR transcript

    Returns:
        str: Cleaned text (safe for disfluency + clause parsing)
    """

    if not text or not text.strip():
        return ""

    # -----------------------------
    # Lowercase (safe)
    # -----------------------------
    text = text.lower()

    # -----------------------------
    # Remove ASR tags
    # -----------------------------
    text = re.sub(r"\[.*?\]", "", text)

    # -----------------------------
    # Normalize punctuation
    # -----------------------------
    text = re.sub(r"[!?]", ".", text)

    # Keep ellipsis (...) → important for pauses
    text = re.sub(r"\.{4,}", "...", text)

    # -----------------------------
    # Remove unwanted symbols
    # (BUT keep . , ' ...)
    # -----------------------------
    text = re.sub(r"[^a-z0-9.,'\s]", "", text)

    # -----------------------------
    # Normalize whitespace
    # -----------------------------
    text = re.sub(r"\s+", " ", text)

    return text.strip()