"""
IU Semantic Templates Loader
----------------------------
Loads story-wise IU semantic templates from JSON.
This file performs NO scoring or preprocessing.
"""

import json
from typing import Dict


def load_iu_semantic_templates(
    file_path: str
) -> Dict[str, Dict[str, str]]:
    """
    Load IU semantic templates from a JSON file.

    Args:
        file_path (str): Path to iu_semantic_templates.json

    Returns:
        Dict[str, Dict[str, str]]:
            {
              story_id: {
                  "IU1": "...",
                  "IU2": "...",
                  ...
              }
            }
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic structural validation
    if not isinstance(data, dict):
        raise ValueError("IU semantic templates JSON must be a dictionary")

    for story_id, iu_dict in data.items():
        if not isinstance(iu_dict, dict):
            raise ValueError(
                f"Story {story_id} must map to a dictionary of IU templates"
            )

        for iu_key, sentence in iu_dict.items():
            if not iu_key.startswith("IU"):
                raise ValueError(
                    f"Invalid IU key '{iu_key}' in story {story_id}"
                )

            if not isinstance(sentence, str) or not sentence.strip():
                raise ValueError(
                    f"Empty or invalid sentence for {iu_key} in story {story_id}"
                )

    return data