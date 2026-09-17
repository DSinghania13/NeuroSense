"""
Entailment Engine
----------------
Singleton Cross-Encoder wrapper for NLI inference.
Loads the model ONCE and reuses it everywhere.
"""

from sentence_transformers import CrossEncoder


class EntailmentEngine:
    _model = None

    @classmethod
    def _load(cls):
        if cls._model is None:
            print("🔵 Loading Cross-Encoder NLI model (one time)...")
            cls._model = CrossEncoder("cross-encoder/nli-deberta-v3-base")
            print("🟢 NLI model loaded.")
        return cls._model

    @classmethod
    def score(cls, sentence_pairs):
        """
        sentence_pairs: List[(utterance, IU_text)]
        returns: numpy array of shape (N, 3)  -> [contradiction, entailment, neutral]
        """
        model = cls._load()
        return model.predict(sentence_pairs)