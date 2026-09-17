"""
Story Recall Pipeline (CORRECTED)
---------------------------------
End-to-end orchestration for Story Recall scoring.
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
from ..scoring.pause_eval import PauseEvaluator  # Import your existing class logic


class StoryRecallPipeline:
    """
    Story Recall scoring pipeline.
    """

    def __init__(
        self,
        data_dir: str,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        self.data_dir = data_dir

        # Load IU semantic templates
        self.iu_semantic_templates = load_iu_semantic_templates(
            os.path.join(self.data_dir, "iu_semantic_templates.json")
        )

        # Load canonical IU mappings
        with open(
            os.path.join(self.data_dir, "iu_mapping.json"),
            "r",
            encoding="utf-8"
        ) as f:
            self.iu_mappings = json.load(f)

        # Initialize scoring components
        self.encoder = SBERTEncoder(model_name=model_name)
        self.thresholds = IUThresholds()
        self.scorer = IUScorer(self.encoder, self.thresholds)

        # Initialize Pause Evaluator (Uses the class from pause_eval.py)
        self.pause_evaluator = PauseEvaluator(pause_threshold=2.0)

    # --------------------------------------------------
    def score_recall(
        self,
        story_id: str,
        recall_text: str,
        recall_segments: Optional[List[Dict]] = None,
        alpha: float = 0.7
    ) -> Dict[str, Any]:
        """
        Score a user's recall for a story.
        """

        if story_id not in self.iu_semantic_templates:
            raise ValueError(f"Story ID '{story_id}' not found")

        # ---------------- TEXT PROCESSING ----------------
        cleaned_text = clean_text(recall_text)
        recall_sentences = split_into_sentences(cleaned_text)

        # ---------------- PAUSE ANALYSIS ----------------
        # Use the class logic rather than rewriting it here
        if recall_segments:
            pause_metrics = self.pause_evaluator.evaluate(recall_segments)
        else:
            pause_metrics = self.pause_evaluator._empty()

        # ---------------- IU + STRUCTURE SCORING ----------------
        iu_templates = self.iu_semantic_templates[story_id]

        # FIX: Pass the calculated pause_stats into the scorer!
        scores = self.scorer.score_story_with_gmatch(
            recall_sentences=recall_sentences,
            iu_templates=iu_templates,
            pause_stats=pause_metrics  # <--- CRITICAL ADDITION
        )

        # ---------------- FINAL OUTPUT ----------------
        return {
            "story_id": story_id,
            "sentence_count": len(recall_sentences),

            "scores": scores,
            "pause_analysis": pause_metrics,

            # Reserved for next phase
            "composite": {
                "normalized_score": None,
                "risk_band": None,
                "explanation": None
            }
        }