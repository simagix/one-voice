#!/usr/bin/env python3
"""OneVoice — experimental local text-to-speech using Qwen-TTS."""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

# VERSION file lives next to this script.
_VERSION_FILE = Path(__file__).resolve().parent / "VERSION"
_PROJECT_NAME = "one-voice"

# Qwen3-TTS 1.7B Base (MLX 8-bit): supports ICL voice cloning from
# ref_audio + ref_text. Override with --model.
DEFAULT_MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit"


def get_version() -> str:
    """Return the project version read from the VERSION file."""
    try:
        version = _VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError as exc:
        print(f"error: unable to read {_VERSION_FILE}: {exc}", file=sys.stderr)
        raise SystemExit(1)
    if not version:
        print(f"error: {_VERSION_FILE} is empty", file=sys.stderr)
        raise SystemExit(1)
    return version


def _fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def _resolve_ref_text(ref_audio: Path, explicit: str | None) -> str | None:
    """Find the transcript for a reference recording.

    Priority: --ref-text > sidecar file next to the reference audio.
    Returns None to let mlx-audio auto-transcribe (downloads a whisper model).
    """
    if explicit:
        return explicit
    sidecar = ref_audio.with_suffix(".txt")
    if sidecar.exists():
        text = sidecar.read_text(encoding="utf-8").strip()
        if text:
            return text
    return None


def _synthesize(
    text: str,
    model: str,
    output: Path,
    ref_audio: Path | None = None,
    ref_text: str | None = None,
) -> None:
    """Generate speech and place the result at the exact requested path.

    mlx-audio writes '<file_prefix>_NNN.wav' into a directory, so we
    generate into a temp dir and move the result to `output`.
    """
    # Imported lazily so --version / --help stay fast.
    from mlx_audio.tts.generate import generate_audio

    output = output.resolve()
    if output.suffix.lower() != ".wav":
        _fail(f"output must be a .wav file, got: {output}")
    if ref_audio is not None and not ref_audio.exists():
        _fail(f"reference audio not found: {ref_audio}")
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        generate_audio(
            text=text,
            model=model,
            voice=None,
            ref_audio=str(ref_audio) if ref_audio is not None else None,
            ref_text=ref_text,
            output_path=tmp,
            file_prefix="out",
            audio_format="wav",
            verbose=False,
        )
        produced = sorted(Path(tmp).glob("out_*.wav"))
        if not produced:
            _fail("model produced no audio")
        shutil.move(str(produced[-1]), output)
    print(f"wrote {output}")


def cmd_generate(args: argparse.Namespace) -> None:
    _synthesize(args.text, args.model, Path(args.output))


def cmd_clone(args: argparse.Namespace) -> None:
    ref_audio = Path(args.reference)
    ref_text = _resolve_ref_text(ref_audio, args.ref_text)
    if ref_text is None:
        print(
            "note: no transcript found for the reference audio; "
            "mlx-audio will auto-transcribe (downloads a whisper model)",
            file=sys.stderr,
        )
    _synthesize(
        args.text,
        args.model,
        Path(args.output),
        ref_audio=ref_audio,
        ref_text=ref_text,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_PROJECT_NAME,
        description="OneVoice — experimental local text-to-speech using Qwen-TTS.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{_PROJECT_NAME} v{get_version()}",
    )
    sub = parser.add_subparsers(dest="command")

    p_gen = sub.add_parser(
        "generate",
        help="generate speech from text (no specific speaker)",
    )
    p_gen.add_argument("--text", required=True, help="text to speak")
    p_gen.add_argument("--output", required=True, help="output WAV path")
    p_gen.add_argument("--model", default=DEFAULT_MODEL, help=f"model repo (default: {DEFAULT_MODEL})")
    p_gen.set_defaults(func=cmd_generate)

    p_clone = sub.add_parser(
        "clone",
        help="generate speech using a cloned reference voice",
    )
    p_clone.add_argument("--reference", required=True, help="reference WAV of the speaker to clone")
    p_clone.add_argument("--text", required=True, help="text to speak")
    p_clone.add_argument("--output", required=True, help="output WAV path")
    p_clone.add_argument(
        "--ref-text",
        default=None,
        help="transcript of the reference audio (defaults to <reference>.txt sidecar)",
    )
    p_clone.add_argument("--model", default=DEFAULT_MODEL, help=f"model repo (default: {DEFAULT_MODEL})")
    p_clone.set_defaults(func=cmd_clone)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

