"""Phase 6: the per-voice listening page (listen.html).

Imported by build_set.py. Groups every clip per voice (reference recording
= identity anchor), puts the neufeld tone sanity check in its own section,
and embeds Simone's Phase 5 clips from ../naturalness/audio/trimmed/ for
direct A/B comparison.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

sys.path.insert(0, str(HERE.parent / "naturalness"))
from clips import CATEGORY_ORDER, CLIPS, listening_name  # noqa: E402

sys.path.insert(0, str(HERE))
from setup_plan import comparison_clips, tone_clips  # noqa: E402

AUDIO_REL = "audio/trimmed"

VOICE_LABELS = {
    "neufeld": "Voice B — Neufeld (male, US narrator)",
    "golding": "Voice C — Golding (female, British narrator)",
}
VOICE_DESC = {
    "neufeld": (
        "Bob Neufeld reading <i>Dr. Jekyll and Mr. Hyde</i> "
        "(LibriVox, public domain)."
    ),
    "golding": (
        "Ruth Golding reading <i>The Adventures of Sherlock Holmes</i> "
        "(LibriVox, public domain)."
    ),
}

EMO_NAMES = {"emo1", "emo2", "emo3"}
EMO_PLAIN_NOTE = (
    "plain here (no tone tag; Phase 5 Simone version was tagged+trimmed)"
)

HEADER = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Phase 6 — multiple voices (listening)</title>
<style>
 body { font-family: -apple-system, sans-serif; max-width: 780px; margin: 2rem auto; }
 h2 { border-bottom: 1px solid #ccc; padding-bottom: .2rem; margin-top: 2.5rem; }
 h3 { margin-top: 1.6rem; color: #333; }
 .ref { background: #f6f6f6; padding: .6rem; border-radius: 6px; margin: 1rem 0; }
 .clip { margin: .8rem 0; }
 .clip label { display: block; font-weight: 600; margin-bottom: .2rem; }
 .promptnote, .catnote { color: #888; font-weight: 400; font-size: .85rem; }
 .catnote::before { content: '['; } .catnote::after { content: ']'; }
 audio { width: 100%; }
</style>
</head>
<body>
<h1>Phase 6 — multiple voices evaluation</h1>
<p>Two new voices alongside Simone (DEVELOPMENT.md §13). For each voice,
listen to the <b>reference</b> first (identity anchor), then every clip, and
rate 1–5 on <b>Identity vs this voice's reference</b> (headline — does it
sound like that speaker?), <b>Naturalness</b> and <b>Consistency</b>.
Cross-voice question to answer after: do the three voices sound like
different people? Simone's Phase 5 clips (same model, same sentences) are
embedded at the bottom for direct comparison.</p>
"""

TONE_SECTION_HEAD = (
    '<h2>Tone sanity check — Voice B (Neufeld)</h2>'
    "<p>For each sentence, listen to the <b>baseline</b> first (no tone "
    "direction), then each tone, and rate the tone <b>against the "
    "baseline</b> (1–5, §18): does it still sound like the <b>same "
    "person</b> (Identity), is it natural (Naturalness), does the tone come "
    "through (Expression), and is it Consistent? Tags are leak-trimmed with "
    "the Phase 3 whisper-timestamp method.</p>"
)

BASELINE_CLIP = (
    '<div class="clip"><label>baseline</label>'
    '<audio controls preload="none" '
    'src="{audio}/{name}.wav"></audio></div>'
)

TONE_CLIP = (
    '<div class="clip"><label>[{prompt_name}] '
    '<span class="promptnote">(tagged, trimmed)</span></label>'
    '<audio controls preload="none" '
    'src="{audio}/{name}_trim.wav"></audio></div>'
)

SIMONE_HEAD = (
    "<h2>Simone — Phase 5 reference set (for direct comparison)</h2>"
    '<p><a href="../naturalness/listen.html">Open the Phase 5 listening page'
    "</a>. Same model, same 15 sentences. In Phase 5 the three emotional "
    "lines were tagged+trimmed (<code>emo1_trim/emo2_trim/emo3_trim</code>); "
    "in Phase 6 they are plain. Compare the new voices against these on the "
    "12 plain clips.</p>"
)


def write_listen_page() -> None:
    parts = [HEADER]

    for voice, label in VOICE_LABELS.items():
        parts.append(f"<h2>{label}</h2>")
        parts.append(
            f'<div class="ref">{VOICE_DESC[voice]} '
            "Reference recording (identity anchor):"
            f'<audio controls preload="none" '
            f'src="../../voices/{voice}/reference.wav"></audio></div>'
        )
        for category in CATEGORY_ORDER:
            parts.append(f"<h3>{category}</h3>")
            for name, text, cat, phase5_name, v in comparison_clips():
                if v != voice or cat != category:
                    continue
                note = (
                    f' <span class="promptnote">{EMO_PLAIN_NOTE}</span>'
                    if phase5_name in EMO_NAMES
                    else ""
                )
                parts.append(
                    f'<div class="clip"><label>&ldquo;{text}&rdquo;'
                    f' <span class="catnote">{category}</span>{note}</label>'
                    f'<audio controls preload="none" '
                    f'src="{AUDIO_REL}/{name}.wav"></audio></div>'
                )

    parts.append(TONE_SECTION_HEAD)
    for name, gen_text, sentence, tagged, key in tone_clips():
        if not tagged:
            parts.append(f"<h3>S{key[-1]} — &ldquo;{sentence}&rdquo;</h3>")
            parts.append(BASELINE_CLIP.format(audio=AUDIO_REL, name=name))
        else:
            prompt_name = gen_text.split("]", 1)[0][1:]
            parts.append(
                TONE_CLIP.format(
                    audio=AUDIO_REL, name=name, prompt_name=prompt_name
                )
            )

    parts.append(SIMONE_HEAD)
    for category in CATEGORY_ORDER:
        parts.append(f"<h3>{category}</h3>")
        for clip in CLIPS:
            if clip["category"] != category:
                continue
            text = clip["text"]
            lname = listening_name(clip)
            parts.append(
                f'<div class="clip"><label>&ldquo;{text}&rdquo;'
                f' <span class="catnote">{category}</span></label>'
                f'<audio controls preload="none" '
                f'src="../naturalness/audio/trimmed/{lname}.wav"></audio></div>'
            )

    parts.append("</body>\n</html>\n")
    (HERE / "listen.html").write_text("\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    write_listen_page()