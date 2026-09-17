"""
Clinical Thresholds (Speech Analysis)
------------------------------------
Central configuration for all linguistic + cognitive metrics.

IMPORTANT:
- All thresholds are clinically calibrated
- DO NOT hardcode thresholds inside feature files
"""

from typing import Dict


class ClinicalThresholds:

    def __init__(self):

        # --------------------------------------------------
        # IDEA DENSITY
        # --------------------------------------------------
        self.idea_density = {
            "impaired": 0.30,
            "borderline": 0.40,
            "very_healthy": 0.45
        }

        # --------------------------------------------------
        # LEXICAL DIVERSITY (MATTR)
        # --------------------------------------------------
        self.mattr = {
            "impaired": 0.45,
            "borderline": 0.60
        }

        self.ttr = {
            "impaired": 4.5,
            "borderline": 6.0
        }

        # --------------------------------------------------
        # COHERENCE (SBERT cosine)
        # --------------------------------------------------
        self.coherence = {
            "impaired": 0.20,
            "borderline": 0.30,
            "healthy": 0.75
        }

        # --------------------------------------------------
        # REPETITION
        # --------------------------------------------------
        self.repetition = {
            "mild": 0.15,
            "severe": 0.35
        }

        # --------------------------------------------------
        # SYNTACTIC COMPLEXITY (Mean Clause Length)
        # --------------------------------------------------
        self.syntax = {
            "impaired": 6.0,
            "borderline": 10.0
        }

        # --------------------------------------------------
        # QUALITY CONTROL (QC)
        # --------------------------------------------------
        self.qc = {
            "min_words": 50,
            "min_clauses": 3,
            "low_conf_words": 80
        }

        # --------------------------------------------------
        # Perplexity
        # --------------------------------------------------
        self.perplexity = {
            "healthy": 20,
            "borderline": 50
        }

        # --------------------------------------------------
        # Fluency
        # --------------------------------------------------
        self.fluency = {
            "impaired": 70.0,
            "borderline": 100.0,
            "fast": 160.0
        }

        # --------------------------------------------------
        # FINAL SCORING WEIGHTS
        # --------------------------------------------------
        self.weights = {
            "idea": 0.23,
            "coherence": 0.23,
            "repetition": 0.17,
            "fluency": 0.15,
            "ttr": 0.10,
            "syntax": 0.07,
            "perplexity": 0.05
        }

        # --------------------------------------------------
        # FINAL DIAGNOSIS THRESHOLDS
        # --------------------------------------------------
        self.final_score = {
            "healthy": 75,
            "mci": 50,
            "mci_high_risk": 40,
        }


# Singleton (IMPORTANT)
Thresholds = ClinicalThresholds()