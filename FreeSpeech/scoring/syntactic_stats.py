"""
Syntactic Statistics
-------------------
Captures grammatical complexity of speech.

✔ Mean Clause Length (MLC)
✔ Subordination Ratio
✔ Dependency Tree Depth

Clinical Insight:
- Low MLC → fragmented speech
- Low subordination → reduced complexity
- Low depth → shallow grammar (AD marker)
"""

from typing import Dict
import spacy
from .thresholds import Thresholds

_nlp = spacy.load("en_core_web_sm")


def compute_syntactic_stats(text: str, clauses: Dict) -> Dict:

    # -----------------------------
    # 0. Safety Checks
    # -----------------------------
    if not text or not text.strip():
        return _empty_response()

    doc = _nlp(text)

    clause_list = clauses.get("clauses", [])
    clause_count = len(clause_list)

    if clause_count == 0:
        return _empty_response()

    # -----------------------------
    # 1. Mean Clause Length (MLC)
    # -----------------------------
    clause_lengths = [
        len([t for t in _nlp(c) if t.is_alpha])
        for c in clause_list
    ]

    total_words = len([t for t in doc if t.is_alpha])
    mlc = total_words / clause_count

    # -----------------------------
    # 2. Subordination Ratio (IMPROVED)
    # -----------------------------
    subordinate_deps = {
        "advcl",   # adverbial clause
        "ccomp",   # clausal complement
        "xcomp",   # open complement
        "acl",     # adjectival clause
        "relcl"    # relative clause
    }

    subordinate_count = sum(
        1 for token in doc if token.dep_ in subordinate_deps
    )

    subordination_ratio = subordinate_count / clause_count

    # -----------------------------
    # 3. Dependency Depth (OPTIMIZED)
    # -----------------------------
    def get_depth(token):
        depth = 0
        while token.head != token:
            token = token.head
            depth += 1
        return depth

    depths = [get_depth(token) for token in doc if token.is_alpha]

    avg_depth = sum(depths) / len(depths) if depths else 0

    # -----------------------------
    # 4. Clinical Interpretation
    # -----------------------------
    # MLC-based (primary signal)
    if mlc < Thresholds.syntax["impaired"]:
        complexity = "impaired"
    elif mlc <= Thresholds.syntax["borderline"]:
        complexity = "borderline"
    else:
        complexity = "healthy"

    # -----------------------------
    # 5. DETECT WEAK CLAUSES
    # -----------------------------
    short_clauses = [
        c for c, l in zip(clause_list, clause_lengths) if l < 5
    ]

    long_clauses = [
        c for c, l in zip(clause_list, clause_lengths) if l > 12
    ]

    # -----------------------------
    # 6. PATTERN DETECTION (CLINICAL)
    # -----------------------------
    if mlc < 6 and subordination_ratio < 0.3:
        pattern = "telegraphic_speech"
    elif avg_depth < 1.5:
        pattern = "shallow_structure"
    elif subordination_ratio < 0.2:
        pattern = "low_complexity"
    else:
        pattern = "normal_structure"

    # -----------------------------
    # 7. Output
    # -----------------------------
    return {
        "mean_clause_length": round(mlc, 4),
        "subordination_ratio": round(subordination_ratio, 4),
        "avg_dependency_depth": round(avg_depth, 4),
        "syntactic_complexity": complexity,
        "evidence": {
            "clause_lengths": clause_lengths,
            "short_clauses": short_clauses[:3],
            "long_clauses": long_clauses[:3],

            "subordinate_count": subordinate_count,

            "avg_depth": round(avg_depth, 4),
            "pattern": pattern
        }
    }


def _empty_response():
    return {
        "mean_clause_length": 0.0,
        "subordination_ratio": 0.0,
        "avg_dependency_depth": 0.0,
        "syntactic_complexity": "impaired",

        "evidence": {}
    }