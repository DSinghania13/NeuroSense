"""
Stories Loader
--------------
Loads story texts and metadata from stories.json.
This module performs NO preprocessing or scoring.
"""

import json
from typing import Dict, Any


def load_stories(file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load stories from a JSON file.

    Expected format:
    {
        "1": {
            "text": "...",
            "word_count": 101
        },
        ...
    }

    Args:
        file_path (str): Path to stories.json

    Returns:
        Dict[str, Dict[str, Any]]: story_id -> story data
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Stories JSON must be a dictionary")

    for story_id, story_data in data.items():
        if not isinstance(story_data, dict):
            raise ValueError(f"Story {story_id} must map to a dictionary")

        if "text" not in story_data:
            raise ValueError(f"Story {story_id} is missing 'text' field")

        if not isinstance(story_data["text"], str) or not story_data["text"].strip():
            raise ValueError(f"Story {story_id} has empty or invalid text")

        if "word_count" in story_data:
            if not isinstance(story_data["word_count"], int):
                raise ValueError(
                    f"Story {story_id} 'word_count' must be an integer"
                )

    return data