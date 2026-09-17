"""
IU Scorer for Picture Description (UPDATED)
-------------------------------------------
Hybrid SBERT + Cross-Encoder scoring for Cookie Theft style tasks.

Updates:
- FIXED: Now gives credit for Inferred IUs (e.g., "Mother is indifferent").
- FIXED: Compatibility with both NLI (logits) and STS (raw score) models.
- NEW:   Integrated Audio Pause Penalty (Silence > 3.0s).
"""

from typing import Dict, List
import numpy as np
import scipy.special

from .sbert_encoder import SBERTEncoder
from .thresholds import IUThresholds
from .entailment import EntailmentEngine


class Scorer:
    """
    Clinically grounded IU scorer (Picture Description).
    """

    # -----------------------------
    # IU Definitions
    # -----------------------------
    CORE_IUS = {
        "IU1","IU2","IU3","IU4","IU5",
        "IU6","IU7","IU8","IU9","IU10"
    }

    CONTEXT_IUS = {
        "IU11","IU12","IU13","IU14",
        "IU15","IU16","IU17","IU18"
    }

    # We keep these definitions for analytics, but we won't exclude them from scoring anymore.
    INFERRED_CORE_IUS = {"IU1", "IU9", "IU10"}

    # -----------------------------
    # Weights (Normalized)
    # -----------------------------
    IU_WEIGHT = 0.75
    FLUENCY_WEIGHT = 0.15
    SPATIAL_WEIGHT = 0.10

    MAX_DISFLUENCY_PENALTY = 0.5

    def __init__(self, encoder: SBERTEncoder, thresholds: IUThresholds):
        self.encoder = encoder
        self.thresholds = thresholds

    # --------------------------------------------------
    # Main Scoring API
    # --------------------------------------------------
    def score_picture_description(
        self,
        utterances: Dict,
        iu_templates: Dict[str, str],
        spatial_stats: Dict = None,
        pause_stats: Dict = None  # <--- NEW: Accept Audio Pause Data
    ) -> Dict:

        raw_utts = utterances.get("cleaned_utterances", [])
        disfluency_stats = utterances.get("disfluency_stats", {})
        spatial_stats = spatial_stats or {}
        pause_stats = pause_stats or {}

        if not raw_utts:
            return self._score_empty(
                iu_templates,
                disfluency_stats,
                spatial_stats,
                pause_stats
            )

        utter_embs = self.encoder.encode(raw_utts)
        iu_table = {}

        # ================= IU SCORING =================
        for iu_id, iu_text in iu_templates.items():
            iu_emb = self.encoder.encode(iu_text)

            sims = np.dot(utter_embs, iu_emb)
            ranked = sorted(
                enumerate(zip(raw_utts, sims)),
                key=lambda x: x[1][1],
                reverse=True
            )

            # Filter candidates using SBERT Gate
            candidates = [
                (idx, utt, float(sim))
                for idx, (utt, sim) in ranked
                if sim >= self.thresholds.sbert_gate
            ][:2]

            if not candidates:
                iu_table[iu_id] = self._miss(iu_id, iu_text, raw_utts)
                continue

            # ---- Cross-Encoder Scoring ----
            pairs = [(utt, iu_text) for _, utt, _ in candidates]
            raw_scores = EntailmentEngine.score(pairs)

            # Handle Model Differences (NLI vs STS)
            if hasattr(raw_scores, "shape") and len(raw_scores.shape) > 1 and raw_scores.shape[1] >= 2:
                # NLI Model: Apply Softmax and take 'Entailment' class (index 1)
                probs = scipy.special.softmax(raw_scores, axis=1)
                entailment_scores = probs[:, 1]
            else:
                # STS Model: Use raw scores directly (already 0.0 - 1.0)
                entailment_scores = raw_scores
                if isinstance(entailment_scores, float):
                    entailment_scores = [entailment_scores]

            best_idx = int(np.argmax(entailment_scores))
            utt_index, best_utt, best_sbert = candidates[best_idx]
            best_nli = float(entailment_scores[best_idx])

            # ---------- Decision ----------
            if best_nli >= self.thresholds.entailment_strong:
                score, match_type, reason = 1.0, "exact", "Strong entailment"
            elif best_nli >= self.thresholds.entailment_weak:
                score, match_type, reason = 0.5, "paraphrase", "Weak entailment"
            elif best_sbert >= self.thresholds.sbert_strong:
                score, match_type, reason = 0.5, "semantic_paraphrase", "Strong semantic similarity"
            elif best_sbert >= self.thresholds.sbert_weak:
                score, match_type, reason = 0.5, "weak_semantic", "Weak semantic similarity"
            else:
                score, match_type, reason = 0.0, "missed", "Below thresholds"

            iu_table[iu_id] = {
                "iu_id": iu_id,
                "iu_type": self._iu_type(iu_id),
                "expected_text": iu_text,
                "matched_utterance": best_utt if score > 0 else None,
                "utterance_index": utt_index if score > 0 else None,
                "sbert_similarity": round(best_sbert, 4),
                "entailment_score": round(best_nli, 4),
                "score": score,
                "match_type": match_type,
                "decision_reason": reason,
                "candidates": [
                    {
                        "utterance": utt,
                        "index": idx,
                        "sbert_similarity": round(sim, 4)
                    }
                    for idx, utt, sim in candidates
                ],
                "all_utterances": [
                    {"index": i, "utterance": u}
                    for i, u in enumerate(raw_utts)
                ]
            }

        return self._build(iu_table, disfluency_stats, spatial_stats, pause_stats)

    # --------------------------------------------------
    # Aggregation
    # --------------------------------------------------
    def _build(
        self,
        iu_table: Dict,
        disfluency_stats: Dict,
        spatial_stats: Dict,
        pause_stats: Dict = None
    ) -> Dict:
        pause_stats = pause_stats or {"long_pauses": 0}

        # 1. Content Scoring
        core_scores = [iu_table[k]["score"] for k in self.CORE_IUS if k in iu_table]
        context_scores = [iu_table[k]["score"] for k in self.CONTEXT_IUS if k in iu_table]

        core_denom = len(self.CORE_IUS)
        context_denom = len(self.CONTEXT_IUS)

        core_recall = sum(core_scores) / core_denom if core_denom > 0 else 0.0
        context_recall = sum(context_scores) / context_denom if context_denom > 0 else 0.0

        iu_normalized = 0.8 * core_recall + 0.2 * context_recall

        # 2. Fluency Scoring (Hybrid: Text + Audio)
        # Part A: Text Disfluency ("um", "uh")
        raw_text_disfluency = disfluency_stats.get("disfluency_score", 0.0)
        penalty_text = min(raw_text_disfluency, 0.30)  # Cap text penalty at 30%

        # Part B: Audio Pause Penalty (> 3.0s)
        # 5% penalty per long pause
        long_pauses = pause_stats.get("long_pauses", 0)
        penalty_audio = min(long_pauses * 0.05, 0.30)  # Cap audio penalty at 30%

        # Combined Fluency
        fluency_score = max(0.0, 1.0 - (penalty_text + penalty_audio))

        # 3. Spatial Scoring
        spatial_density = spatial_stats.get("spatial_density", 0.0)
        spatial_score = min(1.0, spatial_density / 0.20)

        # 4. Final Composition
        final_score = (
            self.IU_WEIGHT * iu_normalized +
            self.FLUENCY_WEIGHT * fluency_score +
            self.SPATIAL_WEIGHT * spatial_score
        )

        return {
            "summary": {
                "final_score": round(final_score, 4),
                "iu_normalized": round(iu_normalized, 4),
                "core_recall": round(core_recall, 4),
                "context_recall": round(context_recall, 4),
                "fluency_score": round(fluency_score, 4),
                "spatial_score": round(spatial_score, 4),
                # UI Helpers
                "penalty_text": round(penalty_text, 4),
                "penalty_audio": round(penalty_audio, 4)
            },
            "details": {
                "iu_table": iu_table,
                "fluency_details": disfluency_stats,
                "pause_details": pause_stats,  # Added to details
                "spatial_details": spatial_stats,
                "conceptual_summary": {
                    "core": {
                        "missed": [
                            k for k in self.CORE_IUS
                            if k in iu_table and iu_table[k]["score"] == 0
                        ]
                    },
                    "context": {
                        "missed": [
                            k for k in self.CONTEXT_IUS
                            if k in iu_table and iu_table[k]["score"] == 0
                        ]
                    }
                }
            }
        }

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    def _iu_type(self, iu):
        return "core" if iu in self.CORE_IUS else "context"

    def _miss(self, iu, txt, utterances):
        return {
            "iu_id": iu,
            "iu_type": self._iu_type(iu),
            "expected_text": txt,
            "matched_utterance": None,
            "utterance_index": None,
            "sbert_similarity": 0.0,
            "entailment_score": 0.0,
            "score": 0.0,
            "match_type": "missed",
            "decision_reason": "No candidate above threshold",
            "candidates": [],
            "all_utterances": [
                {"index": i, "utterance": u}
                for i, u in enumerate(utterances)
            ]
        }

    def _score_empty(self, templates, disfluency_stats, spatial_stats, pause_stats):
        return self._build(
            {iu: self._miss(iu, txt, []) for iu, txt in templates.items()},
            disfluency_stats,
            spatial_stats,
            pause_stats
        )