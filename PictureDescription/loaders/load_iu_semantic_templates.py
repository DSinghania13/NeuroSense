"""
IU Semantic Template Loader
---------------------------
Loads IU definitions for picture description tasks.
"""

import json
import os
from typing import Dict


def load_iu_semantic_templates(file_path: str) -> Dict[str, Dict[str, str]]:
    """
    Load IU semantic templates from JSON.

    Args:
        file_path (str): Path to iu_semantic_templates.json

    Returns:
        Dict[picture_id, Dict[IU_id, IU_text]]
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"IU template file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic validation
    if not isinstance(data, dict):
        raise ValueError("IU template JSON must be a dictionary")

    for picture_id, iu_block in data.items():
        if not isinstance(iu_block, dict):
            raise ValueError(f"IU block for {picture_id} must be a dictionary")

    return data