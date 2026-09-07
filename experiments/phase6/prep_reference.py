"""Phase 6: prepare a reference voice (the Simone pipeline, one voice at a time).

Takes the extracted source segment at the repo root (cut from the untouched
original recording by find_reference_segment.py + ffmpeg) and produces:

  voices/<name>/reference.wav  — mono, 24 kHz, 16-bit (ffmpeg -ac 1 -ar 24000
                                 -c:a pcm_s16le), the exact Simone conversion
  voices/<name>/reference.txt  — whisper-large-v3-turbo transcript sidecar,
                                 so one_voice.py clone picks it up and ICL
                                 cloning gets the correct ref_text

and runs the Phase 6 quality gate BEFORE anything is generated (a bad
reference poisons every downstream clip):

  - source and output format (16-bit mono; output must be 24 kHz)
  - duration inside 8–15 s (Simone's reference: 10.56 s)
  - transcript non-empty and plausible for the duration (chars/s sanity)
  - printed transcript for eyeball confirmation against the known source text

Usage:
    .venv/bin/python experiments/phase6/prep_reference.py SOURCE.wav NAME
    e.g. .venv/bin/python experiments/phase6/prep_reference.py neufeld.wav neufeld
"""

import argparse
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"
MIN_DUR, MAX_DUR = 8.0, 15.0
# Simone's reference is 10.56 s / 154 chars ≈ 14.6 chars/s; flag far outliers.
MIN_CHARS_PER_S, MAX_CHARS_PER_S = 6.0, 30.0


def wav_info(path: Path) -> tuple[float, int, int, int]:
    with wave.open(str(path)) as w:
        return (
            w.getnframes() / w.getframerate(),
            w.getframerate(),
            w.getnchannels(),
            w.getsampwidth(),
        )


def gate(label: str, ok: bool, detail: str) -> bool:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}: {detail}")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="extracted root WAV segment")
    parser.add_argument("name", help="voice name -> voices/<name>/")
    args = parser.parse_args()

    src = args.source.resolve()
    if not src.exists():
        print(f"error: source not found: {src}", file=sys.stderr)
        raise SystemExit(1)

    dur, rate, nch, sw = wav_info(src)
    print(f"# gate: source {src.name}")
    ok = True
    ok &= gate("duration", MIN_DUR <= dur <= MAX_DUR, f"{dur:.2f}s")
    ok &= gate("sample rate", True, f"{rate} Hz (kept as-is; output is 24 kHz)")
    ok &= gate("channels", nch == 1, f"{nch} (mono required)")
    ok &= gate("sample width", sw == 2, f"{sw * 8}-bit")
    if not ok:
        raise SystemExit(1)

    voice_dir = REPO / "voices" / args.name
    voice_dir.mkdir(parents=True, exist_ok=True)
    ref_wav = voice_dir / "reference.wav"
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", str(src),
            "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le",
            "-y", str(ref_wav),
        ],
        check=True,
    )

    import mlx_whisper  # lazy: after the format gate, keeps startup fast

    transcript = mlx_whisper.transcribe(
        str(ref_wav), path_or_hf_repo=WHISPER_MODEL
    )["text"].strip()
    (voice_dir / "reference.txt").write_text(transcript + "\n", encoding="utf-8")

    out_dur, out_rate, out_nch, out_sw = wav_info(ref_wav)
    cps = len(transcript) / out_dur if out_dur else 0.0
    print(f"# gate: output {ref_wav.relative_to(REPO)}")
    ok = True
    ok &= gate("format", out_rate == 24000 and out_nch == 1 and out_sw == 2,
               f"{out_rate} Hz, {out_nch} ch, {out_sw * 8}-bit")
    ok &= gate("duration", MIN_DUR <= out_dur <= MAX_DUR, f"{out_dur:.2f}s")
    ok &= gate("transcript non-empty", bool(transcript), f"{len(transcript)} chars")
    ok &= gate(
        "speech density",
        MIN_CHARS_PER_S <= cps <= MAX_CHARS_PER_S,
        f"{cps:.1f} chars/s (Simone reference ≈ 14.6)",
    )
    print(f"\n  transcript ({voice_dir / 'reference.txt'}):\n    {transcript}")
    if not ok:
        print("\nGATE FAILED — fix the source segment before generating anything.",
              file=sys.stderr)
        raise SystemExit(1)
    print("\nGATE PASSED — reference ready. Confirm the transcript by ear, "
          "then generate.")


if __name__ == "__main__":
    main()
