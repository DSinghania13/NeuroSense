"""
Lexical Diversity (MATTR + Root TTR)
------------------------------------
Measures vocabulary richness.

Clinical Insight:
- Low diversity → repetition / lexical retrieval issues
"""
from collections import Counter
from typing import Dict
import spacy
import math
from .thresholds import Thresholds

_nlp = spacy.load("en_core_web_sm")

WINDOW_SIZE = 50


def compute_lexical_diversity(text: str) -> Dict:

    # -----------------------------
    # SAFETY CHECK (NEW)
    # -----------------------------
    if not text or not text.strip():
        return {
            "primary_score": 0.0,
            "method": "none",
            "ttr_level": "impaired",
            "raw_stats": {
                "total_words": 0,
                "unique_lemmas": 0,
                "root_ttr_value": 0.0,
                "mattr_value": None
            },

            "evidence": {}
        }

    doc = _nlp(text)

    # -----------------------------
    # ALL LEMMAS (INCLUDING STOPWORDS)
    # -----------------------------
    all_lemmas = [
        token.lemma_.lower()
        for token in doc
        if token.is_alpha
    ]

    total_words = len(all_lemmas)

    # -----------------------------
    # SECOND SAFETY CHECK (IMPORTANT)
    # Handles cases like: "..." or symbols
    # -----------------------------
    if total_words == 0:
        return {
            "primary_score": 0.0,
            "method": "none",
            "ttr_level": "impaired",
            "raw_stats": {
                "total_words": 0,
                "unique_lemmas": 0,
                "root_ttr_value": 0.0,
                "mattr_value": None
            },

            "evidence": {}
        }

    unique_words = len(set(all_lemmas))

    freq = Counter(all_lemmas)
    most_common = freq.most_common(5)

    # 🔥 NEW: detect repeated words (>2 occurrences)
    repeated_words = {w: c for w, c in freq.items() if c > 2}

    # -----------------------------
    # Root TTR (Guiraud)
    # -----------------------------
    root_ttr = unique_words / math.sqrt(total_words)

    # -----------------------------
    # MATTR
    # -----------------------------
    mattr = 0.0

    if total_words >= 100:
        current_window = 50
    elif total_words >= 25:
        current_window = 25
    else:
        # Force it to fall back to Root TTR if under 25 words
        current_window = float('inf')

    if total_words >= current_window:
        ttr_values = []

        for i in range(total_words - current_window + 1):
            window = all_lemmas[i:i + current_window]
            window_unique = len(set(window))
            ttr_values.append(window_unique / current_window)

        mattr = sum(ttr_values) / len(ttr_values)
        method = "mattr"
        primary_score = mattr

    else:
        method = "root_ttr"
        primary_score = root_ttr

    # -----------------------------
    # Clinical thresholds
    # -----------------------------
    if method == "mattr":
        if primary_score < Thresholds.mattr["impaired"]:
            ttr_level = "impaired"
        elif primary_score <= Thresholds.mattr["borderline"]:
            ttr_level = "borderline"
        else:
            ttr_level = "healthy"
    else:
        if primary_score < Thresholds.ttr["impaired"]:
            ttr_level = "impaired"
        elif primary_score <= Thresholds.ttr["borderline"]:
            ttr_level = "borderline"
        else:
            ttr_level = "healthy"

    return {
        "primary_score": round(primary_score, 4),
        "method": method,
        "ttr_level": ttr_level,
        "raw_stats": {
            "total_words": total_words,
            "unique_lemmas": unique_words,
            "root_ttr_value": round(root_ttr, 4),
            "mattr_value": round(mattr, 4) if mattr > 0 else None
        },

        "evidence": {
            "most_common_words": most_common,
            "repeated_words": repeated_words,
            "vocab_richness_ratio": round(unique_words / total_words, 4)
        }
    }