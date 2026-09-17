"""
Threshold Rules (CALIBRATED)
----------------------------
Unified thresholds for SBERT + STS Cross-Encoder IU scoring.

Updated to align with STS model outputs where ~0.60 is often a high-quality match.
"""

from typing import Tuple


class IUThresholds:
    """
    Threshold configuration for IU scoring.
    """

    def __init__(
        self,
        # ---------- SBERT (semantic retrieval gate) ----------
        # Lowered to 0.30 to ensure we don't block valid candidates early.
        # Your logs showed "Last Monday morning" was missed at 0.44.
        sbert_gate: float = 0.15,

        # ---------- STS / Cross-Encoder Thresholds ----------
        # A score > 0.35 is now considered a weak match (Paraphrase/Partial)
        entailment_weak: float = 0.25,

        # A score > 0.58 is now considered a strong match (Full Recall)
        # Your logs showed perfect recalls scoring between 0.60 - 0.70.
        entailment_strong: float = 0.50,

        # ---------- Legacy compatibility ----------
        # Kept aligned with new values to prevent breaking older functions
        partial: float = 0.25,
        full: float = 0.50
    ):
        """
        Args:
            sbert_gate (float): SBERT cosine gate
            entailment_weak (float): partial IU credit
            entailment_strong (float): full IU credit
        """

        # ---- Validation ----
        if not (0.0 <= sbert_gate <= 1.0):
            raise ValueError("sbert_gate must be between 0 and 1")

        if not (0.0 <= entailment_weak < entailment_strong <= 1.0):
            raise ValueError("Invalid entailment thresholds")

        # ---- New attributes (USED by IUScorer) ----
        self.sbert_gate = sbert_gate
        self.entailment_weak = entailment_weak
        self.entailment_strong = entailment_strong

        # ---- Legacy (DO NOT REMOVE) ----
        self.partial = partial
        self.full = full

    # --------------------------------------------------
    # Legacy API (kept so nothing else breaks)
    # --------------------------------------------------
    def score(self, similarity: float) -> float:
        if similarity >= self.full:
            return 1.0
        elif similarity >= self.partial:
            return 0.5
        return 0.0

    def as_tuple(self) -> Tuple[float, float]:
        return self.full, self.partial