"""
Fluency Statistics (Temporal Delivery)
--------------------------------------
Measures the mechanical and cognitive speed of speech generation.

Clinical Insight:
- Measures Words Per Minute (WPM)
- Low WPM → hesitation / word-finding issues
- High WPM → pressured speech
"""

from typing import Dict
from .thresholds import Thresholds


def compute_fluency(disfluency: Dict, duration_sec: float) -> Dict:

    # -----------------------------
    # Safety checks
    # -----------------------------
    if duration_sec <= 0:
        return _empty_response()

    total_words = disfluency.get("total_words", 0)

    if total_words == 0:
        return _empty_response()

    filler_count = disfluency.get("filler_count", 0)
    repetition_count = disfluency.get("repetition_count", 0)
    pause_count = disfluency.get("pause_count", 0)
    disfluency_score = disfluency.get("disfluency_score", 0.0)
    flags = []

    # -----------------------------
    # 1. WPM Calculation
    # -----------------------------
    minutes = duration_sec / 60.0
    wpm = total_words / minutes

    # -----------------------------
    # 2. Threshold Mapping
    # -----------------------------
    if wpm <= Thresholds.fluency["impaired"]:
        level = "impaired"
        speed = "slow"

    elif wpm <= Thresholds.fluency["borderline"]:
        level = "borderline"
        speed = "slow_normal"

    elif wpm <= Thresholds.fluency["fast"]:
        level = "healthy"
        speed = "normal"

    else:
        level = "borderline_fast"
        speed = "fast"

        # -----------------------------
        # 3. DISFLUENCY LOAD
        # -----------------------------
        if disfluency_score > 0.12:
            fluency_quality = "poor"
        elif disfluency_score > 0.06:
            fluency_quality = "moderate"
        else:
            fluency_quality = "good"

        # -----------------------------
        # 4. CLINICAL FLAGS
        # -----------------------------
        if wpm < 90:
            flags.append("slow_speech")

        if wpm > 180:
            flags.append("pressured_speech")

        if filler_count > 5:
            flags.append("excess_fillers")

        if repetition_count > 3:
            flags.append("repetition_hesitation")

        if pause_count > 5:
            flags.append("frequent_pauses")

    # -----------------------------
    # Output
    # -----------------------------
    return {
        "wpm": round(wpm, 2),
        "fluency_level": level,
        "speech_speed": speed,
        "total_words": total_words,
        "duration_sec": duration_sec,
        "is_reliable": True,

        "evidence": {
            "wpm": round(wpm, 2),
            "speed_category": speed,
            "filler_count": filler_count,
            "repetition_count": repetition_count,
            "pause_count": pause_count,
            "disfluency_score": disfluency_score,
            "flags": flags
        }
    }


def _empty_response():
    return {
        "wpm": 0.0,
        "fluency_level": "impaired",
        "speech_speed": "unknown",
        "total_words": 0,
        "duration_sec": 0,
        "is_reliable": False,

        "evidence": {}
    }