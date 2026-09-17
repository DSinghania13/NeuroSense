"""
Pause Evaluation for Story Recall
---------------------------------
Analyzes Whisper timestamps to capture retrieval difficulty.

Measures:
- Long pauses (> threshold)
- Average pause duration
- Speech rate (words/sec)

This evaluates HOW recall happens, not WHAT is recalled.
"""

from typing import Dict, List


class PauseEvaluator:
    def __init__(self, pause_threshold: float = 3.0):
        """
        Args:
            pause_threshold (float): seconds considered a cognitive pause
        """
        self.pause_threshold = pause_threshold

    # --------------------------------------------------
    def evaluate(self, segments: List[Dict]) -> Dict:
        """
        Args:
            segments: Whisper segments (each with start, end, text)

        Returns:
            Dict[str, float]
        """

        if not segments or len(segments) < 2:
            return self._empty()

        pauses = []
        total_words = 0

        start_time = segments[0]["start"]
        end_time = segments[-1]["end"]

        for i in range(1, len(segments)):
            gap = segments[i]["start"] - segments[i - 1]["end"]
            if gap >= self.pause_threshold:
                pauses.append(gap)

        for seg in segments:
            total_words += len(seg["text"].split())

        duration = max(end_time - start_time, 0.01)
        speech_rate = total_words / duration

        return {
            "pause_count": len(pauses),
            "avg_pause": round(sum(pauses) / len(pauses), 3) if pauses else 0.0,
            "max_pause": round(max(pauses), 3) if pauses else 0.0,
            "speech_rate": round(speech_rate, 3),
        }

    # --------------------------------------------------
    def _empty(self) -> Dict:
        return {
            "pause_count": 0,
            "avg_pause": 0.0,
            "max_pause": 0.0,
            "speech_rate": 0.0,
        }