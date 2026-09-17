"""
Utterance Segmentation + Disfluency Recovery
--------------------------------------------
Preserves diagnostic speech artifacts:
- Fillers (um, uh, etc.)
- Repetitions
- Raw vs cleaned utterances

Used by Picture Description & Story Recall pipelines.
"""

import re
from typing import Dict, List
from .syntactic_analyzer import analyze_syntax


FILLER_WORDS = {
    "um", "uh", "erm", "ah", "eh",
    "like", "you know"
}


def segment_utterances(text: str) -> Dict:
    """
    Segment raw speech into utterances and compute disfluency stats.

    Args:
        text (str): Raw ASR or typed input (UNCLEANED)

    Returns:
        Dict with:
        - raw_utterances
        - cleaned_utterances
        - disfluency_stats
    """

    if not text or not text.strip():
        return {
            "raw_utterances": [],
            "cleaned_utterances": [],
            "disfluency_stats": {
                "filler_count": 0,
                "repetition_count": 0,
                "total_words": 0,
                "disfluency_score": 0.0
            }
        }

    # -----------------------------
    # 1. Split utterances (soft)
    # -----------------------------
    raw_utterances = re.split(r"[.?!]", text)
    raw_utterances = [u.strip() for u in raw_utterances if u.strip()]

    filler_count = 0
    repetition_count = 0
    total_words = 0

    cleaned_utterances: List[str] = []

    # -----------------------------
    # 2. Analyze each utterance
    # -----------------------------
    for utt in raw_utterances:
        words = utt.lower().split()
        total_words += len(words)

        # ---- Count fillers ----
        for i, w in enumerate(words):
            if w in FILLER_WORDS:
                filler_count += 1

        # ---- Count repetitions ----
        for i in range(1, len(words)):
            if words[i] == words[i - 1]:
                repetition_count += 1

        # ---- Clean utterance (REMOVE fillers only) ----
        cleaned_words = [
            w for w in words
            if w not in FILLER_WORDS
        ]
        cleaned_utterances.append(" ".join(cleaned_words))

    # -----------------------------
    # 3. Disfluency metrics
    # -----------------------------
    disfluency_score = (
        filler_count / total_words
        if total_words > 0 else 0.0
    )

    syntax_stats = analyze_syntax(cleaned_utterances)

    return {
        "raw_utterances": raw_utterances,
        "cleaned_utterances": cleaned_utterances,
        "syntax_stats": syntax_stats,
        "disfluency_stats": {
            "filler_count": filler_count,
            "repetition_count": repetition_count,
            "total_words": total_words,
            "disfluency_score": round(disfluency_score, 4)
        }
    }