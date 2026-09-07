"""Phase 8 side-experiment: does mlx-audio's `instruct=` kwarg give
out-of-band tone control on the Qwen3-TTS-12Hz-1.7B-Base-8bit model?

Phases 3/4 established that tone direction must go in-band (tags / NL
directions are spoken aloud, then leak-trimmed). generate_audio() also
accepts an instruct=str parameter which our pipeline never used. This probe
generates ONE clip with a clean in-band text (no prompt) plus instruct=,
then whisper-transcribes it:

- transcript == target text  -> channel is leak-free (tone delivery still
  needs ears);
- transcript contains the instruction or is garbled -> instruct is not
  honoured by this Base model; the in-band prompt+trim pattern stays.

Usage: .venv/bin/python experiments/phase8/instruct_probe.py
"""

import shutil
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "audio"
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"
MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit"

TARGET = "Thank you for calling."
INSTRUCT = "Speak in a warm, friendly, welcoming way."


def normalize(s: str) -> str:
    return " ".join("".join(c for c in s.lower() if c.isalnum() or c == " ").split())


def main() -> None:
    import mlx_whisper
    from mlx_audio.tts.generate import generate_audio

    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / "instruct_probe.wav"
    ref = ROOT / "voices" / "simone" / "reference.wav"
    ref_text = ref.with_suffix(".txt").read_text(encoding="utf-8").strip()

    with tempfile.TemporaryDirectory() as tmp:
        generate_audio(
            text=TARGET,
            model=MODEL,
            voice=None,
            ref_audio=str(ref),
            ref_text=ref_text,
            instruct=INSTRUCT,
            output_path=tmp,
            file_prefix="probe",
            audio_format="wav",
            verbose=False,
        )
        produced = sorted(Path(tmp).glob("probe_*.wav"))
        if not produced:
            print("PROBE FAILED: model produced no audio")
            return
        shutil.move(str(produced[-1]), out_path)

    transcript = mlx_whisper.transcribe(
        str(out_path), path_or_hf_repo=WHISPER_MODEL
    )["text"].strip()
    ratio = SequenceMatcher(None, normalize(transcript), normalize(TARGET)).ratio()
    print(f"instruct:   {INSTRUCT!r}")
    print(f"target:     {TARGET!r}")
    print(f"transcript: {transcript!r}")
    print(f"match:      {ratio:.2f}")
    verdict = (
        "LEAK-FREE — instruct= did not leak into the audio"
        if ratio >= 0.9
        else "NOT leak-free / not honoured — keep the in-band prompt+trim pattern"
    )
    print(f"verdict:    {verdict}")


if __name__ == "__main__":
    main()
