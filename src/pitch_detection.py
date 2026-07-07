# src/pitch_detection.py
"""
YIN pitch detection — replaces the previous zero-crossing estimate.

Zero-crossing counting is extremely noise-sensitive (harmonics and mic noise
add extra crossings, throwing off the estimate) and was previously papered
over with a random fallback that faked a plausible-looking number near the
expected target when detection failed. This module does real detection and
reports honestly when a chunk has no reliable pitch (e.g. silence, unvoiced
breath) via `None`, rather than fabricating a value.
"""
import numpy as np


def yin_pitch(chunk: np.ndarray, sample_rate: int, fmin: float = 60.0,
              fmax: float = 800.0, threshold: float = 0.15) -> float | None:
    """
    Estimate the fundamental frequency of a mono audio chunk using the YIN
    algorithm (de Cheveigne & Kawahara, 2002).

    Returns the estimated pitch in Hz, or None if no confident pitch is found
    (e.g. silence or noise-dominated chunk).
    """
    chunk = np.asarray(chunk, dtype=np.float64)
    chunk = chunk - np.mean(chunk)

    if np.max(np.abs(chunk)) < 1e-6:
        return None  # silence

    tau_max = int(sample_rate / fmin)
    tau_min = max(1, int(sample_rate / fmax))
    tau_max = min(tau_max, len(chunk) - 1)

    if tau_max <= tau_min:
        return None  # chunk too short for the requested frequency range

    # Step 1-2: difference function d(tau) = sum((x[t] - x[t+tau])^2)
    diff = np.zeros(tau_max + 1)
    for tau in range(1, tau_max + 1):
        delta = chunk[: len(chunk) - tau] - chunk[tau:]
        diff[tau] = np.dot(delta, delta)

    # Step 3: cumulative mean normalized difference function (CMNDF)
    cmndf = np.ones(tau_max + 1)
    running_sum = 0.0
    for tau in range(1, tau_max + 1):
        running_sum += diff[tau]
        cmndf[tau] = diff[tau] * tau / running_sum if running_sum > 0 else 1.0

    # Step 4: find the first local minimum below threshold in the valid range
    tau_est = None
    for tau in range(tau_min, tau_max):
        if cmndf[tau] < threshold and cmndf[tau] < cmndf[tau + 1]:
            tau_est = tau
            break

    if tau_est is None:
        # No dip below threshold — fall back to the global minimum, but only
        # trust it if it's a reasonably deep minimum (avoids reporting noise
        # as a confident pitch).
        candidate = int(np.argmin(cmndf[tau_min:tau_max])) + tau_min
        if cmndf[candidate] < 0.5:
            tau_est = candidate
        else:
            return None

    # Step 5: parabolic interpolation around tau_est for sub-sample accuracy
    if 0 < tau_est < tau_max:
        s0, s1, s2 = cmndf[tau_est - 1], cmndf[tau_est], cmndf[tau_est + 1]
        denom = (s0 - 2 * s1 + s2)
        if abs(denom) > 1e-12:
            shift = 0.5 * (s0 - s2) / denom
        else:
            shift = 0.0
        tau_refined = tau_est + shift
    else:
        tau_refined = float(tau_est)

    if tau_refined <= 0:
        return None

    return sample_rate / tau_refined


def analyze_pitch_trajectory(samples: np.ndarray, sample_rate: int, steps: int = 6,
                              fmin: float = 60.0, fmax: float = 800.0) -> list:
    """
    Splits a mono audio signal into `steps` equal chunks and estimates the
    pitch of each using YIN. Returns a list where each entry is either a
    float (Hz) or None if that chunk had no confident pitch (silence, noise,
    breath) — callers should handle None explicitly rather than assuming
    every chunk produced a usable value.
    """
    chunk_size = len(samples) // steps
    trajectory = []
    for i in range(steps):
        start = i * chunk_size
        end = start + chunk_size if i < steps - 1 else len(samples)
        chunk = samples[start:end]
        hz = yin_pitch(chunk, sample_rate, fmin=fmin, fmax=fmax)
        trajectory.append(round(float(hz), 1) if hz is not None else None)
    return trajectory