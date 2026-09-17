"""
SBERT Encoder Module
-------------------
Loads a pretrained Sentence-BERT model once and provides
methods to encode text into semantic embeddings.

This module is used as a frozen semantic engine (no training).
"""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer


class SBERTEncoder:
    """
    Wrapper around Sentence-BERT for consistent encoding.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu"
    ):
        """
        Initialize SBERT model.

        Args:
            model_name (str): SBERT model name
            device (str): 'cpu' or 'cuda' (cpu recommended)
        """
        self.model_name = model_name
        self.device = device
        self.model = SentenceTransformer(model_name, device=device)

    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True
    ) -> np.ndarray:
        """
        Encode text(s) into embeddings.

        Args:
            texts (str or List[str]): Input text(s)
            normalize (bool): Whether to L2-normalize embeddings

        Returns:
            np.ndarray: Embedding vector(s)
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )

        return embeddings