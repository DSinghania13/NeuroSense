"""
Coherence Score
---------------
Measures semantic flow between sentences/clauses.

Clinical Insight:
- Low coherence (< 0.20) → topic drift / disorganized thinking
- High coherence (> 0.75) → pathological perseveration (getting stuck)
"""

from typing import Dict, List
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from .thresholds import Thresholds

# -----------------------------
# LOAD MODELS ONCE
# -----------------------------
# spaCy is REMOVED! We already have the segmented clauses.
_model = SentenceTransformer("all-MiniLM-L6-v2")

def compute_coherence(clauses: List[str]) -> Dict:
    # -----------------------------
    # Safety Checks
    # -----------------------------
    # Check if we actually got a list with at least 2 items
    if not clauses or not isinstance(clauses, list) or len(clauses) < 2:
        return _empty_response()

    # Clean up just in case there are empty strings in the list
    valid_clauses = [c.strip() for c in clauses if c.strip()]

    if len(valid_clauses) < 2:
        return {
            "coherence_score": 0.0,
            "coherence_level": "impaired_drift",
            "num_sentences": len(valid_clauses),

            "evidence": {}
        }

    try:
        # Encode all clauses simultaneously into dense vectors
        embeddings = _model.encode(valid_clauses)

        similarities = []
        transitions = []

        # Calculate cosine similarity between adjacent clauses
        for i in range(len(embeddings) - 1):
            sim = cosine_similarity(
                [embeddings[i]],
                [embeddings[i + 1]]
            )[0][0]

            similarities.append(float(sim))

            # -----------------------------
            # CLASSIFY TRANSITION
            # -----------------------------
            if sim < Thresholds.coherence["impaired"]:
                label = "❌ drift"
            elif sim > 0.85:
                label = "⚠ perseveration"
            else:
                label = "✅ coherent"

            transitions.append({
                "from": valid_clauses[i],
                "to": valid_clauses[i + 1],
                "similarity": round(sim, 3),
                "label": label
            })

        coherence_score = float(np.mean(similarities))

    except Exception:
        return _empty_response()

    # -----------------------------
    # Clinical Thresholds (Corrected for SBERT)
    # -----------------------------
    if coherence_score < Thresholds.coherence["impaired"]:
        level = "impaired"
    elif coherence_score < Thresholds.coherence["borderline"]:
        level = "borderline"
    elif coherence_score <= Thresholds.coherence["healthy"]:
        level = "healthy"
    else:
        level = "impaired_perseveration"

    drift_points = [
        t for t in transitions if "drift" in t["label"]
    ]

    high_similarity_loops = [
        t for t in transitions if "perseveration" in t["label"]
    ]

    return {
        "coherence_score": round(coherence_score, 4),
        "coherence_level": level,
        "num_sentences": len(valid_clauses),

        "evidence": {
            "transitions": transitions,
            "drift_points": drift_points,
            "possible_loops": high_similarity_loops
        }
    }

def _empty_response():
    return {
        "coherence_score": 0.0,
        "coherence_level": "impaired_drift",
        "num_sentences": 0,

        "evidence": {}
    }