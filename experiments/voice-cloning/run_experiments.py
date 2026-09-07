"""Phase 1 & 2 experiments: basic TTS and voice cloning with Qwen3-TTS (MLX).

Usage:
    .venv/bin/python experiments/voice-cloning/run_experiments.py
"""

import time
from pathlib import Path

from mlx_audio.tts.generate import generate_audio

MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit"

HERE = Path(__file__).resolve().parent
AUDIO_DIR = HERE / "audio"
REF_WAV = HERE.parent.parent / "voices" / "simone" / "reference.wav"
REF_TEXT = (HERE.parent.parent / "voices" / "simone" / "reference.txt").read_text().strip()


def run(name: str, **kwargs) -> None:
    print(f"--- generating {name} ...", flush=True)
    start = time.time()
    generate_audio(
        output_path=str(AUDIO_DIR),
        file_prefix=name,
        audio_format="wav",
        verbose=False,
        **kwargs,
    )
    print(f"--- {name} done in {time.time() - start:.1f}s", flush=True)


if __name__ == "__main__":
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # Phase 1: basic TTS, no speaker / no reference.
    run(
        "phase1_basic_thanks",
        text="Thank you for calling. How may I help you today?",
        model=MODEL,
        voice=None,
    )

    # Phase 2: clone the Simone reference voice (ICL: ref_audio + ref_text).
    run(
        "phase2_simone_thanks",
        text="Thank you for calling. How may I help you today?",
        model=MODEL,
        ref_audio=str(REF_WAV),
        ref_text=REF_TEXT,
    )
    run(
        "phase2_simone_problem",
        text="I'm afraid we have a problem. Let me look into that for you right away.",
        model=MODEL,
        ref_audio=str(REF_WAV),
        ref_text=REF_TEXT,
    )
