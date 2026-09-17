"""
Spatial Analyzer
----------------
Extracts spatial prepositions and relations from utterances
for picture description tasks (Cookie Theft).
"""

from typing import List, Dict
import spacy

# Load once (small model is enough)
_nlp = spacy.load("en_core_web_sm")

# Clinically relevant spatial terms
SPATIAL_PREPOSITIONS = {
    "in", "on", "at", "under", "over", "behind", "beside",
    "next to", "near", "above", "below", "between", "inside",
    "outside", "around", "by"
}


def analyze_spatial_relations(utterances: List[str]) -> Dict:
    """
    Analyze spatial language usage in utterances.

    Args:
        utterances (List[str]): Cleaned utterances

    Returns:
        Dict: Spatial diagnostics
    """

    spatial_hits = []

    for utt in utterances:
        doc = _nlp(utt)

        for token in doc:
            # Prepositions
            if token.dep_ == "prep":
                text = token.text.lower()

                if text in SPATIAL_PREPOSITIONS:
                    spatial_hits.append({
                        "token": text,
                        "utterance": utt
                    })

    spatial_count = len(spatial_hits)
    utterance_count = max(len(utterances), 1)

    spatial_density = spatial_count / utterance_count

    return {
        "spatial_count": spatial_count,
        "spatial_density": round(spatial_density, 4),
        "spatial_tokens": spatial_hits
    }