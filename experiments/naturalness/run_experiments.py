"""Phase 5 experiments: naturalness evaluation set (DEVELOPMENT.md section 12).

Generates the repeatable §12 evaluation set with the Simone clone
(voices/simone/reference.wav + sidecar transcript) on the same model as
Phases 2–4 (mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit), ~5 s per clip.

Plain clone generations by default — §5 naturalness is about the voice
itself, and tone control was already validated in Phase 4. The only tagged
clips are the inherently-emotional lines where flat delivery would fail the
test ("That's fantastic news!"): they use the Phase-4-validated tags, and
their leaked prompt audio is removed afterwards by trim_clips.py (the
Phase 3/4 prompt + trim pattern). The clip table lives in clips.py so the
expected text exists in exactly one place.

Usage:
    .venv/bin/python experiments/naturalness/run_experiments.py [--only GROUP]
"""

import argparse
import sys
import time
from pathlib import Path

from mlx_audio.tts.generate import generate_audio

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from clips import CLIPS, CATEGORY_ORDER, generate_text  # noqa: E402

MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit"

RAW_DIR = HERE / "audio" / "raw"
REPO = HERE.parent.parent
REF_WAV = REPO / "voices" / "simone" / "reference.wav"
REF_TEXT = (REPO / "voices" / "simone" / "reference.txt").read_text().strip()


def run(name: str, text: str) -> None:
    print(f"--- generating {name} ...", flush=True)
    start = time.time()
    generate_audio(
        text=text,
        model=MODEL,
        ref_audio=str(REF_WAV),
        ref_text=REF_TEXT,
        output_path=str(RAW_DIR),
        file_prefix=name,
        audio_format="wav",
        verbose=False,
    )
    print(f"--- {name} done in {time.time() - start:.1f}s", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        default="",
        help="comma-separated categories to run, e.g. 'Questions,Difficult "
        "text'; default: all",
    )
    args = parser.parse_args()

    groups = {g.strip() for g in args.only.split(",") if g.strip()}
    unknown = groups - set(CATEGORY_ORDER)
    if unknown:
        parser.error(f"unknown categories: {sorted(unknown)}")

    selected = [
        (c["name"], generate_text(c))
        for c in CLIPS
        if not groups or c["category"] in groups
    ]
    if not selected:
        parser.error("no clips selected")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name, text in selected:
        run(name, text)
    print(f"done: {len(selected)} clip(s) in {RAW_DIR}")


if __name__ == "__main__":
    main()
