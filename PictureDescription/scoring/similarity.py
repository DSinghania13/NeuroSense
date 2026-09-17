"""
Semantic Similarity Utilities
-----------------------------
Provides cosine similarity helpers for IU scoring.
"""

import numpy as np


def cosine_similarity(
    a: np.ndarray,
    b: np.ndarray
) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        a (np.ndarray): Vector A
        b (np.ndarray): Vector B

    Returns:
        float: Cosine similarity in [0, 1]
    """
    if a.ndim != 1 or b.ndim != 1:
        raise ValueError("cosine_similarity expects 1D vectors")

    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0

    return float(np.dot(a, b) / denom)


def max_similarity(
    query_embedding: np.ndarray,
    corpus_embeddings: np.ndarray
) -> float:
    """
    Compute maximum cosine similarity between a query
    and a list/array of embeddings.

    Args:
        query_embedding (np.ndarray): Shape (d,)
        corpus_embeddings (np.ndarray): Shape (n, d)

    Returns:
        float: Maximum similarity score
    """
    if corpus_embeddings is None or len(corpus_embeddings) == 0:
        return 0.0

    similarities = [
        cosine_similarity(query_embedding, emb)
        for emb in corpus_embeddings
    ]

    return max(similarities)