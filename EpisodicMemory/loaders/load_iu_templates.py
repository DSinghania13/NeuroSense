"""
IU Template Loader
------------------
Loads the global Information Unit (IU) template definition.
This file defines WHAT each IU represents (conceptual layer).
"""

import json
from typing import Dict, Any


def load_iu_templates(file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load IU template definitions from JSON.

    Expected format:
    {
        "IU1": {
            "name": "Time",
            "definition": "...",
            "examples": [...]
        },
        ...
    }

    Args:
        file_path (str): Path to iu_template.json

    Returns:
        Dict[str, Dict[str, Any]]: IU ID -> definition
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("IU template JSON must be a dictionary")

    for iu_id, iu_data in data.items():
        if not iu_id.startswith("IU"):
            raise ValueError(f"Invalid IU key: {iu_id}")

        if not isinstance(iu_data, dict):
            raise ValueError(f"{iu_id} must map to a dictionary")

        if "name" not in iu_data or not isinstance(iu_data["name"], str):
            raise ValueError(f"{iu_id} missing or invalid 'name'")

        if "definition" not in iu_data or not isinstance(iu_data["definition"], str):
            raise ValueError(f"{iu_id} missing or invalid 'definition'")

        if "examples" in iu_data:
            if not isinstance(iu_data["examples"], list):
                raise ValueError(f"{iu_id} 'examples' must be a list")

    return data