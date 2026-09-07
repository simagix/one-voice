"""Phase 4: trim the leaked style text off the tone clips (prompt + trim).

Reuses the trim machinery proven in Phase 3 (experiments/tone/trim_clips.py):
mlx-whisper word timestamps locate the boundary where the target sentence
starts; everything before it is the spoken tag/instruction and is cut off
(-50 ms pad).

Baselines have no tone prompt and no leak, so they are copied unchanged into
audio/trimmed/ — that directory then holds the complete listening set, and
listen.html (generated here) presents each sentence as: baseline player
first, then the tone clips, ready for rating against the baseline.

Usage:
    .venv/bin/python experiments/phase4/trim_clips.py
"""

import shutil
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RAW_DIR = HERE / "audio" / "raw"
TRIMMED_DIR = HERE / "audio" / "trimmed"
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"

# Import the Phase 3 trim helpers instead of reimplementing them.
sys.path.insert(0, str(HERE.parent / "tone"))
from trim_clips import find_cut, trim_wav  # noqa: E402

TARGETS = {
    "s1": "Thank you for calling. How may I help you today?",
    "s2": "Well, that certainly went according to plan.",
    "s3": "I need you to listen to me.",
}
TONE_LABELS = {
    "tag_calm": "[calm] tag",
    "tag_happy": "[happy] tag",
    "tag_sad": "[sad] tag",
    "tag_angry": "[angry] tag",
    "tag_excited": "[excited] tag",
    "nl_sarcastic": "NL sarcasm direction",
}


def main() -> None:
    import mlx_whisper  # lazy: keeps startup fast

    rows = ["# Phase 4 — trimmed clips (leaked style text removed)\n",
            "Tone clips cut with the Phase 3 whisper-timestamp method; baselines "
            "copied untrimmed (no leak). Listen via listen.html.\n",
            "| Clip | Cut at (s) | Match | Trimmed (s) | Transcript of trimmed clip |",
            "| --- | ---: | ---: | ---: | --- |"]
    TRIMMED_DIR.mkdir(parents=True, exist_ok=True)

    for path in sorted(RAW_DIR.glob("*_000.wav")):
        stem = path.stem.replace("_000", "")
        out = TRIMMED_DIR / f"{stem}_trim.wav"
        key = next((k for k in TARGETS if f"_{k}" in stem), None)
        if stem.startswith("base_"):
            # Baseline: no prompt, nothing to trim — copy through unchanged.
            shutil.copy2(path, TRIMMED_DIR / f"{stem}.wav")
            continue
        if key is None:
            continue
        result = mlx_whisper.transcribe(
            str(path), path_or_hf_repo=WHISPER_MODEL, word_timestamps=True
        )
        words = [w for seg in result["segments"] for w in seg.get("words", [])]
        if not words:
            print(f"{stem}: no word timestamps, skipped", flush=True)
            continue
        cut, ratio = find_cut(words, TARGETS[key])
        dur = trim_wav(path, cut, out)
        trimmed_text = mlx_whisper.transcribe(
            str(out), path_or_hf_repo=WHISPER_MODEL
        )["text"].strip()
        print(f"{out.stem:28s} cut {cut:5.2f}s  match {ratio:.2f}  -> {dur:4.1f}s"
              f"\n    transcript: {trimmed_text}\n", flush=True)
        rows.append(f"| {out.stem} | {cut:.2f} | {ratio:.2f} | {dur:.1f} | {trimmed_text} |")

    write_listen_page()
    (HERE / "trim_report.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("wrote trim_report.md and listen.html")


def write_listen_page() -> None:
    """Listening comparison: per sentence, baseline first, then each tone."""
    audio_rel = "audio/trimmed"
    parts = ["""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Phase 4 — voice + tone independence (listening)</title>
<style>
 body { font-family: -apple-system, sans-serif; max-width: 760px; margin: 2rem auto; }
 h2 { border-bottom: 1px solid #ccc; padding-bottom: .2rem; margin-top: 2.5rem; }
 .clip { margin: .8rem 0; }
 .clip label { display: block; font-weight: 600; margin-bottom: .2rem; }
 .baseline label { color: #666; }
 audio { width: 100%; }
 table { border-collapse: collapse; margin-top: 1rem; width: 100%; }
 th, td { border: 1px solid #bbb; padding: .35rem .5rem; text-align: left; }
 th { background: #f2f2f2; }
</style>
</head>
<body>
<h1>Phase 4 — voice + tone independence</h1>
<p>Same Simone reference, same sentence, several tones. For each sentence:
listen to the <b>baseline</b> (no tone direction) first, then each tone, and
rate the tone <b>against the baseline</b> (1–5, DEVELOPMENT.md §18): does it
still sound like the <b>same person</b> (Identity), is it natural
(Naturalness), does the tone come through (Expression), and does it match the
other tones of the same voice (Consistency)? Transfer ratings into
<code>notes.md</code>.</p>
"""]
    for key, sentence in (
        ("s1", TARGETS["s1"]), ("s2", TARGETS["s2"]), ("s3", TARGETS["s3"])
    ):
        parts.append(f'<h2>{key.upper()} — &ldquo;{sentence}&rdquo;</h2>')
        parts.append(
            f'<div class="clip baseline"><label>baseline (no tone)</label>'
            f'<audio controls preload="none" src="{audio_rel}/base_{key}.wav"></audio></div>'
        )
        for prefix, label in TONE_LABELS.items():
            name = f"{prefix}_{key}_trim"
            parts.append(
                f'<div class="clip"><label>{label}</label>'
                f'<audio controls preload="none" src="{audio_rel}/{name}.wav"></audio></div>'
            )
    parts.append("</body>\n</html>\n")
    (HERE / "listen.html").write_text("\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    main()
