# Tone and expression experiment — Qwen3-TTS-12Hz-1.7B-Base-8bit (MLX / mlx-audio)

- Date: 2026-09-07
- Model: mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit
- Reference: voices/simone/reference.wav (mono 24kHz, 10.56s) + whisper-large-v3-turbo transcript
- Purpose: compare tone-control approaches on the same cloned voice (DEVELOPMENT.md §10)
- Files: audio/*.wav (git-ignored; regenerate with `run_experiments.py [--only base,a,b,c]`)
- Timing: see development.log

## How tone is passed

The Qwen3-TTS **Base** model has no separate style input (`instruct` in
mlx-audio 0.5.1 only applies to the CustomVoice/VoiceDesign variants). Tone
must be embedded in the text itself. Also note: mlx-audio splits text on
newlines and generates each line as a separate audio segment, so the tag or
instruction stays on the **same line** as the spoken text.

- Baseline: no direction at all — to hear whether the tone directions change
  anything at all beyond the default reading.
- A: simple tag prefix — `[happy] Thank you for calling. ...`
- B: natural-language instruction — `Speak in a calm, professional and
  reassuring manner. Thank you for calling. ...`
- C: detailed multi-aspect direction (pace, emphasis, pauses, do/don't) —
  still single-line.

## Test sentences (fixed across all approaches)

- S1: "Thank you for calling. How may I help you today?"
- S2: "Well, that certainly went according to plan."
- S3: "I need you to listen to me."

## Experiment matrix

| Name | Approach | Tone | Text |
| --- | --- | --- | --- |
| base_s1_thanks | baseline | none | S1 |
| base_s2_plan | baseline | none | S2 |
| base_s3_listen | baseline | none | S3 |
| a_tag_happy_s1 | tag | happy | S1 |
| a_tag_sad_s1 | tag | sad | S1 |
| a_tag_angry_s1 | tag | angry | S1 |
| a_tag_calm_s1 | tag | calm | S1 |
| a_tag_excited_s1 | tag | excited | S1 |
| a_tag_sarcastic_s1 | tag | sarcastic | S1 |
| a_tag_deadpan_s1 | tag | deadpan | S1 |
| a_tag_sarcastic_s2 | tag | sarcastic | S2 |
| b_nl_calm_s1 | NL | calm/professional/reassuring | S1 |
| b_nl_friendly_s1 | NL | warm/friendly/welcoming | S1 |
| b_nl_excited_s1 | NL | genuinely excited | S1 |
| b_nl_sad_s1 | NL | sad/apologetic | S1 |
| b_nl_sarcasm_s2 | NL | dry understated sarcasm | S2 |
| b_nl_frustrated_s3 | NL | frustrated but controlled | S3 |
| c_detail_frustration_s3 | detail | controlled frustration | S3 |
| c_detail_reassurance_s1 | detail | calm, slow, emphasis | S1 |
| c_detail_sarcasm_s2 | detail | deadpan sarcasm | S2 |

## Evaluation (DEVELOPMENT.md §18, 1–5; listen and fill in)
| Test | Voice Identity | Naturalness | Expression | Consistency | Notes |
| --- | --- | --- | --- | --- | --- |
| **Baseline** | 4 | 4 | 2 | 4 | Clean, neutral delivery; accurate Simone timbre without prompt leakage. Baseline Expression only 2 — the tone directions add a lot beyond the default reading. |
| **A: tag happy** | 4 | 2 | 4 | 4 | Spoke *"Happy"* out loud; target sentence delivered with bright, upbeat pitch and tempo.|
| **A: tag angry** | 4 | 2 | 4 | 4 | Spoke *"Angry"* out loud; target sentence delivered with sharp, tense, elevated cadence.|
| **A: tag sarcastic** | 4 | 2 | 3 | 4 | Spoke *"Sarcastic"* out loud; delivery slowed down with flatter, dry intonation.|
| **B: NL calm** | 4 | 1 | 3 | 3 | Spoke the full instruction *"Speak in a calm..."* out loud; target phrase was calm and measured.|
| **B: NL sarcasm** | 4 | 1 | 4 | 4 | Spoke *"Deliver the sentence with dry understated sarcasm..."* out loud; strong dry delivery on target phrase.|
| **C: detailed frustration** | 4 | 1 | 4 | 4 | Spoke full directive out loud; target phrase achieved crisp emphasis on *"need"* and *"listen"* without shouting.|
| **C: detailed sarcasm** | 4 | 1 | 4 | 4 | Spoke full directive out loud; flat pitch and drawn-out pacing on *"certainly"* matched requested deadpan style.|

## Observations

Objective checks (see `analysis.md`, from `analyze_clips.py`: mlx-whisper
transcription + median-F0 per clip vs the Simone reference and per-sentence
baselines):

1. **Tags AND instructions are spoken aloud.** Whisper transcribes the tag or
   instruction as part of every clip ("Angry. Thank you for calling...",
   "Sound warm, friendly and welcoming. Thank you for calling...", including
   all three detailed-direction clips). Confirmed by the ~2x durations: none
   of the three approaches is out-of-band on the Base model — everything in
   the text stream gets read.
2. **Pitch drift under tone direction.** Reference median F0 ≈ 224 Hz.
   Baselines sit +1 to +2.8 st above it; strong tones sit well below their
   own sentence's baseline: angry −5.0 st, sarcastic −5.9 st, and every B and
   C clip −2.9 to −4.6 st vs its baseline. A 3–6 st median shift is large and
   plausibly contributes to clips sounding like a different speaker.
3. Minor ASR quirks: "Saad" (sad tag), a few "?" where commas were expected.

Subjective (listening) evaluation — fill in the §18 table above; per
DEVELOPMENT.md §11 a tone change must not change speaker identity, so clips
that fail Voice Identity fail regardless of expression quality.

## Experiment 3b — trimming the leaked style text (`trim_clips.py`)

Since the leak is purely that the style text is spoken *first* (it precedes
the target sentence in every clip), the leaked audio can be cut off. This
script transcribes each clip with mlx-whisper `word_timestamps=True`, finds
the word boundary whose remaining transcript best matches the known target
sentence, and slices the audio there (−50 ms pad). Results (`trim_report.md`,
output in `audio/trimmed/`, git-ignored):

- All 20 clips cut with match ratio 1.00; re-transcription of every trimmed
  clip is exactly the target sentence.
- Tag clips lose ~0.6–1.4 s (the spoken tag), NL clips ~3.0–4.3 s (the
  instruction sentence), detailed clips ~7.4–7.9 s (the full directive).

## 3b verdict (user listening, raw vs trimmed pairs)

Compared `a_tag_angry_s1`, `b_nl_sarcasm_s2`, `c_detail_frustration_s3`
against their trimmed versions:

1. **Tone survives the cut.** Anger keeps its elevated pitch/tense pacing,
   sarcasm keeps the slow dry cadence, the detailed frustration direction
   keeps its crisp emphasis on "need"/"listen" — removing the spoken prefix
   does not alter the remaining waveform (it is a pure leading-segment cut).
2. **Identity survives the cut.** Trimmed clips retain the Simone timbre;
   the pitch shifts read as emotional inflection, not a different speaker.

**Conclusion — Phase 3 complete.** Qwen3-TTS Base supports tone control only
in-band (the style text is spoken), but the leak is fully removable in
post-processing. The working pattern for OneVoice is:

    tag or NL instruction + target text  →  generate  →  whisper-timestamp
    trim (trim_clips.py)  →  clean, tone-controlled, Simone-voiced clip

Tags are the better prompt format for this pipeline: equal Expression to NL
(4 vs 4 on happy/angry; NL sarcasm 4 vs tag 3) with ~3–6x less leaked audio
to cut (0.6–1.4 s vs 3.0–4.3 s). NL/detailed direction is the fallback when
a tag under-delivers (e.g. sarcasm).



