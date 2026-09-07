"""Phase 5: build the listening set in audio/trimmed/ (+ trim_report.md).

Most Phase 5 clips are PLAIN clone generations — no prompt, no leak — so
they are copied through unchanged, exactly like the Phase 4 baselines. Only
the three inherently-emotional clips ([sad] / [excited] tags + the NL
concern instruction) carry a spoken style prompt, and those are trimmed to
the target sentence with the whisper-timestamp method proven in Phase 3 and
reused by Phase 4 (find_cut / trim_wav from experiments/tone/trim_clips.py).

This script also generates listen.html, the category-grouped listening page
for the §12 / §18 evaluation.

Usage:
    .venv/bin/python experiments/naturalness/trim_clips.py
"""

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# NOTE: tone dir goes at sys.path[0] so `from trim_clips import ...` resolves
# to experiments/tone/trim_clips.py (the Phase 3 helpers), NOT this script,
# which has the same filename. This script's own directory is already on
# sys.path (script dir), so `import clips` still works.
sys.path.insert(0, str(HERE.parent / "tone"))
from trim_clips import find_cut, trim_wav  # noqa: E402  (Phase 3 helpers)

from clips import (  # noqa: E402
    CATEGORY_ORDER,
    CLIPS,
    generate_text,
    listening_name,
)

RAW_DIR = HERE / "audio" / "raw"
TRIMMED_DIR = HERE / "audio" / "trimmed"


def main() -> None:
    import mlx_whisper  # lazy: keeps startup fast

    WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"
    rows = [
        "# Phase 5 — listening set build (audio/trimmed/)\n",
        "Plain clips copied through untrimmed (no prompt, no leak); the "
        "three tagged emotional clips cut with the Phase 3 "
        "whisper-timestamp method. Listen via listen.html.\n",
        "| Clip | Source | Cut at (s) | Match | Final (s) | Transcript |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    TRIMMED_DIR.mkdir(parents=True, exist_ok=True)

    for clip in CLIPS:
        name = clip["name"]
        src = RAW_DIR / f"{name}_000.wav"
        if not src.exists():
            print(f"{name}: raw clip missing, skipped", flush=True)
            continue
        if clip["prompt"] is None:
            # Plain clone: no prompt, nothing to trim — copy through.
            out = TRIMMED_DIR / f"{name}.wav"
            shutil.copy2(src, out)
            print(f"{name}: copied (plain clip)", flush=True)
            rows.append(f"| {name} | plain copy | — | — | — | — |")
            continue
        # Tagged clip: locate the target-sentence boundary and cut.
        result = mlx_whisper.transcribe(
            str(src), path_or_hf_repo=WHISPER_MODEL, word_timestamps=True
        )
        words = [w for seg in result["segments"] for w in seg.get("words", [])]
        if not words:
            print(f"{name}: no word timestamps, skipped", flush=True)
            continue
        cut, ratio = find_cut(words, clip["text"])
        out = TRIMMED_DIR / f"{listening_name(clip)}.wav"
        dur = trim_wav(src, cut, out)
        trimmed_text = mlx_whisper.transcribe(
            str(out), path_or_hf_repo=WHISPER_MODEL
        )["text"].strip()
        print(
            f"{out.stem:10s} cut {cut:5.2f}s  match {ratio:.2f}  -> {dur:4.1f}s"
            f"\n    transcript: {trimmed_text}\n",
            flush=True,
        )
        rows.append(
            f"| {listening_name(clip)} | `{generate_text(clip)}` "
            f"| {cut:.2f} | {ratio:.2f} | {dur:.1f} | {trimmed_text} |"
        )

    write_listen_page()
    (HERE / "trim_report.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("wrote trim_report.md and listen.html")


def write_listen_page() -> None:
    """Listening page grouped by §12 category, like the Phase 4 page."""
    audio_rel = "audio/trimmed"
    prompt_note = {
        "emo1": "prompt: [sad] (trimmed)",
        "emo2": "prompt: [excited] (trimmed)",
        "emo3": "prompt: NL concern direction (trimmed)",
    }
    parts = ["""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Phase 5 — naturalness evaluation (listening)</title>
<style>
 body { font-family: -apple-system, sans-serif; max-width: 760px; margin: 2rem auto; }
 h2 { border-bottom: 1px solid #ccc; padding-bottom: .2rem; margin-top: 2.5rem; }
 .clip { margin: .8rem 0; }
 .clip label { display: block; font-weight: 600; margin-bottom: .2rem; }
 .promptnote { color: #888; font-weight: 400; font-size: .85rem; }
 audio { width: 100%; }
</style>
</head>
<body>
<h1>Phase 5 — naturalness evaluation</h1>
<p>Simone clone, default delivery. Plain clone generations except the three
emotional lines (tag/NL prompt, leak-trimmed — Phase 4 pattern). Rate every
clip 1–5 on <b>Naturalness</b> (headline dimension, §18); on the difficult
text also note any <b>pronunciation</b> errors, and judge <b>Consistency</b>
across the set. Transfer ratings into <code>notes.md</code>.</p>
"""]
    for category in CATEGORY_ORDER:
        parts.append(f"<h2>{category}</h2>")
        for clip in CLIPS:
            if clip["category"] != category:
                continue
            label = f'&ldquo;{clip["text"]}&rdquo;'
            if clip["prompt"] is not None:
                label += (
                    f' <span class="promptnote">{prompt_note[clip["name"]]}</span>'
                )
            parts.append(
                f'<div class="clip"><label>{label}</label>'
                f'<audio controls preload="none" '
                f'src="{audio_rel}/{listening_name(clip)}.wav"></audio></div>'
            )
    parts.append("</body>\n</html>\n")
    (HERE / "listen.html").write_text("\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    main()
