"""
Clause Segmenter (T-Unit Approximation)
---------------------------------------
Clinically grounded segmentation using spaCy dependency parsing.

FINAL VERSION (STABLE):
✔ ROOT + SUBJECT validation
✔ Conj split ONLY when new subject exists
✔ No subtree deletion bugs
✔ AD-safe (no verb chain splitting)
✔ Clean + deduplicated output
"""

from typing import Dict, List
import spacy

_nlp = spacy.load("en_core_web_sm")


def segment_clauses(text: str) -> Dict:

    if not text or not text.strip():
        return {
            "clauses": [],
            "clause_count": 0
        }

    doc = _nlp(text)

    clauses: List[str] = []
    seen_spans = set()

    for sent in doc.sents:

        for token in sent:

            # -----------------------------
            # ROOT CLAUSE
            # -----------------------------
            if token.dep_ == "ROOT":

                has_subject = any(
                    child.dep_ in ("nsubj", "nsubjpass")
                    for child in token.children
                )

                if has_subject:
                    subtree = sorted(list(token.subtree), key=lambda t: t.i)

                    span_ids = tuple(t.i for t in subtree)

                    if span_ids not in seen_spans:
                        seen_spans.add(span_ids)
                        clause = " ".join(t.text for t in subtree)
                        clauses.append(clause)

            # -----------------------------
            # CONJ CLAUSE (ONLY if new subject)
            # -----------------------------
            if token.dep_ == "conj" and token.pos_ in {"VERB", "AUX"}:

                has_own_subject = any(
                    child.dep_ in ("nsubj", "nsubjpass")
                    for child in token.children
                )

                if not has_own_subject:
                    continue  # skip verb chains

                subtree = sorted(list(token.subtree), key=lambda t: t.i)
                span_ids = tuple(t.i for t in subtree)

                if span_ids not in seen_spans:
                    seen_spans.add(span_ids)
                    clause = " ".join(t.text for t in subtree)
                    clauses.append(clause)

    # ----------------------------------
    # CLEANING
    # ----------------------------------
    cleaned_clauses = []

    for clause in clauses:

        clause = clause.strip()

        for prefix in ["and ", "then ", "so ", "but "]:
            if clause.lower().startswith(prefix):
                clause = clause[len(prefix):]

        clause = clause.replace(" .", ".")
        clause = clause.replace(" ,", ",")

        clause = clause.strip()

        if clause:
            cleaned_clauses.append(clause)

    # ----------------------------------
    # REMOVE DUPLICATES + SUBSUMED CLAUSES
    # ----------------------------------
    final_unique_clauses = []

    for clause in cleaned_clauses:
        is_subset = False

        for other in cleaned_clauses:
            if clause != other and clause in other:
                is_subset = True
                break

        if not is_subset:
            final_unique_clauses.append(clause)

    # ----------------------------------
    # FINAL VALIDATION
    # ----------------------------------
    final_clauses = []

    for clause in final_unique_clauses:
        clause_doc = _nlp(clause)

        has_verb = any(tok.pos_ in {"VERB", "AUX"} for tok in clause_doc)
        has_subject = any(tok.dep_ in {"nsubj", "nsubjpass"} for tok in clause_doc)

        if has_verb and has_subject:
            final_clauses.append(clause)

    return {
        "clauses": final_clauses,
        "clause_count": len(final_clauses)
    }