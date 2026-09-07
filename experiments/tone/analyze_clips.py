"""Objective checks on the Phase 3 tone-experiment clips.

We cannot listen programmatically, so this script gathers evidence that
supports the subjective (listening) evaluation from DEVELOPMENT.md section 18:

1. Transcription (mlx-whisper, same model used for the reference transcript):
   - confirms whether the tone instruction text is spoken aloud,
   - catches garbled/truncated generations.
2. Pitch (F0) statistics via numpy autocorrelation: median F0 per clip,
   compared against the Simone reference and the matching baseline clip as a
   rough identity-drift proxy (in semitones). This is a crude proxy only —
   the listening evaluation in notes.md remains the ground truth.

Usage:
    .venv/bin/python experiments/tone/analyze_clips.py
"""

import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
AUDIO_DIR = HERE / "audio"
REPO = HERE.parent.parent
REF_WAV = REPO / "voices" / "simone" / "reference.wav"
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"

# First baseline clip for each test sentence (identity anchor per sentence).
ANCHORS = {
    "s1": "base_s1_thanks_000.wav",
    "s2": "base_s2_plan_000.wav",
    "s3": "base_s3_listen_000.wav",
}


def load_wav(path: Path) -> tuple[int, np.ndarray]:
    with wave.open(str(path)) as w:
        assert w.getnchannels() == 1 and w.getsampwidth() == 2
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return sr, x.astype(np.float32) / 32768.0


def f0_track(x: np.ndarray, sr: int, fmin: float = 60, fmax: float = 400) -> np.ndarray:
    """Voiced-frame F0 estimates via frame-wise autocorrelation."""
    fl = int(0.040 * sr)
    hp = int(0.010 * sr)
    lo, hi = int(sr / fmax), int(sr / fmin)
    rms_all = float(np.sqrt(np.mean(x**2)))
    f0s = []
    for start in range(0, len(x) - fl, hp):
        fr = x[start : start + fl]
        if np.sqrt(np.mean(fr**2)) < 0.35 * rms_all:
            continue  # skip silence / unvoiced
        fr = fr - fr.mean()
        ac = np.correlate(fr, fr, "full")[fl - 1 :]
        if ac[0] <= 0:
            continue
        ac /= ac[0]
        lag = int(np.argmax(ac[lo:hi])) + lo
        if ac[lag] < 0.30:
            continue  # weak periodicity -> unvoiced
        f0s.append(sr / lag)
    return np.array(f0s)


def pitch_summary(x: np.ndarray, sr: int) -> tuple[float, float]:
    f0s = f0_track(x, sr)
    if len(f0s) == 0:
        return float("nan"), float("nan")
    return float(np.median(f0s)), float(np.percentile(f0s, 75) - np.percentile(f0s, 25))


def main() -> None:
    import mlx_whisper  # lazy: keeps startup fast

    ref_sr, ref_x = load_wav(REF_WAV)
    ref_med, ref_iqr = pitch_summary(ref_x, ref_sr)
    print(f"reference (Simone): median F0 = {ref_med:.0f} Hz, IQR = {ref_iqr:.0f} Hz\n")

    anchors: dict[str, float] = {}
    lines = ["# Tone experiment — objective clip analysis\n",
             "F0 medians are a rough identity proxy; final judgement is by ear (notes.md).\n",
             "| Clip | Dur (s) | Median F0 (Hz) | vs ref (st) | vs anchor (st) | Transcript |",
             "| --- | ---: | ---: | ---: | ---: | --- |"]

    for path in sorted(AUDIO_DIR.glob("*.wav")):
        sr, x = load_wav(path)
        med, _ = pitch_summary(x, sr)
        st_ref = 12 * np.log2(med / ref_med) if med == med else float("nan")

        anchor_name = next((ANCHORS[k] for k, v in ANCHORS.items() if path.name != v and k in path.name), None)
        if anchor_name:
            a_sr, a_x = load_wav(AUDIO_DIR / anchor_name)
            a_med, _ = pitch_summary(a_x, a_sr)
            anchors[path.name] = a_med
            st_anchor = 12 * np.log2(med / a_med) if med == med else float("nan")
        else:
            st_anchor = 0.0  # the anchor itself

        text = mlx_whisper.transcribe(str(path), path_or_hf_repo=WHISPER_MODEL)["text"].strip()
        dur = len(x) / sr
        print(f"{path.stem:28s} {dur:5.1f}s  {med:6.1f} Hz  {st_ref:+5.2f} st vs ref"
              f"  {st_anchor:+5.2f} st vs anchor\n    transcript: {text}\n", flush=True)
        lines.append(f"| {path.stem} | {dur:.1f} | {med:.0f} | {st_ref:+.2f} | {st_anchor:+.2f} | {text} |")

    (HERE / "analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote analysis.md")


if __name__ == "__main__":
    main()
