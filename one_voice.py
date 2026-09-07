#!/usr/bin/env python3
"""OneVoice — experimental local text-to-speech using Qwen-TTS."""

import argparse
import sys
from pathlib import Path

# VERSION file lives next to this script.
_VERSION_FILE = Path(__file__).resolve().parent / "VERSION"
_PROJECT_NAME = "one-voice"


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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())

