"""
Picture Loader
--------------
Loads picture assets for picture description tasks.
"""

import os


def load_picture(picture_dir: str, picture_name: str) -> str:
    """
    Resolve path to picture file.

    Args:
        picture_dir (str): Directory containing pictures
        picture_name (str): File name (e.g. cookie_theft.png)

    Returns:
        str: Absolute path to image
    """
    path = os.path.join(picture_dir, picture_name)

    if not os.path.exists(path):
        raise FileNotFoundError(f"Picture not found: {path}")

    return path