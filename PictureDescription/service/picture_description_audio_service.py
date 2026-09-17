"""
Picture Description Audio Service (FIXED)
-----------------------------------------
Integrates ASR, Pause Detection, and Scoring.

Updates:
- FIXED: Forces transcript to string (prevents tuple errors).
- NEW:   Implements silence detection for Anomia scoring.
"""

from typing import Dict, Any
from pydub import AudioSegment, silence

from speech.asr import ASR
from speech.audio_utils import ensure_wav, validate_audio_duration
from ..pipeline.picture_description_pipeline import PictureDescriptionPipeline


class PictureDescriptionAudioService:
    """
    Audio-based Picture Description service.
    """

    def __init__(
        self,
        data_dir: str,
        whisper_model: str = "small",
        language: str = "en"
    ):
        """
        Initialize audio service.
        """
        self.pipeline = PictureDescriptionPipeline(data_dir=data_dir)
        self.asr = ASR(model_size=whisper_model, language=language)

    # --------------------------------------------------
    # Helper: Pause Detection
    # --------------------------------------------------
    def _detect_pauses(
        self,
        wav_path: str,
        min_silence_len: int = 3000,
        silence_thresh: int = -40
    ) -> Dict[str, Any]:
        """
        Detect cognitive pauses (silence) in the audio.

        Args:
            wav_path: Path to WAV file
            min_silence_len: Threshold in ms (3000ms = 3.0s)
            silence_thresh: dBFS threshold for silence

        Returns:
            Dict with 'long_pauses' count and duration.
        """
        try:
            audio = AudioSegment.from_wav(wav_path)

            # Returns list of [start, end] tuples
            silence_chunks = silence.detect_silence(
                audio,
                min_silence_len=min_silence_len,
                silence_thresh=silence_thresh
            )

            count = len(silence_chunks)
            total_duration = sum([(end - start) for start, end in silence_chunks])

            return {
                "long_pauses": count,
                "total_pause_duration_ms": total_duration,
                "threshold_sec": min_silence_len / 1000.0
            }
        except Exception as e:
            print(f"⚠️ Pause detection warning: {e}")
            return {"long_pauses": 0, "total_pause_duration_ms": 0}

    # --------------------------------------------------
    # Main API
    # --------------------------------------------------
    def score_description_audio(
        self,
        picture_id: str,
        audio_path: str
    ) -> Dict[str, Any]:
        """
        Transcribe and score a picture description from audio.
        """
        # 1. Audio Validation
        validate_audio_duration(audio_path)
        wav_path = ensure_wav(audio_path)

        # 2. ASR Transcription
        raw_response = self.asr.transcribe(wav_path)

        # --- SAFETY FIX: Handle Tuple/Dict returns from ASR ---
        if isinstance(raw_response, tuple):
            # If (text, confidence), take text
            transcript = raw_response[0]
        elif isinstance(raw_response, dict):
            transcript = raw_response.get("text", "")
        else:
            transcript = str(raw_response)

        # 3. Detect Pauses (Cognitive Latency)
        # We use 3000ms (3s) as the clinical threshold for "Anomic Pause"
        pause_stats = self._detect_pauses(wav_path, min_silence_len=3000)

        # 4. Scoring Pipeline
        result = self.pipeline.score_description(
            picture_id=picture_id,
            description_text=transcript,
            pause_stats=pause_stats  # Pass audio metrics to scorer
        )

        # Attach transcript for UI transparency
        result["transcript"] = transcript

        return result