"""
Free Speech Audio Service (Realtime Enabled)
--------------------------------------------
Handles:
✔ ASR transcription
✔ Realtime feedback (UX layer)
✔ Final cognitive scoring
"""

from typing import Dict, Any, List
import time

from speech.asr import ASR
from speech.audio_utils import ensure_wav

from FreeSpeech.pipeline.free_speech_pipeline import FreeSpeechPipeline


class FreeSpeechAudioService:

    def __init__(self, whisper_model: str = "small", language: str = "en"):
        self.last_words = None
        print(f"🔵 Loading Whisper ({whisper_model})...")
        self.asr = ASR(model_size=whisper_model, language=language)

        print("🧠 Loading NeuroSpeech Pipeline...")
        self.pipeline = FreeSpeechPipeline()

        # -----------------------------
        # Realtime State
        # -----------------------------
        self.reset_session()

    # --------------------------------------------------
    def reset_session(self):
        self.total_words = 0
        self.filler_count = 0
        self.start_time = time.time()
        self.last_words = []
        self.prev_word = None

    # --------------------------------------------------
    def process_chunk(self, text_chunk: str) -> Dict:
        """
        Called repeatedly during recording (streaming simulation)
        """

        words = text_chunk.lower().split()
        if not self.last_words:
            new_words = words
        else:
            overlap = 0
            for i in range(min(len(self.last_words), len(words))):
                if self.last_words[i:] == words[:len(self.last_words) - i]:
                    overlap = len(self.last_words) - i
                    break
            new_words = words[overlap:]
        self.total_words += len(new_words)
        self.last_words = words

        # -----------------------------
        # FILLER DETECTION
        # -----------------------------
        fillers = {"uh", "um", "hmm", "ah"}
        self.filler_count += sum(1 for w in new_words if w in fillers)

        # -----------------------------
        # SIMPLE REPETITION (Realtime-safe)
        # -----------------------------
        repetition = 0
        for w in new_words:
            if w == self.prev_word:
                repetition += 1
            self.prev_word = w

        # -----------------------------
        # TIME + WPM
        # -----------------------------
        duration = time.time() - self.start_time

        if duration > 0:
            wpm = (self.total_words / duration) * 60
        else:
            wpm = 0.0

        # -----------------------------
        # FEEDBACK ENGINE
        # -----------------------------
        feedback = self._generate_feedback(
            words=self.total_words,
            wpm=wpm,
            fillers=self.filler_count,
            repetition=repetition
        )


        return {
            "words": self.total_words,
            "target_min": 50,
            "progress": min(1.0, round(self.total_words / 50, 2)),
            "wpm": 0.0,
            "fillers": self.filler_count,
            "duration_sec": round(duration, 2),
            "feedback": "Listening..."
        }

    # --------------------------------------------------
    def _generate_feedback(self, words, wpm, fillers, repetition):
        # 1. PRIMARY GATING (Encourage Volume)
        if words < 30:
            return "Keep going, I'm listening..."
        if words < 50:
            return "Almost there, tell me a little more."

        # 2. BEHAVIORAL PROMPTS (Neutral & Encouraging)
        # If they are speaking very slowly (struggling to find words)
        if wpm > 0 and wpm < 70:
            return "Take your time, you're doing great."

        # If they are stuck in a repetition loop or using heavy fillers
        if repetition > 3 or fillers > 5:
            return "Good detail. What else comes to mind?"

        return "Excellent, keep going! 👍"

    # --------------------------------------------------
    def analyze_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        FINAL analysis (after recording stops)
        """

        wav_path = ensure_wav(audio_path)

        transcript, segments = self.asr.transcribe(wav_path)

        duration_sec = self._get_duration(segments)

        result = self.pipeline.analyze(
            raw_text=transcript,
            duration_sec=duration_sec
        )

        result["transcript"] = transcript
        result["duration_sec"] = duration_sec
        result["segments"] = segments

        return result

    # --------------------------------------------------
    def _get_duration(self, segments: List[Dict]) -> float:
        if not segments:
            return 0.0
        return segments[-1]["end"]