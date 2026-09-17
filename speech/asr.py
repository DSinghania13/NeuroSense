"""
ASR Module (UPDATED)
--------------------
Returns text AND timestamps for pause analysis.
"""
import whisper
import os
import ssl
import certifi
from typing import Tuple, List, Dict


# Fix for SSL errors on some environments
def _patched_https_context():
    return ssl.create_default_context(cafile=certifi.where())


ssl._create_default_https_context = _patched_https_context


_MODEL_CACHE = {}

class ASR:
    def __init__(self, model_size: str = "small", language: str = None):
        if model_size not in _MODEL_CACHE:
            _MODEL_CACHE[model_size] = whisper.load_model(model_size)
        self.model = _MODEL_CACHE[model_size]
        self.language = language

    def transcribe(self, audio_path: str) -> Tuple[str, List[Dict]]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"File not found: {audio_path}")

        # fp16=False is crucial for CPU execution
        result = self.model.transcribe(
            audio_path,
            language=self.language,
            fp16=False,
            verbose=False
        )

        # RETURN BOTH TEXT AND SEGMENTS
        return result["text"].strip(), result["segments"]