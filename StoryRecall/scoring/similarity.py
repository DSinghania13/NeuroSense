"""
Similarity Utilities
--------------------
Provides cosine similarity computation between embeddings.
Used by IU scoring logic.
"""

import numpy as np
from typing import Union


def cosine_similarity(
    vec1: Union[np.ndarray, list],
    vec2: Union[np.ndarray, list]
) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        vec1 (np.ndarray or list): First embedding vector
        vec2 (np.ndarray or list): Second embedding vector

    Returns:
        float: Cosine similarity score
    """
    v1 = np.asarray(vec1).reshape(-1)
    v2 = np.asarray(vec2).reshape(-1)

    if v1.shape != v2.shape:
        raise ValueError("Vectors must have the same dimensions")

    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    if denom == 0.0:
        return 0.0

    return float(np.dot(v1, v2) / denom)


def max_similarity(
    query_embedding: np.ndarray,
    candidate_embeddings: np.ndarray
) -> float:
    """
    Compute maximum cosine similarity between a query embedding
    and a set of candidate embeddings.

    Args:
        query_embedding (np.ndarray): Shape (d,) or (1, d)
        candidate_embeddings (np.ndarray): Shape (n, d)

    Returns:
        float: Maximum cosine similarity score
    """
    query = query_embedding.reshape(1, -1)

    # Since embeddings are normalized, dot product = cosine similarity
    similarities = np.dot(candidate_embeddings, query.T).flatten()

    return float(np.max(similarities))