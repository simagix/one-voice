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

# Voice cloning from a reference recording
# (transcript is read from voices/simone/reference.txt; override with --ref-text)
.venv/bin/python one_voice.py clone \
    --reference voices/simone/reference.wav \
    --text "Thank you for calling." \
    --output output/simone.wav

.venv/bin/python one_voice.py --version
.venv/bin/python one_voice.py --help
```

Both commands accept `--model` to override the default model
(`mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit`).

## Repository layout

```text
one_voice.py            CLI entry point (generate / clone / --version)
voices/<name>/          reference recordings + transcripts (reference.wav / reference.txt)
experiments/            model and prompt experiments (see notes.md in each)
DEVELOPMENT.md          project plan, phases and evaluation criteria
development.log         chronological log of what was done (install/config reference)
VERSION                 current version
```

## Status

Phase 2 (voice cloning) works: the same 1.7B model generates plain speech and
clones a reference speaker in ~5 s per sentence on an M1 Pro. Next phases:
tone/expression control, more reference voices, voice profiles. See
DEVELOPMENT.md for what is deliberately **not** built yet.
