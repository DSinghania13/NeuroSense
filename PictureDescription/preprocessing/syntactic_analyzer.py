"""
Syntactic Complexity Analyzer
-----------------------------
Extracts syntactic tree depth using spaCy dependency parses.

Clinical motivation:
- AD patients show shallow, list-like syntax
- Healthy controls show deeper hierarchical structure
"""

from typing import List, Dict
import spacy

# Load once (small + fast)
_NLP = spacy.load("en_core_web_sm")


def _tree_depth(token) -> int:
    """
    Recursively compute depth of dependency subtree.
    """
    if not list(token.children):
        return 1
    return 1 + max(_tree_depth(child) for child in token.children)


def analyze_syntax(utterances: List[str]) -> Dict:
    """
    Analyze syntactic complexity of utterances.

    Args:
        utterances (List[str]): cleaned utterances

    Returns:
        Dict: syntax statistics
    """
    depths = []

    for utt in utterances:
        doc = _NLP(utt)
        for sent in doc.sents:
            root = sent.root
            depths.append(_tree_depth(root))

    if not depths:
        return {
            "avg_tree_depth": 0.0,
            "max_tree_depth": 0,
            "sentence_count": 0
        }

    return {
        "avg_tree_depth": round(sum(depths) / len(depths), 3),
        "max_tree_depth": max(depths),
        "sentence_count": len(depths)
    }