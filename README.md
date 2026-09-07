# OneVoice

Experimental local text-to-speech on Apple Silicon using [Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base)
and [MLX](https://github.com/ml-explore/mlx), with voice cloning from a short
reference recording.

The goal: natural, consistent, customer-quality voices where **who** is
speaking (voice), **how** they speak (tone), and **what** they say (text) are
controlled independently. See [DEVELOPMENT.md](DEVELOPMENT.md) for the full
plan and [development.log](development.log) for a chronological record of
setup, installation and configuration decisions.

## Requirements

- macOS on Apple Silicon
- Python 3.14 (other recent versions likely work)
- ~2.5 GB disk for the model (downloaded on first use, cached in `~/.cache/huggingface`)

## Setup

```bash
python -m venv .venv
.venv/bin/pip install mlx-audio mlx-whisper
```

## Usage

```bash
# Basic text-to-speech
.venv/bin/python one_voice.py generate \
    --text "Thank you for calling. How may I help you today?" \
    --output output/thanks.wav

# Voice cloning from a named profile (voices/<name>/voice.yaml — Phase 7)
.venv/bin/python one_voice.py voices                # list available profiles
.venv/bin/python one_voice.py clone \
    --voice simone \
    --text "Thank you for calling." \
    --output output/simone.wav

# ...or from an arbitrary reference WAV path (Phase 2 behaviour)
# (transcript is read from <reference>.txt sidecar; override with --ref-text)
.venv/bin/python one_voice.py clone \
    --reference voices/simone/reference.wav \
    --text "Thank you for calling." \
    --output output/simone.wav

# Script support (Phase 8): each block generates an independent WAV.
# Preview the plan without generating (rejects unknown voice/tone, malformed
# blocks, empty text) — recommended, since generation is ~5–9 s per line:
.venv/bin/python one_voice.py script \
    --file examples/callcenter.txt --output-dir output/script_callcenter --dry-run

# Generate: raw/ (untrimmed model output) + final/ (leak-trimmed) + manifest.json
# (per line: voice, tone, text, prompt, files, duration, trim + transcript match)
.venv/bin/python one_voice.py script \
    --file examples/callcenter.txt --output-dir output/script_callcenter

.venv/bin/python one_voice.py --version
.venv/bin/python one_voice.py --help
```

Both `generate`/`clone` and `script` accept `--model` to override the default
model (`mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit`).

### Script format

```text
# comments allowed
[voice]                  # plain clone, no tone
[voice | tone]           # tone: calm happy sad angry excited (validated tags)
                         #       friendly professional reassuring sarcastic (NL directions)
Spoken text, one or more lines (joined onto a single model input line).
```

Tone lines are generated with the prompt in-band on the same line as the text
and the leaked prompt audio is trimmed automatically (whisper word-timestamp
method, Phases 3–6). Every final clip is whisper-transcribed as an objective
gate; `manifest.json` records each line for selective regeneration (Phase 9).
`one_voice.py` is also import-safe — `parse_script` and the voice-profile
helpers can be used as an embedded module from other Python code.

## Repository layout

```text
one_voice.py            CLI entry point (generate / clone / script / voices / --version);
                        import-safe for embedded use (parse_script, voice-profile helpers)
examples/               example scripts for the `script` subcommand
voices/<name>/          reference recordings + transcripts (reference.wav / reference.txt)
                        + optional voice.yaml profile (name / reference / description)
experiments/            model and prompt experiments (see notes.md in each)
DEVELOPMENT.md          project plan, phases and evaluation criteria
development.log         chronological log of what was done (install/config reference)
VERSION                 current version
```

## Status

Phases 2–7 are complete and committed: voice cloning (`--reference`),
tone/expression control via prompt + whisper-timestamp trim, a repeatable
naturalness evaluation set, a three-voice set (Simone + the public-domain
LibriVox readers Neufeld and Golding), and named voice profiles
(`--voice <name>` / `one_voice.py voices`). Phase 8 adds script support
(`one_voice.py script`): per-line independent generation with optional tones,
raw/final preservation and a manifest. See DEVELOPMENT.md for what is
deliberately **not** built yet (audio assembly is Phase 9); `development.log`
records what was done and why.
