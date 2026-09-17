"""
Idea Density
------------
Measures semantic richness of spontaneous speech.

Clinical Insight:
- Low idea density → strong dementia marker ("empty speech")
"""

from typing import Dict

import lemma
import spacy
from .thresholds import Thresholds

# Load once
_nlp = spacy.load("en_core_web_sm")

# Strictly Core Meaning Carriers
CONTENT_POS = {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}

VAGUE_WORDS = {
    "thing", "things", "something", "stuff",
    "place", "something", "anything", "everything"
}

def compute_idea_density(
    text: str,
    disfluency_stats: Dict
) -> Dict:
    """
    Compute idea density from cleaned text.
    """
    if not text or not text.strip():
        return {
            "idea_density": 0.0,
            "base_density": 0.0,
            "content_words": 0,
            "clean_words": 0,
            "density_level": "impaired",
            "flag_low_density": True,

            "evidence": {}
        }

    doc = _nlp(text)

    # -----------------------------
    # Clean word count
    # -----------------------------
    clean_words = disfluency_stats.get("clean_word_count", 0)

    if clean_words == 0:
        return {
            "idea_density": 0.0,
            "content_words": 0,
            "vague_words_count": 0,
            "clean_words": 0,
            "density_level": "impaired",
            "flag_low_density": True,

            "evidence": {}
        }

    # -----------------------------
    # Count content words
    # -----------------------------
    content_words = 0
    vague_count = 0
    anomia_flags = 0

    vague_words_used = []
    content_word_list = []
    anomia_list = []
    seen_content_lemmas = set()

    for i in range(len(doc)):
        token = doc[i]
        # Ignore punctuation/spaces that might have sneaked in
        if not token.is_alpha:
            continue

        #Catch Anomia(Filler + Noun pattern)
        if token.text.lower() in {"uh", "um", "ah", "er", "hmm", "uhh", "umm"}:
            # Scan forward to find the next actual word (skipping commas/spaces)
            next_idx = i + 1
            while next_idx < len(doc) and not doc[next_idx].is_alpha:
                next_idx += 1

            # Now check if that next valid word is a Noun
            if next_idx < len(doc) and doc[next_idx].pos_ in {"NOUN", "PROPN", "ADJ"}:
                anomia_flags += 1
                anomia_list.append(f"{token.text} {doc[next_idx].text}")

        # CRITICAL FIX: Do NOT use token.is_stop here!
        # We want to count common verbs (go, make, get) and adverbs (very, always).
        if token.pos_ in CONTENT_POS:
            lemma_lower = token.lemma_.lower()
            if lemma_lower not in seen_content_lemmas:
                seen_content_lemmas.add(lemma_lower)
                content_words += 1
                content_word_list.append(token.lemma_)

        # NEW: Catch vague words
        if token.lemma_.lower() in VAGUE_WORDS:
            vague_count += 1
            vague_words_used.append(token.lemma_)

    # -----------------------------
    # Compute density
    # -----------------------------
    idea_density = content_words / clean_words

    # 1. Base Density
    base_density = content_words / clean_words

    # 2. MCI Semantic Penalty
    penalty = vague_count * 0.05
    adjusted_density = max(0.1, base_density - penalty)

    # 3. Clinical classification (Using Adjusted)
    if adjusted_density > Thresholds.idea_density["borderline"]:
        density_level = "healthy"
    elif adjusted_density >= Thresholds.idea_density["impaired"]:
        density_level = "borderline"
    else:
        density_level = "impaired"

    return {
        "idea_density": round(adjusted_density, 4),
        "base_density": round(base_density, 4),
        "vague_words_count": vague_count,
        "anomia_flags": anomia_flags,
        "content_words": content_words,
        "clean_words": clean_words,
        "density_level": density_level,
        "flag_low_density": adjusted_density < Thresholds.idea_density["impaired"],

        "evidence": {
            "vague_words": list(set(vague_words_used)),
            "sample_content_words": content_word_list[:10],
            "anomia_instances": list(set(anomia_list))
        }
    }
