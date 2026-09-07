"""Phase 8 side-experiment helper: median-F0 comparison of the instruct= probe
vs a plain clone of the same sentence (rough check that the instruct channel
actually changes delivery; final judgement is by ear). numpy-only autocorr F0.
"""

import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent / "audio"


def f0_median(path: Path, fmin: float = 60.0, fmax: float = 400.0):
    with wave.open(str(path)) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)
    x /= np.max(np.abs(x)) + 1e-9
    frame, hop = int(0.04 * sr), int(0.01 * sr)
    lag_min, lag_max = int(sr / fmax), int(sr / fmin)
    f0s = []
    for i in range(0, len(x) - frame, hop):
        seg = x[i : i + frame] * np.hanning(frame)
        if np.sqrt(np.mean(seg**2)) < 0.02:  # skip silence
            continue
        ac = np.correlate(seg, seg, mode="full")[frame - 1 :]
        if ac[0] <= 0:
            continue
        ac /= ac[0]
        window = ac[lag_min:lag_max]
        k = int(np.argmax(window))
        if window[k] > 0.45:  # voiced
            f0s.append(sr / (lag_min + k))
    return (float(np.median(f0s)) if f0s else float("nan")), len(f0s)


def main() -> None:
    f0_a, n_a = f0_median(HERE / "instruct_probe.wav")
    f0_b, n_b = f0_median(HERE / "plain_probe.wav")
    print(f"instruct(friendly): median F0 = {f0_a:.1f} Hz  ({n_a} voiced frames)")
    print(f"plain clone:        median F0 = {f0_b:.1f} Hz  ({n_b} voiced frames)")
    if f0_a == f0_a and f0_b == f0_b and f0_b > 0:
        print(f"difference: {12 * np.log2(f0_a / f0_b):+.2f} semitones")
    else:
        print("insufficient voiced frames for a comparison")


if __name__ == "__main__":
    main()
