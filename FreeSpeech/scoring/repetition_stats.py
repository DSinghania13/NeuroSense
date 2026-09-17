"""
Repetition Statistics (Improved)
-------------------------------
Captures:
✔ Consecutive repetition
✔ Global word repetition
✔ Phrase repetition

Clinical Insight:
- Detects looping, redundancy, and lexical repetition
"""
from collections import Counter
from typing import Dict
import re
from .thresholds import Thresholds


def compute_repetition(text: str) -> Dict:

    words = text.split()
    total_words = len(words)

    if total_words < 2:
        return _empty()

    repeated_phrases = []
    repeated_words = []

    palilalia_indices = set()
    echolalia_indices = set()

    # -----------------------------
    # 1. PALILALIA (consecutive)
    # -----------------------------
    for i in range(total_words - 1):
        if words[i] == words[i + 1]:
            palilalia_indices.update([i, i + 1])
            repeated_words.append(words[i])

    # -----------------------------
    # 2. ECHOLALIA (phrase repetition)
    # -----------------------------
    max_n = min(4, total_words // 2)
    MAX_GAP = 4

    for n in range(2, max_n + 1):
        for i in range(total_words - n + 1):
            phrase1 = words[i:i + n]

            for j in range(i + 1, min(i + n + MAX_GAP + 1, total_words - n + 1)):
                phrase2 = words[j:j + n]

                if phrase1 == phrase2:
                    echolalia_indices.update(range(i, i + n))
                    echolalia_indices.update(range(j, j + n))
                    repeated_phrases.append(" ".join(phrase1))

    # -----------------------------
    # 3. GLOBAL WORD REPETITION
    # -----------------------------
    word_counts = Counter(words)

    high_freq_words = {
        w: c for w, c in word_counts.items() if c > 2
    }

    # -----------------------------
    # 4. GLOBAL PHRASE REPETITION
    # -----------------------------
    ngrams = [" ".join(words[i:i + 3]) for i in range(len(words) - 2)]
    counts = Counter(ngrams)

    repeated_ngram_counts = {
        k: v for k, v in counts.items() if v > 1
    }

    global_phrase_repetition = sum(v - 1 for v in counts.values() if v > 1)

    # -----------------------------
    # 5. SCORE
    # -----------------------------
    total_flagged_words = len(palilalia_indices.union(echolalia_indices))

    repetition_score = (
        total_flagged_words + (global_phrase_repetition * 3)
    ) / total_words

    repetition_score = min(1.0, repetition_score)

    # -----------------------------
    # 6. CLINICAL LEVEL
    # -----------------------------
    if repetition_score >= Thresholds.repetition["severe"]:
        level = "severe"
    elif repetition_score >= Thresholds.repetition["mild"]:
        level = "mild"
    else:
        level = "healthy"

    # -----------------------------
    # 7. LOOP DETECTION
    # -----------------------------
    dominant_phrase = None
    if repeated_ngram_counts:
        dominant_phrase = max(repeated_ngram_counts, key=repeated_ngram_counts.get)

    loop_detected = False
    if dominant_phrase and repeated_ngram_counts[dominant_phrase] >= 3:
        loop_detected = True

    # -----------------------------
    # 8. PATTERN CLASSIFICATION
    # -----------------------------
    if loop_detected:
        pattern = "perseveration_loop"
    elif len(high_freq_words) > 3:
        pattern = "lexical_repetition"
    elif repeated_phrases:
        pattern = "phrase_repetition"
    else:
        pattern = "normal"

    # -----------------------------
    # OUTPUT
    # -----------------------------
    return {
        "repetition_ratio": round(repetition_score, 4),
        "repetition_count": total_flagged_words,
        "phrase_repetition": global_phrase_repetition,
        "repetition_level": level,

        "evidence": {
            "repeated_words": list(set(repeated_words))[:5],
            "word_frequencies": dict(list(high_freq_words.items())[:5]),
            "repeated_phrases": list(set(repeated_phrases))[:5],
            "phrase_frequencies": dict(list(repeated_ngram_counts.items())[:5]),

            "dominant_phrase": dominant_phrase,
            "loop_detected": loop_detected,
            "pattern": pattern
        }
    }


def _empty():
    return {
        "repetition_ratio": 0.0,
        "repetition_count": 0,
        "phrase_repetition": 0,
        "repetition_level": "healthy",
        "evidence": {}
    }