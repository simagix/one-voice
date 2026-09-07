#!/usr/bin/env python3
"""OneVoice — experimental local text-to-speech using Qwen-TTS."""

import argparse
import difflib
import json
import shutil
import sys
import tempfile
import wave
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


# --------------------------------------------------------------------------
# Phase 8 — script support (DEVELOPMENT.md §15)
# --------------------------------------------------------------------------

# Tone vocabulary for script lines. Bracket tags are the Phase 3/4-validated
# ones, spoken by the model in-band and leak-trimmed afterwards; the other
# entries are natural-language directions (the Phase 3 fallback for tags that
# under-delivered). friendly/professional/reassuring are the §15 call-center
# tones — same in-band pattern, gated in Phase 8 by the whisper transcription
# check + by-ear sanity rather than pre-validated in Phase 3/4.
TONES: dict[str, str] = {
    "calm": "[calm]",
    "happy": "[happy]",
    "sad": "[sad]",
    "angry": "[angry]",
    "excited": "[excited]",
    "sarcastic": "Deliver the sentence with dry, understated sarcasm.",
    "friendly": "Speak in a warm, friendly, welcoming way.",
    "professional": "Speak in a clear, professional, composed way.",
    "reassuring": "Speak in a calm, reassuring and confident way.",
}


class ScriptLine:
    """One parsed script line: a [voice | tone] block plus its spoken text."""

    def __init__(self, index: int, voice: str, tone: str | None, text: str):
        self.index = index
        self.voice = voice
        self.tone = tone
        self.text = text

    @property
    def prompt(self) -> str | None:
        """Tone prompt to prepend (None = plain clone)."""
        if self.tone is None:
            return None
        entry = TONES.get(self.tone)
        if entry is None:
            _fail(f"unknown tone: {self.tone!r} (available: {', '.join(TONES)})")
        return entry

    @property
    def stem(self) -> str:
        """Stable per-line file name stem, used for raw/final WAVs."""
        return f"line{self.index:02d}_{self.voice}"

    def __repr__(self) -> str:  # pragma: no cover — debugging aid
        return f"ScriptLine({self.index}, {self.voice!r}, {self.tone!r}, {self.text!r})"


def parse_script(source: str) -> list[ScriptLine]:
    """Parse the §15 script format into ScriptLine objects.

    Format: blank-line-separated blocks. The first line of a block is the
    header `[voice]` or `[voice | tone]`; the remaining lines of the block
    are spoken text, joined with single spaces onto ONE model input line
    (mlx-audio splits its input on newlines — Phase 3/4 lesson). `#` comment
    lines are ignored. Voice must be a known profile (see the 'voices'
    command); tone must be in TONES. Malformed input fails with a precise
    error naming the offending line.
    """
    lines: list[ScriptLine] = []
    voice: str | None = None
    tone: str | None = None
    text_parts: list[str] = []
    header_lineno = 0
    in_block = False

    def flush() -> None:
        nonlocal in_block
        if not in_block:
            return
        text = " ".join(part.strip() for part in text_parts if part.strip())
        if not text:
            _fail(f"line {header_lineno}: block for voice {voice!r} has no text lines")
        assert voice is not None  # set whenever in_block
        lines.append(ScriptLine(len(lines) + 1, voice, tone, text))
        in_block = False

    if not source.strip():
        _fail("script is empty")

    known = _available_voices()
    for lineno, raw in enumerate(source.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            flush()  # blank line ends the current block
            continue
        if stripped.startswith("["):
            if not stripped.endswith("]"):
                _fail(f"line {lineno}: unterminated block header {stripped!r}")
            flush()
            inner = stripped[1:-1]
            name, sep, tone_part = inner.partition("|")
            voice = name.strip()
            tone = tone_part.strip() if sep else None
            header_lineno = lineno
            if not voice:
                _fail(f"line {lineno}: empty voice name in {stripped!r}")
            if voice not in known:
                avail = ", ".join(known) or "(none)"
                _fail(
                    f"line {lineno}: unknown voice profile {voice!r} (available: {avail})"
                )
            if sep and not tone:
                _fail(f"line {lineno}: empty tone in {stripped!r}")
            if tone is not None and tone not in TONES:
                _fail(
                    f"line {lineno}: unknown tone {tone!r} (available: {', '.join(TONES)})"
                )
            text_parts = []
            in_block = True
            continue
        if not in_block:
            _fail(f"line {lineno}: text {stripped!r} appears before any [voice] header")
        text_parts.append(stripped)
    flush()
    return lines


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


# --------------------------------------------------------------------------
# Phase 8 — script generation (DEVELOPMENT.md §15)
# --------------------------------------------------------------------------

# Leak-trim helpers are imported from experiments/tone/trim_clips.py using
# the sys.path pattern proven in Phase 6 (see development.log for the
# same-named-module gotcha that forced unique filenames in the experiment
# dirs; one_voice.py has no such clash).
_TONE_HELPERS_DIR = _ROOT / "experiments" / "tone"


def _tone_helpers():
    """Lazy import of the Phase 3 helpers: (WHISPER_MODEL, find_cut, normalize, trim_wav)."""
    if str(_TONE_HELPERS_DIR) not in sys.path:
        sys.path.insert(0, str(_TONE_HELPERS_DIR))
    from trim_clips import WHISPER_MODEL, find_cut, normalize, trim_wav

    return WHISPER_MODEL, find_cut, normalize, trim_wav


def _transcribe(path: Path) -> str:
    """Whisper transcript of a clip — the objective pronunciation gate."""
    import mlx_whisper  # lazy: keeps --help / --dry-run fast

    whisper_model, _, _, _ = _tone_helpers()
    return mlx_whisper.transcribe(str(path), path_or_hf_repo=whisper_model)["text"].strip()


def _duration_s(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def _print_plan(lines: list[ScriptLine]) -> None:
    print(f"script plan: {len(lines)} line(s)")
    for line in lines:
        preview = line.text if len(line.text) <= 60 else line.text[:57] + "..."
        tone = line.tone if line.tone is not None else "(none)"
        print(f"  {line.stem}: [{line.voice} | {tone}] {preview}")


def _generate_line(
    line: ScriptLine,
    model: str,
    ref_audio: Path,
    ref_text: str | None,
    raw_dir: Path,
    final_dir: Path,
) -> dict:
    """Generate one script line independently; return its manifest entry.

    Tone lines are generated with the in-band prompt on the SAME line as the
    text (mlx-audio newline-splitting rule) and leak-trimmed to the target
    text with the Phase 3 whisper-timestamp helpers. Plain lines are copied
    through unchanged (the Phase 4 baseline convention).
    """
    whisper_model, find_cut, normalize, trim_wav = _tone_helpers()
    prompt = line.prompt
    raw_path = raw_dir / f"{line.stem}.wav"
    final_path = final_dir / f"{line.stem}.wav"
    model_input = line.text if prompt is None else f"{prompt} {line.text}"
    _synthesize(model_input, model, raw_path, ref_audio=ref_audio, ref_text=ref_text)

    entry: dict = {
        "index": line.index,
        "voice": line.voice,
        "tone": line.tone,
        "text": line.text,
        "prompt": prompt,
        "reference": str(ref_audio),
        "model": model,
        "raw": str(raw_path),
        "final": str(final_path),
    }
    if prompt is None:
        shutil.copy2(raw_path, final_path)
        entry["trim"] = None
    else:
        import mlx_whisper  # lazy

        result = mlx_whisper.transcribe(
            str(raw_path), path_or_hf_repo=whisper_model, word_timestamps=True
        )
        words = [w for seg in result["segments"] for w in seg.get("words", [])]
        if not words:
            _fail(f"{line.stem}: whisper produced no word timestamps; cannot trim the tone leak")
        cut_s, match = find_cut(words, line.text)
        entry["trim"] = {"cut_s": round(cut_s, 3), "match_ratio": round(match, 4)}
        trim_wav(raw_path, cut_s, final_path)

    entry["duration_s"] = round(_duration_s(final_path), 2)
    entry["transcript"] = _transcribe(final_path)
    entry["transcript_match"] = round(
        difflib.SequenceMatcher(
            None, normalize(entry["transcript"]), normalize(line.text)
        ).ratio(),
        4,
    )
    note = "" if entry["transcript_match"] >= 0.90 else "  <-- LOW (listen before accepting)"
    print(
        f"  {line.stem}: {entry['duration_s']:.1f}s "
        f"transcript_match={entry['transcript_match']:.2f}{note}",
        flush=True,
    )
    print(f"    transcript: {entry['transcript']}", flush=True)
    return entry


def cmd_script(args: argparse.Namespace) -> None:
    """Generate each line of a script file independently (Phase 8, §15)."""
    script_path = Path(args.file)
    if not script_path.exists():
        _fail(f"script file not found: {script_path}")
    lines = parse_script(script_path.read_text(encoding="utf-8"))
    if not lines:
        _fail(f"no [voice] blocks found in {script_path}")
    if args.dry_run:
        print("dry run — no audio will be generated")
        _print_plan(lines)
        return

    output_dir = Path(args.output_dir).resolve()
    raw_dir = output_dir / "raw"
    final_dir = output_dir / "final"
    raw_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)
    print(f"generating {len(lines)} line(s) -> {output_dir}", flush=True)

    entries = []
    for line in lines:
        ref_audio = _profile_reference(line.voice)
        ref_text = _resolve_ref_text(ref_audio, None)
        print(
            f"[{line.index}/{len(lines)}] [{line.voice} | {line.tone or 'plain'}]",
            flush=True,
        )
        entries.append(
            _generate_line(line, args.model, ref_audio, ref_text, raw_dir, final_dir)
        )

    manifest = {"script": str(script_path), "model": args.model, "lines": entries}
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {manifest_path}")
    low = [e for e in entries if e["transcript_match"] < 0.90]
    if low:
        names = ", ".join(f"line{e['index']:02d}_{e['voice']}" for e in low)
        print(
            f"warning: {len(low)} line(s) with transcript_match < 0.90: {names}",
            file=sys.stderr,
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

    p_script = sub.add_parser(
        "script",
        help="generate each line of a script file independently (Phase 8)",
    )
    p_script.add_argument(
        "--file",
        required=True,
        help="script path ([voice | tone] blocks, # comments allowed)",
    )
    p_script.add_argument(
        "--output-dir",
        default="output",
        help="directory for raw/ + final/ + manifest.json (default: output)",
    )
    p_script.add_argument(
        "--dry-run",
        action="store_true",
        help="parse and print the plan without generating audio",
    )
    p_script.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"model repo (default: {DEFAULT_MODEL})"
    )
    p_script.set_defaults(func=cmd_script)

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

