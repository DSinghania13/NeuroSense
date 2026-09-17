"""
Free Speech Scorer
----------------------
Combines all linguistic signals into a unified cognitive risk score.
Outputs 'summary' and 'details' objects for easy backend consumption.
"""

from typing import Dict
from .thresholds import Thresholds


class FinalScorer:

    def __init__(self):
        # Feature weights
        self.weights = Thresholds.weights

    # --------------------------------------------------
    def score(
        self,
        disfluency: Dict, repetition: Dict, idea: Dict,
        ttr: Dict, syntax: Dict, coherence: Dict,
        perplexity: Dict, fluency: Dict, duration_sec: float, qc: Dict
    ) -> Dict:

        # -----------------------------
        # 0. QC FAIL → HARD STOP
        # -----------------------------
        if not qc.get("is_valid", False):
            return {
                "summary": {
                    "cognitive_score": None,
                    "risk_level": "invalid",
                    "confidence": "low",
                    "explanation": qc.get("reason", "Insufficient data.")
                },
                "details": {}
            }

        # -----------------------------
        # 1. NORMALIZE FEATURES (With Safety Defaults)
        # -----------------------------
        idea = idea or {}
        coherence = coherence or {}
        repetition = repetition or {}
        fluency = fluency or {}
        ttr = ttr or {}
        syntax = syntax or {}
        perplexity = perplexity or {}
        disfluency = disfluency or {} # Ensure disfluency has a fallback

        scores = {}

        # IDEA DENSITY (Fixed logic: strictly > borderline is healthy)
        val = idea.get("idea_density", 0.0)
        if val > Thresholds.idea_density["very_healthy"]:
            scores["idea"] = 1.0
        elif val > Thresholds.idea_density["borderline"]:
            scores["idea"] = 0.8
        elif val >= Thresholds.idea_density["impaired"]:
            scores["idea"] = 0.6
        else:
            scores["idea"] = 0.2

        # COHERENCE (Fixed logic: Must ascend properly)
        # Normal coherence math
        coh_score = coherence.get("coherence_score", 0.0)

        if coh_score >= Thresholds.coherence["healthy"]:
            base_coh = 1.0
        elif coh_score >= Thresholds.coherence["borderline"]:
            base_coh = 0.6
        else:
            base_coh = 0.2

        # Dynamic Clinical Adjustment:
        # If the repetition ratio is severe, it fundamentally destroys coherence.
        rep_ratio = repetition.get("repetition_ratio", 0.0)
        if rep_ratio > 0.5:
            scores["coherence"] = 0.2  # Force to impaired
        else:
            scores["coherence"] = base_coh

        # REPETITION (Fixed logic: Lower is better)
        val = repetition.get("repetition_ratio", 1.0)
        if val <= Thresholds.repetition["mild"]:
            scores["repetition"] = 1.0
        elif val <= Thresholds.repetition["severe"]:
            scores["repetition"] = 0.6
        else:
            scores["repetition"] = 0.2

        # FLUENCY (WPM Speed + Disfluency Smoothness)
        level = fluency.get("fluency_level", "impaired")

        # 1. Base points from WPM
        if level == "healthy":
            base_fluency = 1.0
        elif level in ["borderline", "borderline_fast"]:
            base_fluency = 0.6
        else:
            base_fluency = 0.2

        # 2. Penalty from Disfluency (Fillers/Pauses)
        # If disfluency_score is 0.15, it means 15% of their speech was stumbling.
        df_penalty = disfluency.get("disfluency_score", 0.0)

        if df_penalty > 0.1:
            df_penalty *= 1.5
        elif df_penalty > 0.05:
            df_penalty *= 1.2

        # 3. Combine and clamp at 0.2 minimum
        scores["fluency"] = max(0.2, base_fluency - df_penalty)

        # TTR
        level = ttr.get("ttr_level", "impaired")
        if level == "healthy":
            scores["ttr"] = 1.0
        elif level == "borderline":
            scores["ttr"] = 0.6
        else:
            scores["ttr"] = 0.2

        # SYNTAX
        level = syntax.get("syntactic_complexity", "impaired")
        if level == "healthy":
            scores["syntax"] = 1.0
        elif level == "borderline":
            scores["syntax"] = 0.6
        else:
            scores["syntax"] = 0.2

        # PERPLEXITY (Fixed logic: Gated by reliability)
        if not perplexity.get("is_reliable", True):
            scores["perplexity"] = 0.5  # Neutral impact if unreliable
        else:
            val = perplexity.get("perplexity", 100.0)
            if val <= Thresholds.perplexity["healthy"]:
                scores["perplexity"] = 1.0
            elif val <= Thresholds.perplexity["borderline"]:
                scores["perplexity"] = 0.6
            else:
                scores["perplexity"] = 0.2

        # -----------------------------
        # 2. WEIGHTED SCORE
        # -----------------------------
        total_score = 0.0
        feature_contribution = {}

        for key, weight in self.weights.items():
            pts = scores.get(key, 0.0) * weight
            total_score += pts
            feature_contribution[key] = round(pts * 100, 2)

        final_score = total_score * 100

        # -----------------------------
        # 2.5 CLINICAL PENALTIES (NEW 🔥)
        # -----------------------------
        coh_val = coherence.get("coherence_score", 0.0)
        rep_val = repetition.get("repetition_ratio", 0.0)

        # 🚨 Coherence penalty (Topic Drift = critical)
        if coh_val < 0.4:
            if coh_val < 0.2:
                final_score *= 0.65
            else:
                penalty = (0.4 - coh_val) * 0.4
                final_score *= (1 - penalty)

        # 🚨 Repetition penalty (Looping / perseveration)
        if rep_val > 0.7:
            final_score *= 0.70
        elif rep_val > 0.4:
            final_score *= 0.85

        # -----------------------------
        # 2.6 IDEA VAGUENESS PENALTY (move AFTER penalties)
        # -----------------------------
        vague_penalty = min(0.25, idea.get("vague_words_count", 0) * 0.03)
        final_score *= (1 - vague_penalty)

        # -----------------------------
        # 3. RISK CLASSIFICATION
        # -----------------------------
        if final_score >= Thresholds.final_score["healthy"]:
            risk = "healthy"
        elif Thresholds.final_score["mci"] <= final_score < Thresholds.final_score["healthy"]:
            risk = "mci"
        elif Thresholds.final_score["mci_high_risk"] <= final_score < Thresholds.final_score["mci"]:
            risk = "mci_high_risk"
        else:
            risk = "high_risk"

        qc_conf = qc.get("confidence", "LOW")
        model_conf = self.compute_confidence(scores, duration_sec)

        if qc_conf == "LOW" and model_conf == "LOW":
            final_conf = "LOW"
        elif qc_conf == "HIGH" and model_conf == "HIGH":
            final_conf = "HIGH"
        else:
            final_conf = "MEDIUM"

        # -----------------------------
        # 4. JSON OUTPUT
        # -----------------------------
        return {
            "summary": {
                "cognitive_score": round(final_score, 2),
                "risk_level": risk,
                "confidence": final_conf,
                "explanation": self._build_explanation(scores, {
                    "idea_density": idea,
                    "coherence": coherence,
                    "repetition": repetition,
                    "fluency": fluency,
                    "disfluency": disfluency,
                    }, final_score)
            },
            "details": {
                "normalized_points": scores,
                "feature_contribution": feature_contribution,
                "raw_metrics": {
                    "idea_density": idea,
                    "coherence": coherence,
                    "repetition": repetition,
                    "fluency": fluency,
                    "lexical_diversity": ttr,
                    "syntax": syntax,
                    "perplexity": perplexity,
                    "disfluency": disfluency
                }
            }
        }

    # --------------------------------------------------
    # CLINICAL EXPLANATION ENGINE
    # --------------------------------------------------
    def _build_explanation(self, scores: Dict, raw_metrics: Dict,final_score: float) -> str:

        feature_names = {
            "coherence": "topic drift",
            "idea": "low semantic specificity (empty speech)",
            "repetition": "high verbal repetition",
            "fluency": "slow or effortful delivery",
            "ttr": "reduced vocabulary richness",
            "syntax": "simplified grammar",
            "perplexity": "grammatical disorganization"
        }

        primary = []
        secondary = []

        if final_score < 85:
            include_secondary = True
        else:
            include_secondary = False

        # Find which features triggered a 0.2 (Impaired) or 0.6 (Borderline) penalty
        for feature, points in scores.items():
            if points <= 0.2:
                primary.append(feature_names[feature])
            elif points <= 0.6 and include_secondary:
                if feature == "coherence":
                    coh_val = raw_metrics.get("coherence", {}).get("coherence_score", 1.0)
                    if coh_val < 0.35:
                        secondary.append(feature_names[feature])

                elif feature == "idea":
                    vague = raw_metrics.get("idea_density", {}).get("vague_words_count", 0)
                    if vague >= 3:
                        secondary.append(feature_names[feature])

                else:
                    secondary.append(feature_names[feature])

        parts = []
        if primary:
            parts.append("Primary issue(s): " + ", ".join(primary))
        if secondary:
            parts.append("Secondary issue(s): " + ", ".join(secondary))

        # Add explicit disfluency warning if high
        disfluency = raw_metrics.get("disfluency", {})
        if disfluency.get("disfluency_score", 0.0) > 0.10:
            parts.append("High rate of fillers/pauses detected")

        if not parts:
            return "No significant cognitive irregularities detected."

        return " | ".join(parts)

    def compute_confidence(self, feature_scores, duration_sec):
        import numpy as np

        if duration_sec < 10:
            return "LOW"

        values = list(feature_scores.values())

        mean_score = np.mean(values)
        std_dev = np.std(values)

        # Stability + strength combined
        if mean_score > 0.85 and std_dev < 0.15:
            return "HIGH"
        elif mean_score > 0.65 and std_dev < 0.25:
            return "MEDIUM"
        else:
            return "LOW"