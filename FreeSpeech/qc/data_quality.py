"""
Free Speech Data Quality Control (QC)
------------------------------------
Clinical validation layer BEFORE feature extraction.

Purpose:
✔ Prevent unreliable metrics
✔ Ensure sufficient linguistic sample
✔ Assign confidence level

Based on:
- Clinical linguistics standards
- Dementia speech research
"""

from typing import Dict
from ..scoring.thresholds import Thresholds


class DataQuality:
    """
    Clinical QC gate for Free Speech.
    """

    # -----------------------------
    # Thresholds (FINALIZED)
    # -----------------------------
    MIN_WORDS = Thresholds.qc["min_words"]
    LOW_CONF_WORDS = Thresholds.qc["low_conf_words"]
    MIN_CLAUSES = Thresholds.qc["min_clauses"]

    def evaluate(
        self,
        total_words: int,
        clause_count: int,
        duration_sec: float = None
    ) -> Dict:
        """
        Evaluate data quality.

        Args:
            total_words (int)
            clause_count (int)
            duration_sec (float, optional)

        Returns:
            Dict:
                {
                    is_valid: bool,
                    confidence: str,
                    reason: str,
                    metrics: {...}
                }
        """

        # -----------------------------
        # HARD FAIL CONDITIONS
        # -----------------------------
        if total_words < self.MIN_WORDS:
            return self._fail(
                "Too few words (minimum 50 required)",
                total_words,
                clause_count,
                duration_sec
            )

        if clause_count < self.MIN_CLAUSES:
            return self._fail(
                "Too few clauses (minimum 3 required)",
                total_words,
                clause_count,
                duration_sec
            )

        # -----------------------------
        # CONFIDENCE LEVEL
        # -----------------------------
        if total_words < self.LOW_CONF_WORDS:
            confidence = "LOW"
            reason = "Borderline sample size (50–79 words)"
        else:
            confidence = "HIGH"
            reason = "Sufficient sample size"

        return {
            "is_valid": True,
            "confidence": confidence,
            "reason": reason,
            "metrics": {
                "total_words": total_words,
                "clause_count": clause_count,
                "duration_sec": duration_sec
            }
        }

    # -----------------------------
    # FAIL HANDLER
    # -----------------------------
    def _fail(self, reason, words, clauses, duration):
        return {
            "is_valid": False,
            "confidence": "INVALID",
            "reason": reason,
            "metrics": {
                "total_words": words,
                "clause_count": clauses,
                "duration_sec": duration
            }
        }