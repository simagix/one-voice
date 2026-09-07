"""Experiment 3b: trim the leaked style text from the tone-experiment clips.

Phase 3 showed the Qwen3-TTS Base model speaks the tag/instruction text aloud
(in-band only). This script cuts each clip so only the target sentence
remains, using mlx-whisper word timestamps:

1. transcribe each clip with word_timestamps=True,
2. find the word boundary where the target sentence starts (best fuzzy match
   of the transcript tail against the known target sentence),
3. write the trimmed audio to audio/trimmed/ (git-ignored, like audio/).

If the trimmed clips still sound like Simone and rate well on naturalness,
that gives us practical out-of-band tone control on the Base model via
post-processing.

Usage:
    .venv/bin/python experiments/tone/trim_clips.py
"""

import difflib
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
AUDIO_DIR = HERE / "audio"
TRIMMED_DIR = AUDIO_DIR / "trimmed"
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"

# Known target sentence per clip (everything before it is leaked direction).
TARGETS = {
    "s1": "Thank you for calling. How may I help you today?",
    "s2": "Well, that certainly went according to plan.",
    "s3": "I need you to listen to me.",
}
CUT_PAD_S = 0.05  # small back-off so the first phoneme is not clipped


def normalize(s: str) -> str:
    return " ".join("".join(c for c in s.lower() if c.isalnum() or c == " ").split())


def find_cut(words: list[dict], target: str) -> tuple[float, float]:
    """Return (cut_time_s, match_ratio) for the boundary that best matches
    the target sentence as the remaining transcript tail."""
    norm_target = normalize(target)
    words_norm = [normalize(w["word"]) for w in words]
    best_time, best_ratio = 0.0, 0.0
    for i in range(len(words)):
        tail = " ".join(words_norm[i:])
        ratio = difflib.SequenceMatcher(None, tail, norm_target).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_time = words[i]["start"]
    return best_time, best_ratio


def trim_wav(path: Path, cut_s: float, out_path: Path) -> float:
    with wave.open(str(path)) as w:
        sr = w.getframerate()
        nch = w.getnchannels()
        sw = w.getsampwidth()
        assert sw == 2 and nch == 1
        frames = w.readframes(w.getnframes())
    x = np.frombuffer(frames, dtype=np.int16)
    start = max(0, int((cut_s - CUT_PAD_S) * sr))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(nch)
        w.setsampwidth(sw)
        w.setframerate(sr)
        w.writeframes(x[start:].tobytes())
    return (len(x) - start) / sr


def main() -> None:
    import mlx_whisper  # lazy: keeps startup fast

    rows = ["# Experiment 3b — trimmed clips (leaked style text removed)\n",
            "Cut points found via whisper word timestamps; listen and re-rate naturalness.\n",
            "| Clip | Cut at (s) | Match | Trimmed (s) | Transcript of trimmed clip |",
            "| --- | ---: | ---: | ---: | --- |"]

    for path in sorted(AUDIO_DIR.glob("*_000.wav")):
        if path.parent != AUDIO_DIR:
            continue
        key = next((k for k in TARGETS if k in path.name), None)
        if key is None:
            continue
        result = mlx_whisper.transcribe(
            str(path), path_or_hf_repo=WHISPER_MODEL, word_timestamps=True
        )
        words = [w for seg in result["segments"] for w in seg.get("words", [])]
        if not words:
            print(f"{path.stem}: no word timestamps, skipped", flush=True)
            continue
        cut, ratio = find_cut(words, TARGETS[key])
        out = TRIMMED_DIR / f"{path.stem.replace('_000', '')}_trim.wav"
        dur = trim_wav(path, cut, out)
        trimmed_text = mlx_whisper.transcribe(str(out), path_or_hf_repo=WHISPER_MODEL)["text"].strip()
        print(f"{out.stem:30s} cut {cut:5.2f}s  match {ratio:.2f}  -> {dur:4.1f}s"
              f"\n    transcript: {trimmed_text}\n", flush=True)
        rows.append(f"| {out.stem} | {cut:.2f} | {ratio:.2f} | {dur:.1f} | {trimmed_text} |")

    (HERE / "trim_report.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("wrote trim_report.md")


if __name__ == "__main__":
    main()
