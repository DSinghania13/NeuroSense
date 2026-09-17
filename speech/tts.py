"""
TTS Module
----------
Text-to-Speech using gTTS.
Used for story narration in Story Recall.
"""

from gtts import gTTS
import os


def text_to_speech(
    text: str,
    output_path: str,
    lang: str = "en"
):
    """
    Convert text to speech and save as audio file.

    Args:
        text (str): Text to convert
        output_path (str): Output audio file path (.mp3)
        lang (str): Language code
    """
    if not text.strip():
        raise ValueError("Text for TTS is empty")

    tts = gTTS(text=text, lang=lang)
    tts.save(output_path)

    return output_path