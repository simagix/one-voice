"""Phase 5: objective checks — whisper transcription of every listening clip.

The naturalness ratings themselves are subjective (§18, done by listening —
see notes.md). This script gathers the objective evidence:

1. Transcription (mlx-whisper, whisper-large-v3-turbo) of EVERY clip in
   audio/trimmed/, shown next to the expected text. Whisper caught every
   leak in Phase 3/4; here it doubles as the objective pronunciation /
   garbling check for the difficult-text lines (numbers, dates, acronyms,
   currency, abbreviations): a mispronounced or garbled item shows up as a
   wrong or missing word in the transcript.
2. A rough normalized text-similarity ratio per clip. Exact matches (the
   short plain lines) should be 1.00. Difficult-text lines legitimately
   score lower — the model SPELLS OUT "$1,247.50" as words, so the
   transcript differs from the written form while still being a CORRECT
   reading; the ratio is only a pointer, the transcript column is the check.

F0 analysis deliberately skipped: this phase measures naturalness, not
identity (Phase 4 covered identity).

Usage:
    .venv/bin/python experiments/naturalness/check_clips.py
"""

import difflib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# NOTE: tone dir goes at sys.path[0] so `from trim_clips import normalize`
# resolves to experiments/tone/trim_clips.py (Phase 3 helper), not this
# directory's same-named trim_clips.py. This script's own directory is
# already on sys.path (script dir), so `import clips` still works.
sys.path.insert(0, str(HERE.parent / "tone"))
from trim_clips import normalize  # noqa: E402  (Phase 3 helper)

from clips import CLIPS, listening_name  # noqa: E402

TRIMMED_DIR = HERE / "audio" / "trimmed"
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"


def main() -> None:
    import mlx_whisper  # lazy: keeps startup fast
    import wave

    lines = [
        "# Phase 5 — objective checks (whisper transcription of every clip)\n",
        "`Similarity` is a rough normalized-text ratio: 1.00 = transcript "
        "matches the written text word-for-word. Difficult-text lines "
        "legitimately score lower (the model spells numbers/currency out "
        "in words) — read the transcript column to judge the actual "
        "pronunciation.\n",
        "| Clip | Dur (s) | Similarity | Expected text | Transcript |",
        "| --- | ---: | ---: | --- | --- |",
    ]

    for clip in CLIPS:
        name = listening_name(clip)
        path = TRIMMED_DIR / f"{name}.wav"
        if not path.exists():
            print(f"{name}: missing, skipped", flush=True)
            continue
        with wave.open(str(path)) as w:
            dur = w.getnframes() / w.getframerate()
        transcript = mlx_whisper.transcribe(
            str(path), path_or_hf_repo=WHISPER_MODEL
        )["text"].strip()
        # autojunk=False: difflib's heuristic junk-treats frequent characters
        # in sequences >200 elements, which collapses the ratio for long
        # sentences (long2 read almost perfectly yet scored 0.31).
        ratio = difflib.SequenceMatcher(
            None, normalize(clip["text"]), normalize(transcript), autojunk=False
        ).ratio()
        flag = "  <- CHECK" if ratio < 0.90 else ""
        print(
            f"{name:10s} {dur:5.1f}s  sim {ratio:.2f}{flag}"
            f"\n    expected:   {clip['text']}"
            f"\n    transcript: {transcript}\n",
            flush=True,
        )
        lines.append(
            f"| {name} | {dur:.1f} | {ratio:.2f} | {clip['text']} | {transcript} |"
        )

    (HERE / "analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote analysis.md")


if __name__ == "__main__":
    main()
