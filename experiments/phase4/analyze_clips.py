"""Phase 4: objective checks on the trimmed tone clips.

Reuses the F0/pitch utilities from Phase 3 (experiments/tone/analyze_clips.py).
Cannot listen programmatically, so this gathers evidence for the §11 question
(same person performing differently?) and the §18 listening evaluation in
notes.md:

1. Transcription (mlx-whisper) of every TRIMMED clip — verifies the leaked
   tag/instruction is gone and catches garbled/truncated generations.
2. Median F0 per clip vs the Simone reference, and — the Phase 4 metric —
   vs the NO-TONE BASELINE of the same sentence (identity-drift proxy, in
   semitones). Crude proxy only; listening remains the ground truth.

Usage:
    .venv/bin/python experiments/phase4/analyze_clips.py
"""

import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TRIMMED_DIR = HERE / "audio" / "trimmed"
REPO = HERE.parent.parent
REF_WAV = REPO / "voices" / "simone" / "reference.wav"
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"

# Reuse the Phase 3 pitch utilities instead of reimplementing them.
sys.path.insert(0, str(HERE.parent / "tone"))
from analyze_clips import load_wav, pitch_summary  # noqa: E402

TONE_ORDER = [
    "tag_calm", "tag_happy", "tag_sad", "tag_angry", "tag_excited",
    "nl_sarcastic",
]


def main() -> None:
    import mlx_whisper  # lazy: keeps startup fast

    ref_sr, ref_x = load_wav(REF_WAV)
    ref_med, _ = pitch_summary(ref_x, ref_sr)
    print(f"reference (Simone): median F0 = {ref_med:.0f} Hz\n")

    # Per-sentence baseline F0 (identity anchor).
    anchors: dict[str, float] = {}
    for key in ("s1", "s2", "s3"):
        path = TRIMMED_DIR / f"base_{key}.wav"
        sr, x = load_wav(path)
        med, _ = pitch_summary(x, sr)
        anchors[key] = med
        print(f"baseline base_{key}: median F0 = {med:.0f} Hz")

    lines = ["# Phase 4 — objective clip analysis (trimmed clips)\n",
             "F0 medians are a rough identity proxy; the key column is "
             "`vs baseline` (same sentence, no tone) — the §11 identity-drift "
             "proxy. Final judgement is by ear (notes.md).\n",
             "| Clip | Dur (s) | Median F0 (Hz) | vs ref (st) | vs baseline (st) | Transcript |",
             "| --- | ---: | ---: | ---: | ---: | --- |"]

    for key in ("s1", "s2", "s3"):
        names = [f"base_{key}"] + [f"{p}_{key}_trim" for p in TONE_ORDER]
        for name in names:
            path = TRIMMED_DIR / f"{name}.wav"
            if not path.exists():
                print(f"{name}: missing, skipped", flush=True)
                continue
            sr, x = load_wav(path)
            med, _ = pitch_summary(x, sr)
            st_ref = 12 * np.log2(med / ref_med) if med == med else float("nan")
            st_base = 12 * np.log2(med / anchors[key]) if med == med else float("nan")
            text = mlx_whisper.transcribe(
                str(path), path_or_hf_repo=WHISPER_MODEL
            )["text"].strip()
            dur = len(x) / sr
            print(f"{name:26s} {dur:5.1f}s  {med:6.1f} Hz  {st_ref:+5.2f} st vs ref"
                  f"  {st_base:+5.2f} st vs base_{key}"
                  f"\n    transcript: {text}\n", flush=True)
            lines.append(
                f"| {name} | {dur:.1f} | {med:.0f} | {st_ref:+.2f} | {st_base:+.2f} | {text} |"
            )

    (HERE / "analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote analysis.md")


if __name__ == "__main__":
    main()
