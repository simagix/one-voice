"""Phase 3 experiments: tone and expression control with Qwen3-TTS (MLX).

The Qwen3-TTS *Base* model has no separate style/instruct input (that only
exists for the CustomVoice/VoiceDesign variants), so tone is embedded in the
text itself. Three approaches from DEVELOPMENT.md section 10 are compared:

  A) simple tag prefix:            "[happy] Thank you for calling."
  B) natural-language instruction: "Speak in a calm, professional manner. ..."
  C) detailed performance direction (multi-aspect, still single line)

Note: mlx-audio splits the text on newlines and generates each line as a
separate audio segment, so tags/instructions are kept on the same line as
the text.

Usage:
    .venv/bin/python experiments/tone/run_experiments.py [--only base,a,b,c]
"""

import argparse
import time
from pathlib import Path

from mlx_audio.tts.generate import generate_audio

MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit"

HERE = Path(__file__).resolve().parent
AUDIO_DIR = HERE / "audio"
REF_WAV = HERE.parent.parent / "voices" / "simone" / "reference.wav"
REF_TEXT = (HERE.parent.parent / "voices" / "simone" / "reference.txt").read_text().strip()

# Fixed test sentences, shared across all tone approaches for comparability.
S1_THANKS = "Thank you for calling. How may I help you today?"
S2_PLAN = "Well, that certainly went according to plan."
S3_LISTEN = "I need you to listen to me."

# (name, group, text). Names sort into groups: base_ / a_tag_ / b_nl_ / c_detail_.
EXPERIMENTS = [
    # Baseline: no tone direction, for A/B comparison.
    ("base_s1_thanks", "base", S1_THANKS),
    ("base_s2_plan", "base", S2_PLAN),
    ("base_s3_listen", "base", S3_LISTEN),
    # Experiment A: simple tag prefix (DEVELOPMENT.md section 10).
    ("a_tag_happy_s1", "a", f"[happy] {S1_THANKS}"),
    ("a_tag_sad_s1", "a", f"[sad] {S1_THANKS}"),
    ("a_tag_angry_s1", "a", f"[angry] {S1_THANKS}"),
    ("a_tag_calm_s1", "a", f"[calm] {S1_THANKS}"),
    ("a_tag_excited_s1", "a", f"[excited] {S1_THANKS}"),
    ("a_tag_sarcastic_s1", "a", f"[sarcastic] {S1_THANKS}"),
    ("a_tag_deadpan_s1", "a", f"[deadpan] {S1_THANKS}"),
    ("a_tag_sarcastic_s2", "a", f"[sarcastic] {S2_PLAN}"),
    # Experiment B: natural-language instruction (DEVELOPMENT.md section 10).
    ("b_nl_calm_s1", "b", f"Speak in a calm, professional and reassuring manner. {S1_THANKS}"),
    ("b_nl_friendly_s1", "b", f"Sound warm, friendly and welcoming. {S1_THANKS}"),
    ("b_nl_excited_s1", "b", f"Sound genuinely excited and enthusiastic. {S1_THANKS}"),
    ("b_nl_sad_s1", "b", f"Sound sad and sympathetic, like you are apologising. {S1_THANKS}"),
    ("b_nl_sarcasm_s2", "b", f"Deliver the sentence with dry, understated sarcasm. {S2_PLAN}"),
    ("b_nl_frustrated_s3", "b", f"Sound frustrated and impatient, but remain controlled. {S3_LISTEN}"),
    # Experiment C: detailed multi-aspect performance direction (section 10).
    (
        "c_detail_frustration_s3",
        "c",
        "Deliver this with controlled frustration. Speak firmly and slightly "
        f"faster. Emphasize 'need' and 'listen'. Do not shout. {S3_LISTEN}",
    ),
    (
        "c_detail_reassurance_s1",
        "c",
        "Deliver this calmly and slowly. Emphasize 'help'. Pause briefly "
        f"before the question. Do not rush. {S1_THANKS}",
    ),
    (
        "c_detail_sarcasm_s2",
        "c",
        "Deliver this with dry, deadpan sarcasm. Speak slowly and flatly. "
        f"Emphasize 'certainly'. Do not smile. {S2_PLAN}",
    ),
]


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
        help="comma-separated groups to run (base,a,b,c); default: all",
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
