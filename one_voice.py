#!/usr/bin/env python3
"""OneVoice — experimental local text-to-speech using Qwen-TTS."""

import argparse
import difflib
import json
import os
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
_VOICES_DIR = Path(os.environ.get("ONE_VOICE_DIR", _ROOT / "voices"))
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


def resolve_default_voice(explicit: str | None = None) -> str:
    """Return the default voice to use when a header omits it.

    Priority:
    1. ``explicit`` argument (caller-specified)
    2. ``ONE_VOICE`` environment variable
    3. First available voice alphabetically (fallback)
    """
    import os

    if explicit:
        return explicit
    env_voice = os.environ.get("ONE_VOICE")
    if env_voice:
        return env_voice
    available = _available_voices()
    if available:
        return available[0]
    _fail("no voice profiles found — add one under voices/<name>/")


# --------------------------------------------------------------------------
# Phase 8 — script support (DEVELOPMENT.md §15)
# --------------------------------------------------------------------------

# Tone vocabulary for script lines. Bracket tags are the Phase 3/4-validated
# ones, spoken by the model in-band and leak-trimmed afterwards; the other
# entries are natural-language directions (the Phase 3 fallback for tags that
# under-delivered). friendly/professional/reassuring are the §15 call-center
# tones — same in-band pattern, gated in Phase 8 by the whisper transcription
# check + by-ear sanity rather than pre-validated in Phase 3/4.
#
# Compatible with deck-to-video's tone vocabulary (narration.py TONES) so the
# same [voice: NAME | tone: TAG] speaker notes work across both systems.
TONES: dict[str, str] = {
    # --- In-band tags (spoken aloud, leak-trimmed) ---
    "calm": "[calm]",
    "happy": "[happy]",
    "sad": "[sad]",
    "angry": "[angry]",
    "excited": "[excited]",
    # --- Natural-language directions ---
    "neutral": "Use a natural, conversational, balanced delivery.",
    "professional": "Speak in a clear, professional, composed way.",
    "friendly": "Speak in a warm, friendly, welcoming way.",
    "warm": "Speak in a warm, sincere, personable way.",
    "cheerful": "Speak in a bright, cheerful, upbeat way, with positive energy.",
    "enthusiastic": "Speak with high enthusiasm and engagement, while remaining natural.",
    "confident": "Speak in a confident, assured, authoritative way.",
    "serious": "Speak in a serious, deliberate, measured way, with appropriate weight.",
    "concerned": "Speak in a concerned, thoughtful way, conveying genuine worry.",
    "frustrated": "Speak with frustration and exasperation, with noticeable impatience.",
    "disappointed": "Speak in a disappointed, slightly dejected way, but controlled.",
    "surprised": "Speak with genuine surprise, with heightened energy and emphasis.",
    "confused": "Speak in a confused, uncertain way, as though trying to understand.",
    "curious": "Speak in a curious, engaged, inquisitive way.",
    "skeptical": "Speak in a skeptical, doubtful way, with a questioning tone.",
    "sarcastic": "Deliver the sentence with dry, understated sarcasm.",
    "humorous": "Speak in a humorous, playful way, with a light-hearted tone.",
    "witty": "Speak in a witty, clever way, with a sharp sense of humor.",
    "dramatic": "Speak in a dramatic, intense way, with strong emotional delivery.",
    "mysterious": "Speak in a mysterious, enigmatic way, with a conspiratorial whisper.",
    "narrative": "Speak as if telling a story, with clear pacing and emphasis.",
    "explainer": "Speak clearly and educationally, like a teacher explaining something.",
    "whisper": "Speak softly and intimately, as if whispering to the listener.",
    "robotic": "Speak in a mechanical, flat way, with artificial precision.",
    "urgent": "Speak with urgency, as if racing against time.",
    "reassuring": "Speak in a calm, reassuring and confident way.",
}


class ScriptLine:
    """One parsed script line: a [voice | tone] block plus its spoken text.

    Supports both bare (``[simone | friendly]``) and labeled
    (``[voice: simone | tone: friendly]``) header formats so existing
    deck-to-video speaker notes work unchanged.
    """

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


def _parse_labeled_header(inner: str) -> tuple[str | None, str | None]:
    """Parse a labeled header: ``voice: NAME | tone: TAG``, ``voice: NAME``, or ``tone: TAG``.

    Returns ``(voice, tone)`` where either may be None if not specified.
    Used for deck-to-video compatibility (``[voice: simone | tone: friendly]``).
    """
    voice: str | None = None
    tone: str | None = None

    for part in inner.split("|"):
        part = part.strip()
        if part.lower().startswith("voice:"):
            voice = part[6:].strip() or None
        elif part.lower().startswith("tone:"):
            tone = part[5:].strip() or None

    return voice, tone


def parse_script(source: str, default_voice: str | None = None) -> list[ScriptLine]:
    """Parse the script format into ScriptLine objects.

    Supports two header formats:

    - **Bare** (one-voice style): ``[voice]`` or ``[voice | tone]``
    - **Labeled** (deck-to-video style): ``[voice: NAME | tone: TAG]``,
      ``[voice: NAME]``, or ``[tone: TAG]``

    Format: blank-line-separated blocks. The first line of a block is the
    header; the remaining lines of the block are spoken text, joined with
    single spaces onto ONE model input line (mlx-audio splits its input on
    newlines — Phase 3/4 lesson). `#` comment lines are ignored. Voice must
    be a known profile (see the 'voices' command); tone must be in TONES.
    Malformed input fails with a precise error naming the offending line.

    ``default_voice`` specifies the voice to use when a header omits it
    (e.g. ``[tone: friendly]`` or untagged text). When ``None``, the first
    available voice is used. Use this to match deck-to-video's "default
    profile" pattern.
    """
    lines: list[ScriptLine] = []
    voice: str | None = default_voice
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
    # Resolve default voice once at the start (for auto-fallback)
    resolved_default = default_voice or resolve_default_voice()
    voice = resolved_default
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

            # Detect format: labeled (deck-to-video) or bare (one-voice)
            if "voice:" in inner or "tone:" in inner:
                # Labeled format: [voice: NAME | tone: TAG], [voice: NAME], [tone: TAG]
                new_voice, new_tone = _parse_labeled_header(inner)
                if new_voice is not None:
                    voice = new_voice
                if new_tone is not None:
                    tone = new_tone
                if voice is None and tone is None:
                    _fail(f"line {lineno}: neither voice nor tone specified in {stripped!r}")
                # Apply default voice if header didn't specify one
                if voice is None:
                    voice = resolved_default
            else:
                # Bare format: [voice | tone] or [voice]
                name, sep, tone_part = inner.partition("|")
                voice = name.strip()
                tone = tone_part.strip() if sep else None
                if sep and not tone:
                    _fail(f"line {lineno}: empty tone in {stripped!r}")

            header_lineno = lineno
            if not voice:
                _fail(f"line {lineno}: empty voice name in {stripped!r}")
            if voice not in known:
                avail = ", ".join(known) or "(none)"
                _fail(
                    f"line {lineno}: unknown voice profile {voice!r} (available: {avail})"
                )
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


def trim_tone_leak(raw_wav: Path, target_text: str, out_wav: Path) -> None:
    """Trim a leaked tone prompt from generated audio.

    After generating ``<instruct> <target_text>``, the spoken instruct leaks
    into the audio. This finds the cut point (whisper-timestamp method,
    Phases 3–6) and writes the trimmed clip to ``out_wav``.
    """
    whisper_model, find_cut, normalize, trim_wav = _tone_helpers()
    transcript = _transcribe(raw_wav)
    if not transcript:
        _fail(f"{raw_wav}: whisper produced no transcript; cannot trim tone leak")
    words = transcript.get("words")
    if not words:
        _fail(f"{raw_wav}: whisper produced no word timestamps; cannot trim tone leak")
    cut_s, match = find_cut(words, target_text)
    trim_wav(raw_wav, cut_s, out_wav)


def _parse_only(spec: str | None) -> list[int] | None:
    """Parse --only INDEX(,INDEX) into a sorted list of unique line indexes."""
    if spec is None:
        return None
    try:
        only = sorted({int(tok) for tok in spec.split(",") if tok.strip()})
    except ValueError:
        _fail(f"--only expects a comma-separated list of integers, got: {spec!r}")
    if not only:
        _fail("--only: no line indexes given")
    return only


def cmd_script(args: argparse.Namespace) -> None:
    """Generate each line of a script file independently (Phase 8, §15)."""
    script_path = Path(args.file)
    if not script_path.exists():
        _fail(f"script file not found: {script_path}")
    lines = parse_script(script_path.read_text(encoding="utf-8"))
    if not lines:
        _fail(f"no [voice] blocks found in {script_path}")
    only = _parse_only(args.only)
    if args.dry_run:
        print("dry run — no audio will be generated")
        if only:
            print(f"--only: would regenerate line(s) {', '.join(str(i) for i in only)}")
        _print_plan(lines)
        return

    output_dir = Path(args.output_dir).resolve()
    raw_dir = output_dir / "raw"
    final_dir = output_dir / "final"
    raw_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)

    # Phase 9 selective regeneration (§16): --only regenerates the listed
    # manifest lines from this script and updates manifest.json in place;
    # every other entry — and its audio — is kept untouched.
    existing: dict[int, dict] = {}
    if only:
        manifest_path = output_dir / "manifest.json"
        if not manifest_path.exists():
            _fail(
                f"--only requires an existing manifest: {manifest_path} "
                "(run a full script generation first)"
            )
        try:
            prior = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            _fail(f"cannot parse {manifest_path}: {exc}")
        existing = {e["index"]: e for e in prior.get("lines", [])}
        missing = [i for i in only if i not in existing]
        if missing:
            avail = ", ".join(str(i) for i in sorted(existing)) or "(none)"
            _fail(
                f"--only: no manifest line(s) with index "
                f"{', '.join(str(i) for i in missing)} (available: {avail})"
            )
        added = [ln.index for ln in lines if ln.index not in existing]
        if added:
            _fail(
                f"--only: script line(s) {', '.join(str(i) for i in added)} are "
                "not in the manifest; regenerate the full script first"
            )
        print(f"regenerating {len(only)} line(s) -> {output_dir}", flush=True)
    else:
        print(f"generating {len(lines)} line(s) -> {output_dir}", flush=True)

    entries = []
    for line in lines:
        if only and line.index not in only:
            entries.append(existing[line.index])
            print(f"[{line.index}/{len(lines)}] [keep] {line.stem}", flush=True)
            continue
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


# --------------------------------------------------------------------------
# Phase 9 — audio assembly (DEVELOPMENT.md §16)
# --------------------------------------------------------------------------

# Basic per-segment level matching ("basic volume normalization", §16): gain
# each clip's RMS to a shared target. Gains are clamped so a near-silent clip
# is not boosted into noise and a very loud one is not crushed — deliberately
# "basic", not loudness-war engineering.
TARGET_RMS = 0.08
MAX_GAIN = 8.0  # clamp headroom: Phase 8 clips measure RMS ~0.014–0.026, peak ≤ 0.21
DEFAULT_PAUSE_MS = 350
DEFAULT_SPEAKER_PAUSE_MS = 600


def _read_wav_mono16(path: Path):
    """Read a mono 16-bit WAV as (sample_rate, int16 numpy array)."""
    import numpy as np  # lazy: only the assembly path needs it

    with wave.open(str(path)) as w:
        sample_rate = w.getframerate()
        nch = w.getnchannels()
        sw = w.getsampwidth()
        frames = w.readframes(w.getnframes())
    if nch != 1 or sw != 2:
        _fail(f"{path}: expected mono 16-bit WAV, got {nch} ch / {sw * 8}-bit")
    return sample_rate, np.frombuffer(frames, dtype=np.int16)


def _write_wav_mono16(path: Path, sample_rate: int, samples) -> None:
    """Write mono 16-bit PCM WAV (the Phase 8 clip format)."""
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(np.ascontiguousarray(samples, dtype=np.int16).tobytes())


def _rms(samples) -> float:
    """RMS of an int16 waveform, normalized to digital full scale (~1.0)."""
    import numpy as np

    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)) / 32768.0)


def _level_gain(samples, target_rms: float) -> float:
    """Gain that brings a segment to the shared RMS target, clamped."""
    import numpy as np

    rms = _rms(samples)
    if rms <= 0.0:
        return 1.0
    return float(np.clip(target_rms / rms, 1.0 / MAX_GAIN, MAX_GAIN))


def _apply_gain(samples, gain: float):
    """Apply a gain to int16 samples, clipping to the int16 range."""
    import numpy as np

    return np.clip(samples.astype(np.float64) * gain, -32768, 32767).astype(np.int16)


def _print_timeline(timeline: list[dict], speaker_changes: int, source: str) -> None:
    print(f"assembly timeline ({len(timeline)} segment(s), source={source}):")
    for seg in timeline:
        print(
            f"  line{seg['index']:02d} {seg['voice'] or '?':<8} "
            f"[{seg['tone'] or 'plain'}] silence {seg['gap_before_s']:5.2f}s | "
            f"{seg['duration_s']:5.2f}s gain {seg['gain']:.2f}x "
            f"@ {seg['start_s']:6.2f}s  {Path(seg['file']).name}"
        )
    print(f"speaker changes: {speaker_changes}")


def _parse_pause_after(spec: str | None, known_indexes: list) -> dict[int, int]:
    """Parse --pause-after INDEX=MS(,INDEX=MS) into {line_index: pause_ms}.

    Each pair replaces the default gap (pause-ms / speaker-pause-ms) that
    follows the given manifest line index — for per-gap micro-adjustments
    such as a longer beat on a multi-agent handoff.
    """
    if not spec:
        return {}
    overrides: dict[int, int] = {}
    for tok in spec.split(","):
        tok = tok.strip()
        if not tok:
            continue
        idx, sep, ms = tok.partition("=")
        try:
            index, pause = int(idx.strip()), int(ms.strip())
        except ValueError:
            _fail(f"--pause-after expects INDEX=MS pairs, got: {tok!r}")
        if pause < 0:
            _fail(f"--pause-after values must be >= 0 ms, got: {pause}")
        if index not in known_indexes:
            avail = ", ".join(str(i) for i in known_indexes) or "(none)"
            _fail(f"--pause-after: line index {index} is not in the manifest (available: {avail})")
        overrides[index] = pause
    return overrides


def cmd_assemble(args: argparse.Namespace) -> None:
    """Combine a Phase 8 output dir's segments into ONE WAV (Phase 9, §16).

    Reads the manifest's per-line clips (final/ by default), matches levels
    with a basic per-segment RMS gain, inserts configurable silences (a longer
    gap on speaker change) and writes a single mono 16-bit WAV plus a small
    assembly report. Never touches raw/, final/ or manifest.json.
    """
    import numpy as np

    if args.pause_ms < 0 or args.speaker_pause_ms < 0:
        _fail("pause values must be >= 0 ms")
    if not args.no_normalize and args.target_rms <= 0.0:
        _fail("--target-rms must be > 0")

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        _fail(f"manifest not found: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _fail(f"cannot parse {manifest_path}: {exc}")
    entries = manifest.get("lines") or []
    if not entries:
        _fail(f"{manifest_path}: manifest has no lines")

    output = Path(args.output).resolve()
    if output.suffix.lower() != ".wav":
        _fail(f"output must be a .wav file, got: {output}")

    # Load every segment up front: the timeline needs durations and gains even
    # for --dry-run, and format errors must fail before anything is written.
    loaded = []
    sample_rate = None
    for entry in entries:
        rel = entry.get(args.source)
        if not rel:
            _fail(
                f"line {entry.get('index')}: manifest entry has no "
                f"{args.source!r} clip path"
            )
        path = Path(rel)
        if not path.exists():
            _fail(f"line {entry.get('index')}: missing {args.source} clip: {path}")
        sr, samples = _read_wav_mono16(path)
        if sample_rate is None:
            sample_rate = sr
        elif sr != sample_rate:
            _fail(f"{path}: sample rate {sr} Hz != {sample_rate} Hz of earlier segments")
        gain = 1.0 if args.no_normalize else _level_gain(samples, args.target_rms)
        loaded.append((entry, path, samples, gain))

    # Pause model: --pause-ms between consecutive lines, --speaker-pause-ms
    # when the voice profile changes (silence between speakers, §16).
    # --pause-after INDEX=MS replaces the default gap after specific lines.
    pause_overrides = _parse_pause_after(
        args.pause_after, [e.get("index") for e in entries]
    )
    last_index = entries[-1].get("index")
    if last_index in pause_overrides:
        print(
            f"note: --pause-after {last_index} has no effect "
            "(no gap after the last line)",
            file=sys.stderr,
        )
    gap_frames = [0]  # silence before each segment; none before the first
    for pos in range(1, len(loaded)):
        after_index = loaded[pos - 1][0].get("index")
        if after_index in pause_overrides:
            ms = pause_overrides[after_index]
        else:
            changed = loaded[pos][0].get("voice") != loaded[pos - 1][0].get("voice")
            ms = args.speaker_pause_ms if changed else args.pause_ms
        gap_frames.append(round(ms * sample_rate / 1000))
    total_frames = sum(len(s) for _, _, s, _ in loaded) + sum(gap_frames)
    assembled = np.zeros(total_frames, dtype=np.int16)

    cursor = 0
    speaker_changes = 0
    timeline = []
    for pos, (entry, path, samples, gain) in enumerate(loaded):
        if pos > 0:
            changed = entry.get("voice") != loaded[pos - 1][0].get("voice")
            speaker_changes += int(changed)
            cursor += gap_frames[pos]  # zeros: the silence
        out_samples = samples if gain == 1.0 else _apply_gain(samples, gain)
        assembled[cursor : cursor + len(samples)] = out_samples
        cursor += len(samples)
        timeline.append(
            {
                "index": entry.get("index"),
                "voice": entry.get("voice"),
                "tone": entry.get("tone"),
                "file": str(path),
                "gap_before_s": round(gap_frames[pos] / sample_rate, 3),
                "start_s": round((cursor - len(samples)) / sample_rate, 3),
                "duration_s": round(len(samples) / sample_rate, 3),
                "gain": round(gain, 3),
            }
        )

    speech_s = round(sum(t["duration_s"] for t in timeline), 3)
    total_s = round(cursor / sample_rate, 3)
    silence_s = round(total_s - speech_s, 3)
    _print_timeline(timeline, speaker_changes, args.source)
    print(f"total: {speech_s:.2f}s speech + {silence_s:.2f}s silence = {total_s:.2f}s")
    if args.dry_run:
        print("dry run — no audio written")
        return


    _write_wav_mono16(output, sample_rate, assembled)
    print(f"wrote {output}")

    # Gate: the written file must equal Σ segments + Σ silences exactly.
    with wave.open(str(output)) as w:
        written_frames = w.getnframes()
        written_s = written_frames / w.getframerate()
    check = "PASS" if written_frames == cursor else "FAIL"
    print(
        f"duration arithmetic: written {written_s:.2f}s "
        f"vs expected {total_s:.2f}s — {check}"
    )
    if check != "PASS":
        _fail("assembled duration does not match the timeline")

    report = {
        "manifest": str(manifest_path),
        "script": manifest.get("script"),
        "source": args.source,
        "output": str(output),
        "pause_ms": args.pause_ms,
        "speaker_pause_ms": args.speaker_pause_ms,
        "pause_overrides_ms": {str(i): ms for i, ms in pause_overrides.items()},
        "normalize": not args.no_normalize,
        "target_rms": args.target_rms,
        "sample_rate": sample_rate,
        "speaker_changes": speaker_changes,
        "segments": timeline,
        "speech_s": speech_s,
        "silence_s": silence_s,
        "total_duration_s": total_s,
    }
    report_path = output.with_suffix(".report.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {report_path}")


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
        "--only",
        metavar="INDEX[,INDEX]",
        default=None,
        help="regenerate only these manifest line indexes, updating "
        "manifest.json in place (requires an existing manifest.json; Phase 9)",
    )
    p_script.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"model repo (default: {DEFAULT_MODEL})"
    )
    p_script.set_defaults(func=cmd_script)

    p_asm = sub.add_parser(
        "assemble",
        help="combine a script output dir's segments into one WAV (Phase 9)",
    )
    p_asm.add_argument(
        "--manifest",
        required=True,
        help="Phase 8 manifest.json path (the segment source of truth)",
    )
    p_asm.add_argument("--output", required=True, help="assembled output WAV path")
    p_asm.add_argument(
        "--source",
        choices=["final", "raw"],
        default="final",
        help="which per-line clips to assemble (default: final)",
    )
    p_asm.add_argument(
        "--pause-ms",
        type=int,
        default=DEFAULT_PAUSE_MS,
        help=f"silence between consecutive lines (default: {DEFAULT_PAUSE_MS})",
    )
    p_asm.add_argument(
        "--speaker-pause-ms",
        type=int,
        default=DEFAULT_SPEAKER_PAUSE_MS,
        help=f"longer silence on a voice change (default: {DEFAULT_SPEAKER_PAUSE_MS})",
    )
    p_asm.add_argument(
        "--pause-after",
        metavar="INDEX=MS[,INDEX=MS]",
        default=None,
        help="replace the default gap after these manifest line indexes "
        "(e.g. --pause-after 4=800 for a longer agent-handoff beat)",
    )
    p_asm.add_argument(
        "--target-rms",
        type=float,
        default=TARGET_RMS,
        help=f"per-segment RMS target for level matching (default: {TARGET_RMS})",
    )
    p_asm.add_argument(
        "--no-normalize",
        action="store_true",
        help="skip per-segment level matching",
    )
    p_asm.add_argument(
        "--dry-run",
        action="store_true",
        help="print the timeline (durations, silences, gains) without writing",
    )
    p_asm.set_defaults(func=cmd_assemble)

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

