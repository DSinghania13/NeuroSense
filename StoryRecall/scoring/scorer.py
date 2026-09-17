"""
IU Scorer for Story Recall (UPDATED)
------------------------------------
Hybrid SBERT + Cross-Encoder (STS) IU scoring.

Updates:
- Added "Exact String Match" shortcut to fix vector dilution on short IUs.
- Updated threshold variables to use new 'entailment_strong/weak'.
"""

from typing import Dict, List, Optional
import numpy as np
# Removed scipy.special since we no longer use softmax for STS
# import scipy.special

from .sbert_encoder import SBERTEncoder
from .thresholds import IUThresholds
from .entailment import EntailmentEngine
from .gmatch import compute_gmatch


class IUScorer:

    CORE_IUS = {
        "IU1", "IU2", "IU3", "IU4",
        "IU5", "IU6", "IU7", "IU8"
    }

    CONTEXT_IUS = {
        "IU9", "IU10", "IU11",
        "IU12", "IU13", "IU14", "IU15"
    }

    # -----------------------------
    # Weights
    # -----------------------------
    CORE_WEIGHT = 0.7
    CONTEXT_WEIGHT = 0.3

    IU_WEIGHT = 0.6
    GMATCH_WEIGHT = 0.25
    PAUSE_WEIGHT = 0.15

    MAX_PAUSE_PENALTY = 0.3

    def __init__(self, encoder: SBERTEncoder, thresholds: IUThresholds):
        self.encoder = encoder
        self.thresholds = thresholds

    # --------------------------------------------------
    def score_story_with_gmatch(
        self,
        recall_sentences: List[str],
        iu_templates: Dict[str, str],
        pause_stats: Optional[Dict] = None,
        **_
    ) -> Dict:
        return self.score_story_recall(
            recall_sentences,
            iu_templates,
            pause_stats
        )

    # --------------------------------------------------
    def score_story_recall(
        self,
        recall_sentences: List[str],
        iu_templates: Dict[str, str],
        pause_stats: Optional[Dict]
    ) -> Dict:

        if not recall_sentences:
            return self._score_empty(iu_templates)

        recall_embs = self.encoder.encode(recall_sentences)
        iu_table: Dict[str, Dict] = {}

        # ================= IU MATCHING =================
        for iu_id, iu_text in iu_templates.items():

            # --- SHORTCUT: Exact String Match ---
            # Fixes "Vector Dilution" where short IUs (like "Monday morning")
            # get drowned out in long sentences.
            exact_found = False
            matched_sent_idx = -1
            matched_sent_text = ""

            for idx, sent in enumerate(recall_sentences):
                # Simple case-insensitive substring check
                if iu_text.lower().strip() in sent.lower():
                    exact_found = True
                    matched_sent_idx = idx
                    matched_sent_text = sent
                    break

            if exact_found:
                # Bypass SBERT/STS and award full points immediately
                iu_table[iu_id] = {
                    "iu_id": iu_id,
                    "iu_type": self._iu_type(iu_id),
                    "expected_text": iu_text,
                    "all_recall_sentences": [],
                    "recall_candidates": [],
                    "selected_candidate_index": -1,
                    "matched_recall_text": matched_sent_text,
                    "recall_sentence_index": matched_sent_idx,
                    "score": 1.0,
                    "match_type": "exact",
                    "decision_reason": "Verbatim substring match (Shortcut)"
                }
                continue

            # --- END SHORTCUT ---

            # Standard SBERT + STS Logic for non-exact matches
            iu_emb = self.encoder.encode(iu_text).reshape(-1)

            sims = np.dot(recall_embs, iu_emb)
            ranked = sorted(
                enumerate(zip(recall_sentences, sims)),
                key=lambda x: x[1][1],
                reverse=True
            )

            # Use the new SBERT Gate
            gated = [
                (idx, sent, float(sim))
                for idx, (sent, sim) in ranked
                if sim >= self.thresholds.sbert_gate
            ][:2]

            if not gated:
                iu_table[iu_id] = self._miss(iu_id, iu_text, recall_sentences)
                continue

            # ---- Cross-Encoder (STS) ----
            pairs = [(sent, iu_text) for _, sent, _ in gated]
            scores = EntailmentEngine.score(pairs)

            if isinstance(scores, float):
                entailment_scores = [scores]
            else:
                entailment_scores = scores

            # ---- Build candidate trace ----
            candidate_trace = []
            for (idx, sent, sim), ent in zip(gated, entailment_scores):
                candidate_trace.append({
                    "sentence_index": idx,
                    "sentence": sent,
                    "sbert_similarity": round(float(sim), 4),
                    "entailment_score": round(float(ent), 4),
                    "used_for_decision": False
                })

            best_idx = int(np.argmax(entailment_scores))
            candidate_trace[best_idx]["used_for_decision"] = True
            best = candidate_trace[best_idx]

            # ---- Decision (Using Calibrated Thresholds) ----
            # Use .entailment_strong instead of .full
            if best["entailment_score"] >= self.thresholds.entailment_strong:
                score, match, reason = 1.0, "exact", "Strong entailment"
            # Use .entailment_weak instead of .partial
            elif best["entailment_score"] >= self.thresholds.entailment_weak:
                score, match, reason = 0.5, "paraphrase", "Weak entailment"
            else:
                score, match, reason = 0.0, "missed", "Below entailment threshold"

            iu_table[iu_id] = {
                "iu_id": iu_id,
                "iu_type": self._iu_type(iu_id),

                "expected_text": iu_text,

                "all_recall_sentences": [
                    {"index": i, "sentence": s}
                    for i, s in enumerate(recall_sentences)
                ],

                "recall_candidates": candidate_trace,
                "selected_candidate_index": best_idx if score > 0 else None,

                "matched_recall_text": best["sentence"] if score > 0 else None,
                "recall_sentence_index": best["sentence_index"] if score > 0 else None,

                "score": score,
                "match_type": match,
                "decision_reason": reason
            }

        # ================= STRUCTURE =================
        canonical_order = list(iu_templates.keys())
        recalled_order = [iu for iu, r in iu_table.items() if r["score"] > 0]

        gmatch = compute_gmatch(
            canonical_order=canonical_order,
            recalled_order=recalled_order
        )
        gmatch_score = 1.0 - gmatch["penalty"]

        # ================= PRIMACY =================
        primacy_cutoff = max(1, len(canonical_order) // 4)
        primacy_expected = canonical_order[:primacy_cutoff]
        primacy_recalled = [iu for iu in primacy_expected if iu in recalled_order]
        primacy_ratio = len(primacy_recalled) / primacy_cutoff

        # ================= PAUSE =================
        pause_penalty = 0.0
        if pause_stats:
            pause_penalty = min(
                self.MAX_PAUSE_PENALTY,
                pause_stats.get("pause_count", 0) * 0.05
            )
        pause_score = max(0.0, 1.0 - pause_penalty)

        # ================= NORMALIZATION =================
        core_scores = [r["score"] for iu, r in iu_table.items() if iu in self.CORE_IUS]
        context_scores = [r["score"] for iu, r in iu_table.items() if iu in self.CONTEXT_IUS]

        core_recall = sum(core_scores) / len(self.CORE_IUS)
        context_recall = sum(context_scores) / len(self.CONTEXT_IUS)

        iu_normalized = (
            self.CORE_WEIGHT * core_recall +
            self.CONTEXT_WEIGHT * context_recall
        )

        final_score = (
            self.IU_WEIGHT * iu_normalized +
            self.GMATCH_WEIGHT * gmatch_score +
            self.PAUSE_WEIGHT * pause_score
        )

        # ================= OUTPUT =================
        return {
            "summary": {
                "iu_recall": round((sum(core_scores)+sum(context_scores))/len(iu_table), 4),
                "core_recall": round(core_recall, 4),
                "context_recall": round(context_recall, 4),
                "iu_normalized": round(iu_normalized, 4),
                "gmatch_penalty": gmatch["penalty"],
                "pause_penalty": round(pause_penalty, 4),
                "final_score": round(final_score, 4),
                "primacy_ratio": round(primacy_ratio, 3)
            },
            "details": {
                "iu_table": iu_table,
                "gmatch_details": gmatch,
                "pause_details": pause_stats or {},
                "primacy_details": {
                    "expected_start_ius": primacy_expected,
                    "recalled_start_ius": primacy_recalled
                }
            }
        }

    # --------------------------------------------------
    def _iu_type(self, iu: str) -> str:
        return "core" if iu in self.CORE_IUS else "context"

    def _miss(self, iu: str, txt: str, recall_sentences: List[str]) -> Dict:
        return {
            "iu_id": iu,
            "iu_type": self._iu_type(iu),
            "expected_text": txt,
            "all_recall_sentences": [
                {"index": i, "sentence": s}
                for i, s in enumerate(recall_sentences)
            ],
            "recall_candidates": [],
            "selected_candidate_index": None,
            "matched_recall_text": None,
            "recall_sentence_index": None,
            "score": 0.0,
            "match_type": "missed",
            "decision_reason": "No candidate above similarity threshold"
        }

    def _score_empty(self, templates: Dict[str, str]) -> Dict:
        return {
            "summary": {"final_score": 0.0},
            "details": {}
        }