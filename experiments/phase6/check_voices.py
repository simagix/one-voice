"""Phase 6: objective checks — whisper transcription of every listening clip.

Same approach as the Phase 5 check (whisper-large-v3-turbo on every clip in
audio/trimmed/, transcript vs expected text with a normalized similarity
ratio) extended to the two new voices and the neufeld tone sanity check.
The transcript column is the pronunciation/garbling check; the similarity
ratio is only a pointer (difficult-text lines legitimately score lower
because the model spells out numbers and currency in words).

F0 analysis deliberately skipped — this phase measures cross-voice identity
and naturalness, not pitch contours; Phase 4 already covered F0, and
nothing sounded off in the smoke test.

Usage:
    .venv/bin/python experiments/phase6/check_voices.py
"""

import difflib
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tone"))
from trim_clips import normalize  # noqa: E402  (Phase 3 helper)

sys.path.insert(0, str(HERE))
from setup_plan import comparison_clips, tone_clips  # noqa: E402

TRIMMED_DIR = HERE / "audio" / "trimmed"
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"


def listening_inventory() -> list[tuple[str, str]]:
    """(clip basename, expected text) for every file in audio/trimmed/."""
    items = [(n, t) for n, t, _c, _p5, _v in comparison_clips()]
    for name, _gen, sentence, tagged, _key in tone_clips():
        items.append((name, sentence) if not tagged else (f"{name}_trim", sentence))
    return items


def main() -> None:
    import mlx_whisper  # lazy: keeps startup fast

    lines = [
        "# Phase 6 — objective checks (whisper transcription of every clip)\n",
        "`Similarity` is a rough normalized-text ratio: 1.00 = the transcript "
        "matches the written text word-for-word. Difficult-text lines "
        "legitimately score lower (the model spells numbers/currency out in "
        "words) — read the transcript column to judge the pronunciation. "
        "Tone-tagged clips are the neufeld sanity check, leak-trimmed.\n",
        "| Clip | Dur (s) | Similarity | Expected text | Transcript |",
        "| --- | ---: | ---: | --- | --- |",
    ]

    for name, expected in listening_inventory():
        path = TRIMMED_DIR / f"{name}.wav"
        if not path.exists():
            print(f"{name}: missing, skipped", flush=True)
            continue
        with wave.open(str(path)) as w:
            dur = w.getnframes() / w.getframerate()
        transcript = mlx_whisper.transcribe(
            str(path), path_or_hf_repo=WHISPER_MODEL
        )["text"].strip()
        ratio = difflib.SequenceMatcher(
            None, normalize(expected), normalize(transcript), autojunk=False
        ).ratio()
        flag = "  <- CHECK" if ratio < 0.90 else ""
        print(
            f"{name:34s} {dur:5.1f}s  sim {ratio:.2f}{flag}"
            f"\n    expected:   {expected}"
            f"\n    transcript: {transcript}\n",
            flush=True,
        )
        lines.append(
            f"| {name} | {dur:.1f} | {ratio:.2f} | {expected} | {transcript} |"
        )

    (HERE / "analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote analysis.md")


if __name__ == "__main__":
    main()