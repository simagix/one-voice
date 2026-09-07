"""Phase 6 shared plan — voices, sentences, clips — single source of truth.

Imported by run_clips.py (generation), build_set.py (trim + listening page)
and check_voices.py (whisper objective checks) so every clip name, expected
text and reference path lives in one place (same idea as the Phase 5
clips.py module).

Import note (the sys.path gotcha): phase6 module names are unique — there is
no clips.py / trim_clips.py in this directory — so `from clips import ...`
and `from trim_clips import ...` unambiguously resolve to the Phase 5 /
Phase 3 helpers in the sibling experiment directories.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent

# Phase 5 evaluation set (single source of truth for the comparison clips).
sys.path.insert(0, str(HERE.parent / "naturalness"))
from clips import CLIPS  # noqa: E402

MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit"

# The two new voices alongside Simone — Bob Neufeld (male, US narrator) and
# Ruth Golding (female, British narrator), both public-domain LibriVox reads.
COMPARISON_VOICES = ["neufeld", "golding"]

# One new voice gets the Phase 4 tone sanity check: neufeld — the most
# distant from Simone (gender + F0), i.e. the strongest test that the §11
# voice/tone independence finding generalizes beyond Simone.
TONE_VOICE = "neufeld"

# Phase 4 sentences, unchanged for comparability.
SENTENCES = {
    "s1": "Thank you for calling. How may I help you today?",
    "s2": "Well, that certainly went according to plan.",
    "s3": "I need you to listen to me.",
}

# Tags validated in Phase 3/4; sarcasm (NL fallback) deliberately excluded —
# keep the sanity-check matrix small.
TAGS = ["calm", "happy", "sad"]


def ref_paths(voice: str) -> tuple[Path, str]:
    """Return (reference.wav path, sidecar transcript) for a voice."""
    d = REPO / "voices" / voice
    return d / "reference.wav", (d / "reference.txt").read_text().strip()


def comparison_clips() -> list[tuple[str, str, str, str, str]]:
    """(name, text, category, phase5_name, voice) — every Phase 5 clip PLAIN.

    Plain means no tone prompt: the voice comparison must be apples-to-apples
    with Simone's Phase 5 numbers on the 12 plain clips; the three
    emotionally-worded lines are also generated plain here (Simone's Phase 5
    versions were tagged+trimmed — noted in the rating tables).
    """
    out = []
    for voice in COMPARISON_VOICES:
        for clip in CLIPS:
            out.append(
                (
                    f"{voice}_{clip['name']}",
                    clip["text"],
                    clip["category"],
                    clip["name"],
                    voice,
                )
            )
    return out


def tone_clips() -> list[tuple[str, str, str, bool, str]]:
    """(name, gen_text, sentence, is_tagged, sentence_key) for TONE_VOICE."""
    out = []
    for key, sentence in SENTENCES.items():
        out.append((f"{TONE_VOICE}_tone_base_{key}", sentence,
                    sentence, False, key))
        for tone in TAGS:
            out.append(
                (
                    f"{TONE_VOICE}_tone_tag_{tone}_{key}",
                    f"[{tone}] {sentence}",
                    sentence,
                    True,
                    key,
                )
            )
    return out