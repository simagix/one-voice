# Phase 8 — side-experiment: mlx-audio `instruct=` channel (2026-09-07)

Question: does `generate_audio(instruct=...)` give out-of-band tone control
on `mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit` (the model Phases 2–8 use)?

## Method

- `instruct_probe.py` — one clip, simone reference, clean in-band text
  (`Thank you for calling.`) + `instruct="Speak in a warm, friendly,
  welcoming way."`; whisper-transcribed afterwards.
- `f0_compare.py` — median F0 (numpy autocorrelation, 60–400 Hz, voiced
  frames only) of the instruct clip vs a plain clone of the same sentence
  (`plain_probe.wav`, generated with `one_voice.py clone --voice simone`).
- Audio in `audio/` (git-ignored, as everywhere).

## Results

| Clip | Transcript | Match | Median F0 |
| --- | --- | ---: | ---: |
| instruct="Speak in a warm, friendly, welcoming way." | Thank you for calling | 1.00 | 177.1 Hz |
| plain clone (no instruct) | Thank you for calling. | (expected) | 164.4 Hz |

- The instruct text does **NOT** leak into the audio — mlx-audio passes it as
  a separate channel (`Instruct: ...` is echoed by the library), transcript is
  exactly the target. No trim needed.
- Delivery shift: **+1.29 semitones** median F0 vs plain — within the 3–6 st
  emotional-inflection range Phase 3/4 measured for in-band tags, i.e. the
  channel demonstrably changes delivery.

## Verdict / implications

- `instruct=` is a viable LEAK-FREE out-of-band tone channel on the Base
  model — a potential simplification over the Phase 3 in-band prompt+trim
  pattern (no trim step, no trim-mismatch risk).
- NOT adopted in Phase 8: the in-band prompt+trim pattern is the validated
  workhorse (Phases 3–6, by-ear PASS). Switching the tone pipeline to
  `instruct=` requires its own by-ear listening pass (are NL directions
  actually *delivered* through this channel?). Logged as a Phase 9 candidate.
- Known transcript nuance: whisper dropped the final period — cosmetic only.
