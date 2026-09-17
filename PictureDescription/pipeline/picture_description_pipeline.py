"""
Picture Description Pipeline (UPDATED)
--------------------------------------
End-to-end pipeline for Picture Description scoring.

Updates:
- FIXED: Now passes 'spatial_stats' to the scorer.
- NEW:   Now passes 'pause_stats' (audio silence) to the scorer.
"""

from typing import Dict, Any
import os

from ..loaders.load_iu_semantic_templates import load_iu_semantic_templates
from ..preprocessing.text_cleaning import clean_text
from ..preprocessing.utterance_segmenter import segment_utterances
from ..scoring.sbert_encoder import SBERTEncoder
from ..scoring.thresholds import IUThresholds
from ..scoring.scorer import Scorer
from ..preprocessing.spatial_analyzer import analyze_spatial_relations


class PictureDescriptionPipeline:
    """
    Picture Description scoring pipeline.
    """

    def __init__(
        self,
        data_dir: str,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the pipeline.
        """
        self.data_dir = data_dir

        # Load IU templates once
        template_path = os.path.join(self.data_dir, "iu_semantic_templates.json")
        if not os.path.exists(template_path):
             raise FileNotFoundError(f"IU templates not found at: {template_path}")

        self.iu_templates = load_iu_semantic_templates(template_path)

        # Initialize scoring stack
        self.encoder = SBERTEncoder(model_name=model_name)
        self.thresholds = IUThresholds()
        self.scorer = Scorer(self.encoder, self.thresholds)

    # --------------------------------------------------
    # Main API
    # --------------------------------------------------
    def score_description(
        self,
        picture_id: str,
        description_text: str,
        pause_stats: Dict = None  # <--- NEW: Accept Audio Pause Data
    ) -> Dict[str, Any]:
        """
        Score a picture description.
        """

        # Validate picture ID
        iu_templates = self.iu_templates.get(picture_id)
        if iu_templates is None:
            raise ValueError(f"Picture ID '{picture_id}' not found in IU templates")

        # -----------------------------
        # Preprocessing
        # -----------------------------
        cleaned_text = clean_text(description_text)
        utterances = segment_utterances(description_text)

        # -----------------------------
        # Spatial Analysis
        # -----------------------------
        # Calculate spatial density (prepositions per utterance)
        spatial_stats = analyze_spatial_relations(utterances["cleaned_utterances"])

        # -----------------------------
        # IU Scoring
        # -----------------------------
        scores = self.scorer.score_picture_description(
            utterances=utterances,
            iu_templates=iu_templates,
            spatial_stats=spatial_stats,
            pause_stats=pause_stats or {}  # <--- PASS TO SCORER
        )

        # -----------------------------
        # Final Output
        # -----------------------------
        return {
            "picture_id": picture_id,
            "utterance_count": len(utterances["raw_utterances"]),
            "utterances": utterances,
            "spatial_stats": spatial_stats,
            "pause_stats": pause_stats or {}, # <--- RETURN DATA
            "scores": scores["summary"],      # numeric results
            "details": scores["details"]      # explainability
        }