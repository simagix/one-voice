"""Phase 4 experiments: voice + tone independence (DEVELOPMENT.md section 11).

Phase 3 established the working pattern for tone control on the Qwen3-TTS
Base model: the style text is spoken aloud (in-band only), but the leaked
audio is a leading segment that can be trimmed with whisper word timestamps.
Tags are the preferred prompt format; NL direction is the fallback when a
tag under-delivers (sarcasm).

This phase asks the §11 question: with the SAME reference voice (Simone) and
the SAME sentences, do the different tones still sound like ONE person
performing differently — not like different speakers? Each sentence is
therefore generated once with NO tone direction (baseline = identity anchor)
and once per tone, and every tone clip is compared against its own
sentence's baseline.

Note: mlx-audio splits the text on newlines and generates each line as a
separate audio segment, so tags/instructions are kept on the same line as
the text.

Usage:
    .venv/bin/python experiments/phase4/run_experiments.py [--only base,tones]
"""

import argparse
import time
from pathlib import Path

from mlx_audio.tts.generate import generate_audio

MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit"

HERE = Path(__file__).resolve().parent
AUDIO_DIR = HERE / "audio" / "raw"
REPO = HERE.parent.parent
REF_WAV = REPO / "voices" / "simone" / "reference.wav"
REF_TEXT = (REPO / "voices" / "simone" / "reference.txt").read_text().strip()

# Fixed test sentences, identical to Phase 3 for comparability.
S1_THANKS = "Thank you for calling. How may I help you today?"
S2_PLAN = "Well, that certainly went according to plan."
S3_LISTEN = "I need you to listen to me."
SENTENCES = {"s1": S1_THANKS, "s2": S2_PLAN, "s3": S3_LISTEN}

# Tones under test: tags preferred (Phase 3 verdict); sarcasm uses the NL
# instruction because the [sarcastic] tag under-delivered in Phase 3.
TAG_TONES = ["calm", "happy", "sad", "angry", "excited"]
NL_PROMPTS = {"sarcastic": "Deliver the sentence with dry, understated sarcasm."}

# (name, group, text). Groups: base (no-tone baseline) / tone.
EXPERIMENTS = []
for key, sentence in SENTENCES.items():
    EXPERIMENTS.append((f"base_{key}", "base", sentence))
for key, sentence in SENTENCES.items():
    for tone in TAG_TONES:
        EXPERIMENTS.append((f"tag_{tone}_{key}", "tone", f"[{tone}] {sentence}"))
    EXPERIMENTS.append(
        (f"nl_sarcastic_{key}", "tone", f"{NL_PROMPTS['sarcastic']} {sentence}")
    )


def run(name: str, text: str) -> None:
    print(f"--- generating {name} ...", flush=True)
    start = time.time()
    generate_audio(
        text=text,
        model=MODEL,
        ref_audio=str(REF_WAV),
        ref_text=REF_TEXT,
        output_path=str(AUDIO_DIR),
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
        help="comma-separated groups to run (base,tone); default: all",
    )
    args = parser.parse_args()

    groups = {g.strip() for g in args.only.split(",") if g.strip()}
    selected = [
        (name, text)
        for name, group, text in EXPERIMENTS
        if not groups or group in groups
    ]
    if not selected:
        parser.error(f"no experiments match --only {args.only!r}")

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    for name, text in selected:
        run(name, text)


if __name__ == "__main__":
    main()
