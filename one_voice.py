#!/usr/bin/env python3
"""OneVoice — experimental local text-to-speech using Qwen-TTS."""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

try:
    import yaml  # for voice profiles (voices/<name>/voice.yaml)
except ImportError:  # pragma: no cover — degrade gracefully to the default layout
    yaml = None

# Files and directories live next to this script.
_ROOT = Path(__file__).resolve().parent
_VOICES_DIR = _ROOT / "voices"
_VERSION_FILE = _ROOT / "VERSION"
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


def _available_voices() -> list[str]:
    """Voice profile names = subdirectories of voices/ with a reference.wav."""
    if not _VOICES_DIR.is_dir():
        return []
    return sorted(
        d.name
        for d in _VOICES_DIR.iterdir()
        if d.is_dir() and (d / "reference.wav").exists()
    )


def _profile_reference(voice: str) -> Path:
    """Reference WAV for a named voice profile (Phase 7, DEVELOPMENT.md §14).

    Reads voices/<voice>/voice.yaml for the reference path, defaulting to
    voices/<voice>/reference.wav when the profile is absent. Refuses unknown
    voices with a helpful list of the available ones.
    """
    voice_dir = _VOICES_DIR / voice
    if not (voice_dir / "reference.wav").exists():
        avail = ", ".join(_available_voices()) or "(none)"
        _fail(f"unknown voice profile: {voice!r} (available: {avail})")
    ref_rel = "reference.wav"
    yaml_path = voice_dir / "voice.yaml"
    if yaml_path.exists() and yaml is not None:
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            _fail(f"cannot parse {yaml_path}: {exc}")
        ref = (data or {}).get("reference")
        if ref:
            ref_rel = str(ref)
    return voice_dir / ref_rel


def _profile_description(voice: str) -> str:
    yaml_path = _VOICES_DIR / voice / "voice.yaml"
    if yaml_path.exists() and yaml is not None:
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            return "—"
        return (data or {}).get("description") or "—"
    return "—"


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
    has_voice, has_ref = bool(args.voice), bool(args.reference)
    if has_voice == has_ref:
        _fail(
            "exactly one of --voice (named profile) or --reference (path) "
            "is required"
        )
    ref_audio = (
        _profile_reference(args.voice) if has_voice else Path(args.reference)
    )
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


def cmd_voices(args: argparse.Namespace) -> None:
    """List the available named voice profiles (voices/<name>/voice.yaml)."""
    voices = _available_voices()
    if not voices:
        print("no voice profiles found in voices/", file=sys.stderr)
        raise SystemExit(1)
    print("available voice profiles:")
    for voice in voices:
        print(f"  {voice:<10} {_profile_description(voice)}")


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
    ref_group = p_clone.add_mutually_exclusive_group()
    ref_group.add_argument(
        "--reference",
        metavar="WAV",
        help="reference WAV path (mutually exclusive with --voice)",
    )
    ref_group.add_argument(
        "--voice",
        metavar="NAME",
        help="named voice profile (see the 'voices' command)",
    )
    p_clone.add_argument("--text", required=True, help="text to speak")
    p_clone.add_argument("--output", required=True, help="output WAV path")
    p_clone.add_argument(
        "--ref-text",
        default=None,
        help="transcript of the reference audio (defaults to <reference>.txt sidecar)",
    )
    p_clone.add_argument("--model", default=DEFAULT_MODEL, help=f"model repo (default: {DEFAULT_MODEL})")
    p_clone.set_defaults(func=cmd_clone)

    p_voices = sub.add_parser(
        "voices",
        help="list the available voice profiles (voices/<name>/voice.yaml)",
    )
    p_voices.set_defaults(func=cmd_voices)

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

