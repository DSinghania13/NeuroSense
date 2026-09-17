"""
Entailment Engine
-----------------
Shared Cross-Encoder NLI engine for all tasks.

Used by:
- Story Recall IU scoring
- Picture Description IU scoring
"""

import torch
from sentence_transformers import CrossEncoder


class EntailmentEngine:
    _model = None

    @classmethod
    def load(cls):
        if cls._model is None:
            print("🔵 Loading Cross-Encoder NLI model (shared)...")
            cls._model = CrossEncoder("cross-encoder/stsb-distilroberta-base")
            print("🟢 NLI model loaded.")
        return cls._model

    @classmethod
    def score(cls, pairs):
        """
        Args:
            pairs: List[(text, hypothesis)]
        Returns:
            entailment probabilities
        """
        model = cls.load()
        return model.predict(pairs)