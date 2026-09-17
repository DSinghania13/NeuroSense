"""
SBERT Encoder
-------------
Sentence-level semantic embedding using Sentence-BERT.

Shared encoder used for:
- IU semantic matching
- Utterance similarity
- Explainability pipelines

CPU-safe and production-ready.
"""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer


class SBERTEncoder:
    """
    Wrapper around Sentence-BERT for semantic encoding.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize SBERT model.

        Args:
            model_name (str): HuggingFace SBERT model name
        """
        self.model_name = model_name
        self.model = SentenceTransformer(
            model_name,
            device="cpu"
        )

    def encode(
        self,
        texts: Union[str, List[str]]
    ) -> np.ndarray:
        """
        Encode text(s) into embeddings.

        Args:
            texts (str or List[str]): Input text(s)

        Returns:
            np.ndarray:
              - shape (d,) for single string
              - shape (n, d) for list of strings
        """
        if isinstance(texts, str):
            embeddings = self.model.encode(
                [texts],
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return embeddings[0]

        if isinstance(texts, list):
            if len(texts) == 0:
                return np.empty((0, self.model.get_sentence_embedding_dimension()))

            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return embeddings

        raise TypeError("Input must be a string or a list of strings")