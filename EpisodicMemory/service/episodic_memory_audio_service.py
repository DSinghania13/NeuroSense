"""
Story Recall Audio Service (UPDATED)
------------------------------------
Passes Whisper segments to the pipeline for Pause Analysis.
"""
from typing import Dict, Any
import os
from speech.tts import text_to_speech
from speech.asr import ASR
from speech.audio_utils import validate_audio_duration, ensure_wav
from EpisodicMemory.pipeline.episodic_memory_pipeline import MemoryQAPipeline

class MemoryQAAudioService:
    def __init__(
        self,
        data_dir: str,
        whisper_model: str = "small",
        language: str = "en"
    ):
        print(f"🔵 Loading Whisper ({whisper_model})...")
        self.pipeline = MemoryQAPipeline(data_dir=data_dir)
        self.asr = ASR(model_size=whisper_model, language=language)

    def generate_story_audio(self, story_text: str, output_path: str) -> str:
        return text_to_speech(story_text, output_path)

    def score_memory_session_audio(
            self,
            story_id: str,
            immediate_audio_path: str,
            delayed_audio_path: str,
            alpha: float = 0.7
    ) -> Dict[str, Any]:
        # ---------------- IMMEDIATE ----------------
        immediate_wav = ensure_wav(immediate_audio_path)
        immediate_text, immediate_segments = self.asr.transcribe(immediate_wav)

        # ---------------- DELAYED ----------------
        delayed_wav = ensure_wav(delayed_audio_path)
        delayed_text, delayed_segments = self.asr.transcribe(delayed_wav)

        # ---------------- PIPELINE ----------------
        result = self.pipeline.score_memory_session(
            story_id=story_id,
            immediate_text=immediate_text,
            delayed_text=delayed_text,
            immediate_segments=immediate_segments,
            delayed_segments=delayed_segments
        )

        # Attach transcripts (VERY useful for debugging/UI)
        result["transcripts"] = {
            "immediate": immediate_text,
            "delayed": delayed_text
        }

        return result