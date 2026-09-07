"""Phase 6: locate a clean 10–15 s reference window in a long source recording.

The Phase 6 references come from long public-domain LibriVox recordings, not
dedicated 10 s takes like Simone's. This script finds the raw material for a
reference clip inside a long source file:

1. decode the first --scan seconds to a temp mono 24 kHz WAV (ffmpeg),
2. whisper-transcribe with word timestamps (mlx-whisper,
   whisper-large-v3-turbo — the same model as the reference sidecar),
3. report candidate windows: --min–--max seconds of continuous speech
   starting at a segment (sentence) boundary, ranked by total internal
   pause time, then by closeness to --min+2 s.

The chosen window is then cut at the repo root (original untouched) and
converted to voices/<name>/reference.wav by prep_reference.py, exactly like
Simone's root WAV -> voices/simone/reference.wav pipeline.

Usage:
    .venv/bin/python experiments/phase6/find_reference_segment.py SOURCE.mp3 \
        [--scan 240] [--min 10] [--max 15] [--top 5]
"""

import argparse
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"
MAX_GAP_S = 0.7  # a sentence pause inside the window is fine, but not silence


def decode_head(src: Path, seconds: float) -> Path:
    """Decode the first `seconds` of src to a mono 24 kHz temp WAV."""
    tmp = Path(tempfile.mkdtemp()) / "head.wav"
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-t", str(seconds),
            "-i", str(src),
            "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le",
            "-y", str(tmp),
        ],
        check=True,
    )
    return tmp


def candidates(segments: list[dict], lo: float, hi: float) -> list[dict]:
    """Windows starting at each segment boundary, spanning lo–hi seconds."""
    out = []
    for i in range(len(segments)):
        start = segments[i]["start"]
        text_parts, gaps = [], 0.0
        for j in range(i, len(segments)):
            if j > i:
                gaps += max(0.0, segments[j]["start"] - segments[j - 1]["end"])
                if gaps > MAX_GAP_S * (j - i):
                    break
            text_parts.append(segments[j]["text"].strip())
            dur = segments[j]["end"] - start
            if dur >= lo:
                if dur <= hi:
                    out.append(
                        {
                            "start": start,
                            "end": segments[j]["end"],
                            "dur": dur,
                            "gaps": gaps,
                            "text": " ".join(text_parts),
                        }
                    )
                break
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--scan", type=float, default=240,
                        help="seconds of the source to scan (default 240)")
    parser.add_argument("--min", type=float, default=10.0)
    parser.add_argument("--max", type=float, default=15.0)
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    import mlx_whisper  # lazy: keeps startup fast

    head = decode_head(args.source, args.scan)
    try:
        result = mlx_whisper.transcribe(
            str(head), path_or_hf_repo=WHISPER_MODEL, word_timestamps=True
        )
    finally:
        head.unlink(missing_ok=True)

    found = candidates(result["segments"], args.min, args.max)
    if not found:
        print(f"no {args.min}–{args.max}s window in the first {args.scan}s",
              file=sys.stderr)
        raise SystemExit(1)
    found.sort(key=lambda c: (c["gaps"], abs(c["dur"] - (args.min + 2))))
    print(f"# {args.source.name} — top {min(args.top, len(found))} "
          f"of {len(found)} candidate windows")
    for rank, c in enumerate(found[: args.top], 1):
        print(
            f"\n[{rank}] {c['start']:7.2f}s -> {c['end']:7.2f}s "
            f"(dur {c['dur']:.2f}s, internal pauses {c['gaps']:.2f}s)\n"
            f"    {c['text']}"
        )


if __name__ == "__main__":
    main()
