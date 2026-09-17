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
from StoryRecall.pipeline.story_recall_pipeline import StoryRecallPipeline

class StoryRecallAudioService:
    def __init__(
        self,
        data_dir: str,
        whisper_model: str = "small",
        language: str = "en"
    ):
        print(f"🔵 Loading Whisper ({whisper_model})...")
        self.pipeline = StoryRecallPipeline(data_dir=data_dir)
        self.asr = ASR(model_size=whisper_model, language=language)

    def generate_story_audio(self, story_text: str, output_path: str) -> str:
        return text_to_speech(story_text, output_path)

    def score_recall_audio(
        self,
        story_id: str,
        recall_audio_path: str,
        alpha: float = 0.7
    ) -> Dict[str, Any]:

        # 1. Validate
        wav_path = ensure_wav(recall_audio_path)

        # UNPACK TUPLE
        recall_text, recall_segments = self.asr.transcribe(wav_path)

        result = self.pipeline.score_recall(
            story_id=story_id,
            recall_text=recall_text,
            recall_segments=recall_segments,  # Pass to pipeline
            alpha=alpha
        )
        result["transcript"] = recall_text
        return result