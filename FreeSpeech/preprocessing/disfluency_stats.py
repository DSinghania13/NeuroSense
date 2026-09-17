"""
Disfluency Extraction (Free Speech)
-----------------------------------
Detects clinically relevant speech disruptions.

Captures:
✔ Fillers (uh, um, ah, etc.)
✔ Word repetitions (the the, I I)
✔ Broken speech / pauses (...)

DOES NOT modify text — only analyzes.
"""

from typing import Dict, List
import re


# -----------------------------
# FILLER WORD LIST (extendable)
# -----------------------------
FILLERS = {
    "uh", "um", "ah", "er", "hmm",
    "uhh", "umm"
}


def extract_disfluency(text: str) -> Dict:
    """
    Extract disfluency metrics from cleaned text.

    Args:
        text (str): Cleaned transcript

    Returns:
        Dict with disfluency stats
    """

    if not text or not text.strip():
        return _empty_stats()

    # -----------------------------
    # Tokenization (simple + safe)
    # -----------------------------
    words = [re.sub(r"[^\w']", "", w) for w in text.split()]
    words = [w for w in words if w]  # remove empty tokens
    total_words = len(words)

    if total_words == 0:
        return _empty_stats()

    # -----------------------------
    # 1. FILLER COUNT
    # -----------------------------
    filler_count = sum(1 for w in words if w in FILLERS)
    fillers_used = [w for w in words if w in FILLERS]

    # -----------------------------
    # 2. REPETITION COUNT
    # (Consecutive repetition only)
    # -----------------------------
    repetition_count = 0

    for i in range(1, len(words)):
        if words[i] == words[i - 1]:
            repetition_count += 1

    # -----------------------------
    # 3. BROKEN SPEECH / PAUSES
    # Count "..." occurrences
    # -----------------------------
    pause_count = len(re.findall(r"\.\.\.", text))

    # -----------------------------
    # 4. CLEAN WORD COUNT
    # (remove fillers only for later metrics)
    # -----------------------------
    clean_words = [w for w in words if w not in FILLERS]
    clean_word_count = len(clean_words)

    # -----------------------------
    # 5. DISFLUENCY SCORE
    # -----------------------------
    # Weighted (clinically balanced)
    raw_disfluency = (
        filler_count +
        repetition_count +
        pause_count
    ) / total_words

    # Clamp to avoid extreme penalties
    disfluency_score = min(raw_disfluency, 1.0)

    return {
        "filler_count": filler_count,
        "repetition_count": repetition_count,
        "pause_count": pause_count,
        "total_words": total_words,
        "clean_word_count": clean_word_count,
        "disfluency_score": round(disfluency_score, 4),

        "evidence": {
            "fillers_used": list(set(fillers_used)),
            "filler_count": filler_count
        }
    }


# -----------------------------
# EMPTY CASE
# -----------------------------
def _empty_stats() -> Dict:
    return {
        "filler_count": 0,
        "repetition_count": 0,
        "pause_count": 0,
        "total_words": 0,
        "clean_word_count": 0,
        "disfluency_score": 0.0,

        "evidence": {}
    }