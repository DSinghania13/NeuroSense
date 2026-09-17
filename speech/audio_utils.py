"""
Audio Utilities
---------------
Common audio helper functions used across tests.

Designed to:
- Normalize audio for Whisper
- Validate duration
- Convert audio formats if needed
"""

import os
from typing import Tuple

import soundfile as sf
import numpy as np
from pydub import AudioSegment


def ensure_wav(
    audio_path: str,
    target_sr: int = 16000
) -> str:
    """
    Convert audio to WAV format if needed.
    """
    if audio_path.lower().endswith(".wav"):
        return audio_path

    wav_path = audio_path.rsplit(".", 1)[0] + ".wav"

    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_frame_rate(target_sr).set_channels(1)
    audio.export(wav_path, format="wav")

    return wav_path


def load_audio(
    audio_path: str,
    target_sr: int = 16000
) -> Tuple[np.ndarray, int]:
    """
    Load audio file and resample if necessary.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    audio_path = ensure_wav(audio_path)

    audio, sr = sf.read(audio_path)

    # Convert stereo to mono
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    return audio, sr


def get_audio_duration(
    audio_path: str
) -> float:
    """
    Get duration of audio file in seconds.
    """
    audio_path = ensure_wav(audio_path)
    info = sf.info(audio_path)
    return info.duration


def validate_audio_duration(
    audio_path: str,
    min_seconds: float = 2.0,
    max_seconds: float = 300.0
) -> None:
    """
    Validate audio duration for cognitive tests.
    """
    audio_path = ensure_wav(audio_path)
    duration = sf.info(audio_path).duration

    if duration < min_seconds:
        raise ValueError(
            f"Audio too short ({duration:.2f}s). "
            f"Minimum required is {min_seconds}s."
        )

    if duration > max_seconds:
        raise ValueError(
            f"Audio too long ({duration:.2f}s). "
            f"Maximum allowed is {max_seconds}s."
        )