"""
Memory QA Pipeline (FINAL - CLINICAL GRADE)
-------------------------------------------
Robust scoring for Encoding + Retention with penalties and safeguards.
"""

from typing import Dict, Any, List, Optional
import os
import json

from ..loaders.load_iu_semantic_templates import load_iu_semantic_templates
from ..preprocessing.text_cleaning import clean_text
from ..preprocessing.sentence_splitter import split_into_sentences
from ..scoring.sbert_encoder import SBERTEncoder
from ..scoring.thresholds import IUThresholds
from ..scoring.scorer import IUScorer
from ..scoring.pause_eval import PauseEvaluator


class MemoryQAPipeline:
    def __init__(
        self,
        data_dir: str,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        self.data_dir = data_dir

        # Load templates
        self.iu_semantic_templates = load_iu_semantic_templates(
            os.path.join(self.data_dir, "iu_semantic_templates.json")
        )

        with open(
            os.path.join(self.data_dir, "iu_mapping.json"),
            "r",
            encoding="utf-8"
        ) as f:
            self.iu_mappings = json.load(f)

        # Models
        self.encoder = SBERTEncoder(model_name=model_name)
        self.thresholds = IUThresholds()
        self.scorer = IUScorer(self.encoder, self.thresholds)

        self.pause_evaluator = PauseEvaluator(pause_threshold=2.0)

    # ==================================================
    # 🧠 MEMORY SESSION SCORING
    # ==================================================
    def score_memory_session(
        self,
        story_id: str,
        immediate_text: str,
        delayed_text: str,
        immediate_segments: Optional[List[Dict]] = None,
        delayed_segments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:

        # -------- IMMEDIATE --------
        immediate_result = self.score_recall(
            story_id, immediate_text, immediate_segments
        )

        # -------- DELAYED --------
        delayed_result = self.score_recall(
            story_id, delayed_text, delayed_segments
        )

        immediate_score = float(
            immediate_result["scores"]["summary"]["final_score"]
        )

        delayed_score_raw = float(
            delayed_result["scores"]["summary"]["final_score"]
        )

        # 🚨 Prevent hallucinated improvement
        delayed_score = min(delayed_score_raw, immediate_score)

        # -------- CORE METRICS --------
        memory_drop = max(0.0, immediate_score - delayed_score)

        if immediate_score > 0:
            forgetting_rate = memory_drop / immediate_score
            recall_efficiency = delayed_score / immediate_score
            valid_memory = True
        else:
            forgetting_rate = None
            recall_efficiency = None
            valid_memory = False

        # -------- STATUS LOGIC (IMPROVED) --------
        # ---------------- STATUS LOGIC (FINAL FIX) ----------------
        if not valid_memory:
            memory_status = "invalid"

        # 🚨 Severe encoding failure
        elif immediate_score < 0.4:
            memory_status = "high_risk"

        # 🚨 Severe forgetting
        elif forgetting_rate is not None and forgetting_rate > 0.45:
            memory_status = "high_risk"

        # 🚨 COMBINED RISK (VERY IMPORTANT)
        elif (
                immediate_score < 0.65 and
                forgetting_rate is not None and
                forgetting_rate > 0.35
        ):
            memory_status = "high_risk"

        # Moderate encoding issue
        elif immediate_score < 0.65:
            memory_status = "mci"

        # Healthy retention
        elif forgetting_rate is not None and forgetting_rate < 0.2:
            memory_status = "healthy"

        else:
            memory_status = "mci"

        # -------- EXPLANATION --------
        explanation_map = {
            "healthy": "Memory retention is stable with minimal information loss.",
            "mci": "Moderate memory decline observed with noticeable forgetting.",
            "high_risk": "Significant impairment in encoding or retention detected.",
            "invalid": "Memory assessment could not be reliably performed."
        }

        explanation = explanation_map[memory_status]

        # ==================================================
        # 🎯 FINAL MEMORY SCORE (BALANCED MODEL)
        # ==================================================
        encoding_weight = 0.5
        retention_weight = 0.5

        final_memory_score = (
            immediate_score * encoding_weight +
            delayed_score * retention_weight
        ) * 100

        # -------- PENALTIES --------

        # 1. Forgetting penalty
        if forgetting_rate is not None:
            final_memory_score -= forgetting_rate * 20

        # 2. Encoding penalty (VERY IMPORTANT)
        if immediate_score < 0.65:
            encoding_penalty = (0.65 - immediate_score) * 60
            final_memory_score -= encoding_penalty

        # 3. Safety clamp
        final_memory_score = max(0.0, min(100.0, final_memory_score))

        # -------- IU SUMMARY --------
        immediate_iu = immediate_result["scores"]["summary"].get("matched_units", 0)
        delayed_iu = delayed_result["scores"]["summary"].get("matched_units", 0)

        # -------- OUTPUT --------
        return {
            "story_id": story_id,

            "immediate": immediate_result,
            "delayed": delayed_result,

            "memory_drop": round(memory_drop, 4),

            "memory_analysis": {
                "immediate_score": round(immediate_score, 4),
                "delayed_score": round(delayed_score, 4),
                "forgetting_rate": None if forgetting_rate is None else round(forgetting_rate, 4),
                "recall_efficiency": None if recall_efficiency is None else round(recall_efficiency, 4),
                "memory_status": memory_status,
                "valid_memory_assessment": valid_memory,
                "final_memory_score": round(final_memory_score, 2),
                "explanation": explanation
            },

            "iu_summary": {
                "immediate_iu_recalled": immediate_iu,
                "delayed_iu_recalled": delayed_iu
            }
        }

    # ==================================================
    # 🔍 SINGLE RECALL SCORING
    # ==================================================
    def score_recall(
        self,
        story_id: str,
        recall_text: str,
        recall_segments: Optional[List[Dict]] = None,
        alpha: float = 0.7
    ) -> Dict[str, Any]:

        if story_id not in self.iu_semantic_templates:
            raise ValueError(f"Story ID '{story_id}' not found")

        # -------- CLEAN TEXT --------
        cleaned_text = clean_text(recall_text)
        recall_sentences = split_into_sentences(cleaned_text)

        # -------- PAUSE ANALYSIS --------
        if recall_segments:
            pause_metrics = self.pause_evaluator.evaluate(recall_segments)
        else:
            pause_metrics = self.pause_evaluator._empty()

        # -------- IU SCORING --------
        iu_templates = self.iu_semantic_templates[story_id]

        scores = self.scorer.score_story_with_gmatch(
            recall_sentences=recall_sentences,
            iu_templates=iu_templates,
            pause_stats=pause_metrics
        )

        return {
            "story_id": story_id,
            "sentence_count": len(recall_sentences),
            "scores": scores,
            "pause_analysis": pause_metrics,

            "composite": {
                "normalized_score": None,
                "risk_band": None,
                "explanation": None
            }
        }