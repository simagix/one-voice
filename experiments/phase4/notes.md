# Phase 4 — voice + tone independence — Qwen3-TTS-12Hz-1.7B-Base-8bit (MLX / mlx-audio)

- Date: 2026-09-07
- Model: mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit
- Reference: voices/simone/reference.wav (mono 24kHz, 10.56s) + whisper-large-v3-turbo transcript — the SAME voice for every clip
- Purpose: verify that voice identity and tone can be controlled independently (DEVELOPMENT.md §11): the same sentences in several tones must sound like the **same person performing differently**, not like different speakers
- Files: audio/raw/*.wav and audio/trimmed/*.wav (git-ignored; regenerate with `run_experiments.py` then `trim_clips.py`)
- Listening page: `open experiments/phase4/listen.html` — per sentence, baseline first, then each tone

## Method (from the Phase 3 verdict)

Prompt + trim: the Base model speaks any style text aloud (in-band only), so
each tone clip is generated as `[tag] + sentence` (NL instruction for
sarcasm) and then trimmed to the target sentence with the Phase 3
whisper-timestamp method (`trim_clips.py`, reusing
`experiments/tone/trim_clips.py`). Baselines have no prompt and are copied
through untrimmed — they are the **identity anchor** for their sentence.

## Test sentences (identical to Phase 3)

- S1: "Thank you for calling. How may I help you today?"
- S2: "Well, that certainly went according to plan."
- S3: "I need you to listen to me."

## Tones under test

Tag prompts (preferred per Phase 3): `[calm]`, `[happy]`, `[sad]`,
`[angry]`, `[excited]`. NL prompt (fallback per Phase 3, tag under-delivered):
"Deliver the sentence with dry, understated sarcasm."

## Experiment matrix

| Name | Prompt | Tone | Text |
| --- | --- | --- | --- |
| base_s1 / base_s2 / base_s3 | none (baseline / identity anchor) | none | S1 / S2 / S3 |
| tag_calm_s1..s3 | `[calm] …` | calm | S1 / S2 / S3 |
| tag_happy_s1..s3 | `[happy] …` | happy | S1 / S2 / S3 |
| tag_sad_s1..s3 | `[sad] …` | sad | S1 / S2 / S3 |
| tag_angry_s1..s3 | `[angry] …` | angry | S1 / S2 / S3 |
| tag_excited_s1..s3 | `[excited] …` | excited | S1 / S2 / S3 |
| nl_sarcastic_s1..s3 | NL dry-sarcasm instruction | sarcastic | S1 / S2 / S3 |

21 clips total: 3 baselines + 18 tone clips. Raw clips in `audio/raw/`,
trimmed listening set in `audio/trimmed/` (see `trim_report.md` for cut
points/match ratios, `analysis.md` for transcripts + F0 drift).

## Evaluation — rate each tone AGAINST its sentence's baseline (§18, 1–5; listen via listen.html)

| Sentence | Tone | Identity vs baseline | Naturalness | Expression | Consistency | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | calm | 5 | 5 | 4 | 5 | Very subtle drop in energy; smooth, controlled cadence. |
| S1 | happy | 5 | 5 | 5 | 5 | Bright, smiling posture; warm and welcoming pitch inflection. |
| S1 | sad | 5 | 4 | 4 | 4 | Melancholic tone; slight reduction in breath support towards the end. |
| S1 | angry | 5 | 4 | 5 | 5 | Firm, assertive tone with sharp, deliberate articulation. |
| S1 | excited | 5 | 5 | 5 | 5 | High energy with dynamic range and upbeat cadence. |
| S1 | sarcastic | 5 | 4 | 4 | 4 | Dry, flat delivery with subtle ironic emphasis. |
| S2 | calm | 5 | 5 | 4 | 5 | Low-key, measured delivery matching the baseline voice persona well. |
| S2 | happy | 5 | 5 | 5 | 5 | Cheerful, upbeat tone that sounds genuine and warm. |
| S2 | sad | 5 | 4 | 4 | 4 | Melancholic inflection with drawn-out vowels and lowered pitch. |
| S2 | angry | 5 | 5 | 5 | 5 | Strained intensity with strong emphasis on "plan." |
| S2 | excited | 5 | 5 | 5 | 5 | Bright, enthusiastic pitch contour throughout. |
| S2 | sarcastic | 5 | 5 | 5 | 5 | Excellent dry, ironic inflection suited to the sentence meaning. |
| S3 | calm | 5 | 5 | 4 | 5 | Steady, gentle, and controlled vocal presentation. |
| S3 | happy | 5 | 4 | 4 | 4 | Warm and friendly tone, though slightly unusual context for the sentence phrase. |
| S3 | sad | 5 | 5 | 5 | 5 | Vulnerable, somber tone with a slight breathy strain. |
| S3 | angry | 5 | 5 | 5 | 5 | Strong, urgent imperative tone with heavy emphasis. |
| S3 | excited | 5 | 4 | 4 | 4 | High-pitched urgency that sounds energetic and intense. |
| S3 | sarcastic | 5 | 4 | 4 | 4 | Dismissive, flat delivery with dry cadence. |

Rating guide: **Identity vs baseline** — does the tone clip sound like the
same person as that sentence's baseline (5 = unmistakably the same person
performing differently; 1 = sounds like a different speaker)? Per §11, a
clip that fails Identity fails regardless of Expression.

## Objective checks (see `analysis.md`)

- Whisper transcription of every trimmed clip must be exactly the target
  sentence (leak fully removed, no garbling).
- Median F0 per tone clip vs its sentence's baseline (semitones) as a rough
  identity-drift proxy; Phase 3 showed 3–6 st shifts under strong tones.

## Observations

Objective checks (`analysis.md`, mlx-whisper transcription + median-F0 per
clip vs the Simone reference and vs the per-sentence baseline):

1. **Leak fully removed.** Every trimmed clip transcribes exactly to its
   target sentence (18/18 cut at match ratio 1.00, cut points 0.68–1.24 s
   for tags, 3.64–3.84 s for the NL sarcasm instruction; see
   `trim_report.md`).
2. **Pitch drift under tone direction, similar magnitude to Phase 3.**
   Most tone clips sit within ±3 st of their sentence's baseline
   (identity-friendly). Larger median shifts: sad_s1 +6.7 st,
   angry_s1 +7.0 st, happy_s2 +6.5 st, excited_s2 +6.2 st vs baseline.
   Outlier: tag_excited_s3 sits −12.9 st vs baseline (median 115 Hz) —
   either a genuinely low, pressed "excited" delivery on the short
   imperative or an F0-tracker artifact; flagged for listening.
3. Phase 3 precedent: 3–6 st shifts read as emotional inflection, not a
   different speaker — but §11 is the critical requirement, so the listening
   evaluation above is the ground truth.

Subjective (listening) evaluation: done — see the table above and the
verdict below.

## Phase 4 verdict (user listening, 18 tone clips vs their sentence baselines)

**PASS — voice identity and tone are controlled independently
(DEVELOPMENT.md §11 satisfied on the Base model via prompt + trim).**

- **Identity vs baseline: 5/5 on all 18 comparisons.** Every tone clip —
  calm, happy, sad, angry, excited, sarcastic, across all three sentences —
  was judged unmistakably the same person as its sentence's no-tone
  baseline, performing differently. The §11 fear that tone direction turns
  the clone into a different speaker is empirically retired; the Phase 3
  3–6 st F0 shifts read as emotional inflection, exactly as hypothesised.
- **Naturalness 4–5 (mean ≈ 4.6), Expression 4–5 (mean ≈ 4.5),
  Consistency 4–5 (mean ≈ 4.7).** No cell below 4 anywhere.
- Strongest tones: happy and angry (Expression 5 on S1/S2), excited
  (5 on S1/S2), sarcastic on its natural home S2 (5/5/5/5 — the NL sarcasm
  prompt + "certainly" is the best pairing in the whole matrix).
- Weakest (still 4s): calm Expression (subtle by design), sad breath
  support, and the semantically mismatched pairings happy/excited/sarcastic
  on S3 — a performance/fit issue, not an identity or naturalness failure.
- `tag_excited_s3` F0 outlier (−12.9 st, median 115 Hz) resolved: the clip
  was *heard* as high-pitched, energetic urgency (5/4/4/4), confirming the
  low F0 median was an autocorrelation tracker artifact (pressed/creaky
  voiced frames), not a real pitch drop or identity drift.

**Working pattern confirmed for OneVoice (Phase 3 + 4 combined):**
with a cloned reference voice,

    [tag] or NL instruction + target text  →  generate  →  whisper-timestamp
    trim  →  clip that is recognisably the reference speaker, delivered in
    the requested tone, rated 4–5 on all §18 dimensions

Next: commit experiments/phase4/ (awaiting explicit user approval), then
Phase 5 — Naturalness Evaluation (DEVELOPMENT.md §12).
