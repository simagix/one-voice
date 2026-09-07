"""Phase 6 generation: comparison clips (both voices) + tone sanity check.

Reuses the Phase 5 §12 evaluation set (experiments/naturalness/clips.py —
the single source of truth) so the new voices are directly comparable to
Simone's Phase 5 numbers. Every comparison clip is generated PLAIN (no tone
prompt), including the three emotionally-worded lines (Simone's Phase 5
versions were tagged+trimmed; the plain comparison is the apples-to-apples
baseline and the difference is noted in notes.md).

On ONE voice (neufeld: male US — the most distant from Simone, hence the
strongest test of whether the §11 voice/tone independence finding
generalizes) also generates the Phase 4 tone sanity check: sentences
S1/S2/S3 at baseline (no tone) + the 3 tags validated in Phase 3/4
([calm], [happy], [sad]). Tag clips carry the spoken style-prompt leak;
build_set.py removes it with the Phase 3 whisper-timestamp trim (the exact
Phase 4 pattern).

Same model and reference pipeline as Phases 2–5.

Usage:
    .venv/bin/python experiments/phase6/run_clips.py [--voice neufeld,golding]
        [--only comparison,tone]
"""

import argparse
import sys
import time
from pathlib import Path

from mlx_audio.tts.generate import generate_audio

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from setup_plan import (  # noqa: E402
    COMPARISON_VOICES,
    MODEL,
    TONE_VOICE,
    comparison_clips,
    ref_paths,
    tone_clips,
)

RAW_DIR = HERE / "audio" / "raw"


def run(name: str, text: str, voice: str) -> None:
    print(f"--- [{voice}] {name}: {text[:60]!r}", flush=True)
    start = time.time()
    ref_wav, ref_text = ref_paths(voice)
    generate_audio(
        text=text,
        model=MODEL,
        ref_audio=str(ref_wav),
        ref_text=ref_text,
        output_path=str(RAW_DIR),
        file_prefix=name,
        audio_format="wav",
        verbose=False,
    )
    print(f"--- {name} done in {time.time() - start:.1f}s", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--voices",
        default=",".join(COMPARISON_VOICES),
        help="comma-separated comparison voices (default: both)",
    )
    parser.add_argument(
        "--only",
        default="",
        help="comma-separated groups (comparison,tone); default: all",
    )
    args = parser.parse_args()

    voices = {v.strip() for v in args.voices.split(",") if v.strip()}
    unknown = voices - set(COMPARISON_VOICES)
    if unknown:
        parser.error(f"unknown voices: {sorted(unknown)}")
    groups = {g.strip() for g in args.only.split(",") if g.strip()}
    bad = groups - {"comparison", "tone"}
    if bad:
        parser.error(f"unknown groups: {sorted(bad)}")
    do_compare = not groups or "comparison" in groups
    do_tone = not groups or "tone" in groups

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    plan = []
    if do_compare:
        plan += [(n, t, v) for n, t, _c, _p, v in comparison_clips()
                 if v in voices]
    if do_tone:
        plan += [(n, t, TONE_VOICE) for n, t, _s, _tagged, _k in tone_clips()]
    print(f"generating {len(plan)} clip(s) into {RAW_DIR}", flush=True)
    for name, text, voice in plan:
        run(name, text, voice)
    print(f"done: {len(plan)} clip(s)")


if __name__ == "__main__":
    main()