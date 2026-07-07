# src/live_guru.py
import wave
import io
import numpy as np
from pitch_detection import analyze_pitch_trajectory


class VocalPitchTrackingSkill:
    """Custom Agent computational skill executing pitch tracking via the YIN algorithm."""

    def __init__(self):
        self.name = "vocal_pitch_tracker"
        self.description = "Parses raw binary audio buffers to track fundamental pitch timelines using YIN."

    def execute(self, audio_bytes: bytes, focus_mode: str, num_notes: int = 6) -> list:
        """
        Returns a list of per-note pitch estimates in Hz, one per note in
        the target sequence (num_notes). Entries are `None` where no
        confident pitch was found (silence, breath, noise) rather than a
        fabricated value.

        fmin=100 avoids a common false-positive: 60 Hz US mains hum being
        picked up as a "detected pitch" during a quiet moment in the take.
        """
        try:
            with wave.open(io.BytesIO(audio_bytes), 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                data = wav_file.readframes(n_frames)
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                return analyze_pitch_trajectory(
                    samples, sample_rate, steps=num_notes, fmin=100.0, fmax=650.0
                )
        except Exception:
            return [None] * num_notes