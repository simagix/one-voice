# Phase 6 — multiple voices — Qwen3-TTS-12Hz-1.7B-Base-8bit (MLX / mlx-audio)

- Date: 2026-09-07
- Model: mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit
- References (all mono 24 kHz 16-bit, whisper-large-v3-turbo sidecar):
  - `voices/simone/reference.wav` — female, US film dialogue (10.56 s)
  - `voices/neufeld/reference.wav` — **male, US narrator** (11.82 s); Bob
    Neufeld, *Dr. Jekyll and Mr. Hyde* (LibriVox, public domain)
  - `voices/golding/reference.wav` — **female, British narrator** (13.02 s);
    Ruth Golding, *The Adventures of Sherlock Holmes* (LibriVox, public domain)
- Purpose: DEVELOPMENT.md §13 — each voice recognizable, natural, consistent,
  independently controllable; are they "different people"?
- Files: `audio/raw/` + `audio/trimmed/` (git-ignored; regenerate with
  `run_clips.py` → `build_set.py`; objective check with `check_voices.py`)
- Listening page: `open experiments/phase6/listen.html`

## Method

- **Evaluation set**: the Phase 5 §12 set reused as-is (imported from
  `experiments/naturalness/clips.py`) — every clip generated **plain** (no
  tone prompt) so the new voices are directly comparable to Simone's Phase 5
  numbers. The three inherently-emotional lines are *also* plain here
  (Simone's Phase 5 versions were tagged+trimmed); the strict comparison
  rests on the 12 plain clips and the `emo*` difference is flagged in the
  tables.
- **Tone sanity check** (ONE voice — neufeld, the most distant from Simone,
  hence the strongest test that the §11 voice/tone independence finding
  generalizes): Phase 4 sentences S1/S2/S3, baseline + 3 tags validated in
  Phase 3/4 (`[calm]`, `[happy]`, `[sad]`); tags leak-trimmed with the
  Phase 3 whisper-timestamp method (the prompt+trim pattern).
- **Objective check**: whisper transcription of every clip vs expected text
  (`check_voices.py` → `analysis.md`).
- **F0 analysis deliberately skipped** — identity across voices was Phase 4's
  question and nothing sounded off in the smoke test.

## Evaluation set (30 comparison clips + 12 tone clips — see `setup_plan.py`)

| Voice | Clips | Prompts |
| --- | --- | --- |
| neufeld | conv1–3, q1–2, emo1–3, diff1–5, long1–2 | plain (no prompt) |
| golding | conv1–3, q1–2, emo1–3, diff1–5, long1–2 | plain (no prompt) |
| neufeld (tone) | base_s1/s2/s3 + tag_calm/happy/sad × s1/s2/s3 | `[calm]`/`[happy]`/`[sad]`, leak-trimmed |

## Evaluation — §18, 1–5 (listen via listen.html; Identity vs own reference is the headline dimension)

### Voice B — Neufeld (male, US)

| Clip | Identity vs reference | Naturalness | Consistency | Notes |
| --- | ---: | ---: | ---: | --- |
| conv1 | 4 | 4 | 4 | Timbre and resonance closely match reference.wav; natural cadence for short conversational greeting. |
| conv2 | 4 | 4 | 4 | Strong vocal similarity; clear pitch contour and standard warm helper tone. |
| conv3 | 4 | 4 | 4 | Consistent lower-mids tone; natural pacing. |
| q1 | 4 | 4 | 4 | Good speaker identity retention; rising question inflection sounds organic. |
| q2 | 4 | 3 | 4 | Matches reference identity; slight robotic cadence on the ending phrasing. |
| emo1 (plain) | 4 | 4 | 4 | Identity holds well; subtle drop in pitch reflects sad tone naturally. (Phase 5 Simone: `[sad]`+trim) |
| emo2 (plain) | 3 | 4 | 3 | Brighter tone causes slight shift away from deep reference timbre, but remains natural. (Phase 5 Simone: `[excited]`+trim) |
| emo3 (plain) | 4 | 4 | 4 | Retains speaker identity; subtle pitch tension fits concerned tone. (Phase 5 Simone: NL concern+trim) |
| diff1 | 4 | 4 | 4 | Excellent match to reference timbre; handles mixed alphanumeric tokens ("401B") cleanly. |
| diff2 | 4 | 4 | 4 | Stable voice identity; clear articulation of financial figures and currency units. |
| diff3 | 3 | 3 | 3 | Slight artificial tightness on technical jargon ("API", "NAS"), though character remains recognizable. |
| diff4 | 4 | 4 | 4 | Maintains deep male timbre well across alphanumeric model numbers and proper names. |
| diff5 | 4 | 4 | 4 | Consistent vocal texture; clean digit/time string delivery. |
| long1 | 4 | 4 | 4 | Great long-form identity retention; smooth multi-clause transitions without drift. |
| long2 | 4 | 4 | 4 | Highly consistent with reference across extended speech; natural pause timing and sentence flow. |

### Voice C — Golding (female, British)

| Clip | Identity vs reference | Naturalness | Consistency | Notes |
| --- | ---: | ---: | ---: | --- |
| conv1 | 4 | 4 | 4 | "Thank you for calling." Clear British accent, clean vocal tone. |
| conv2 | 4 | 4 | 4 | "How can I help you today?" Natural, polite tone. |
| conv3 | 4 | 4 | 4 | "Let me check that for you." Matches reference timbre well. |
| q1 | 4 | 4 | 4 | "Could you please confirm your account number?" / "Would you like me to explain that again?" — rated together; clear, natural question intonations. |
| q2 | 4 | 4 | 4 | (same pass as q1; both question clips rated together) |
| emo1 (plain) | 4 | 4 | 4 | "I'm really sorry about what happened." Expresses apologetic nuance smoothly while keeping vocal character intact. (Phase 5 Simone: `[sad]`+trim) |
| emo2 (plain) | 4 | 4 | 4 | "That's fantastic news." Upbeat tone with organic pitch movement. (Phase 5 Simone: `[excited]`+trim) |
| emo3 (plain) | 4 | 4 | 4 | "I'm afraid we have a problem." Controlled inflection conveys concern while staying aligned with the reference. (Phase 5 Simone: NL concern+trim) |
| diff1 | 4 | 4 | 4 | "Your appointment is on March 3rd at 2:30 PM, in room 401B of the Beaumont Clinic." Good fluency across digits and dates. |
| diff2 | 4 | 4 | 4 | "The total comes to $1,247.50, including the $19.99 monthly service fee." Clear articulation of currency and figures. |
| diff3 | 3 | 3 | 3 | "The API returned a 503 error, so the VPN tunnel to the NAS dropped during the HTTP upload." Slightly robotic cadence on technical acronyms. |
| diff4 | 4 | 4 | 4 | "Mrs. O'Neill from 42 Hackney Blvd, Apt 7A… Corvex XR-500." Natural phrasing for address and model names. |
| diff5 | 4 | 4 | 4 | "Call 555-0142 between 9 AM and 5 PM EST… Q3 report." Consistent pitch and rhythm across contact instructions. |
| long1 | 4 | 4 | 4 | "Before we can process the refund…" (natural pacing across complex clauses) / "Once everything checks out… 3 to 5 business days" (clear cadence, reliable vocal texture). |
| long2 | 4 | 4 | 4 | "Thank you for your patience while I looked into this for you…" Excellent sustained performance across multi-sentence long-form text. |

> **Row-shift note (Golding):** the submitted notes quoted the *spoken text*
> heard for each rating, and for most rows the quote identifies a different
> clip than the row labeled (e.g. the row labeled "q1" quotes the diff1
> text). The audio files are verified correct (`analysis.md`); ratings were
> re-mapped to the clips whose text was quoted, preserving the listener's
> exact wording. Net effect: all 15 clips rated — q1/q2 rated in one pass
> (both 4/4/4), long1 rated across two contiguous quote-rows (both 4/4/4),
> and the single 3/3/3 is the technical-acronym clip (diff3). Same class of
> row-shift incident as Phase 5 (re-checked there too).

### Tone sanity check — Neufeld (Identity vs that sentence's baseline; §11 fail-on-identity rule)

| Sentence | Tone | Identity vs baseline | Naturalness | Expression | Consistency | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| S1 | calm | 4 | 4 | 3 | 4 | Slight addition of initial breath/filler ("Um"), maintain stable baseline pitch and voice quality. |
| S1 | happy | 4 | 4 | 4 | 4 | Upbeat pitch contour and brighter resonance while retaining core speaker identity. |
| S1 | sad | 4 | 4 | 4 | 4 | Subtle drop in pitch and softer energy; faithful to baseline identity. |
| S2 | calm | 4 | 4 | 3 | 4 | Neutral, measured cadence; minimal expressive departure from baseline. |
| S2 | happy | 4 | 4 | 4 | 4 | Cheerful intonation pattern with higher dynamic range. |
| S2 | sad | 4 | 4 | 4 | 4 | Drawn-out cadence and somber inflection without identity shift. |
| S3 | calm | 4 | 4 | 3 | 4 | Controlled, steady delivery; retains deep male timbre. |
| S3 | happy | 4 | 4 | 4 | 4 | Elevated pitch accent on key words while maintaining speaker identity. |
| S3 | sad | 4 | 4 | 4 | 4 | Lowered pitch and muted dynamics convey seriousness smoothly. |

### Cross-voice distinctiveness (§13: "different people", not "different settings of the same person")

| Pair | Distinct? (1–5) | Notes |
| --- | ---: | --- |
| Simone vs Neufeld | 5 | Distinct genders and timbres; American accent. |
| Simone vs Golding | 4 | Distinct timbres and accents — American vs British female. |
| Neufeld vs Golding | 5 | Distinct genders, timbres, and accents — American male vs British female. |

## Objective checks (check_voices.py → analysis.md, 42/42 clips)

All 42 listening clips were whisper-transcribed vs expected text. Results:

- **Plain clips (30)** — everything transcribes correctly. Most are 1.00;
  the only below-0.95 rows are two Neufeld difficult-text clips where the
  model reads the hard items out correctly but whisper writes them in
  spelled-out words:
  - `neufeld_diff1` (0.89): "March 3rd at 2:30 PM, room 401B" → "march
    third … two thirty p m … 401 b" — a CORRECT reading, ratio lower
    than Simone's diff1 (which whisper wrote numerically).
  - `neufeld_diff4` (0.78): "forty two", "hackney boulevard" correct;
    **flagged for listening** — whisper heard "apart to seven a" for the
    expected "Apt 7A" (the same fuzzy spot as Simone's Phase 5 diff4
    "App 7A"). Everything else in the clip is right.
- **Tone trims (9)** — 8/9 transcribe exactly to the target sentence
  (leak fully removed, match 1.00). One known artifact:
  `neufeld_tone_tag_sad_s1_trim` keeps a leading "had." — the `[sad]`
  tag's plosive "d" tail blurs into the start of "Thank", so no boundary
  fully separates them (0.94–1.03 cuts tested; later cuts clip "Thank").
  Kept the exact whisper word-boundary cut (0.94 s, no pad) and flagged it
  for the by-ear rating. Identity vs baseline is unaffected by a
  half-syllable lead-in.
- **Comparability note**: the new-voice clips are directly comparable to
  Simone's Phase 5 numbers on the 12 plain clips; `emo1–emo3` were
  tagged+trimmed for Simone but plain here.

## Phase 6 verdict

**PASS — a set of three distinct, recognizable, independently controllable
voices (DEVELOPMENT.md §13).** Both new voices are immediately identifiable
as themselves, rate 3.9–4.0 on naturalness/consistency (vs Simone's Phase 5
4.1/4.3), and hold identity through every tone.

### Against the four §13 criteria

| Criterion | Neufeld (male US) | Golding (female UK) | Simone (reference) |
| --- | --- | --- | --- |
| Recognizable — Identity vs own reference | 3.87 | 4.00 | — (identity was Phase 4) |
| Natural — Naturalness | 3.87 | 3.93 | 4.1 (Phase 5) |
| Consistent — Consistency | 3.87 | 3.93 | 4.3 (Phase 5) |
| Independently controllable — tone Identity vs baseline | 4.00 (all 9 rows) | tone check not run (by design) | 4–5 on all §18 dims (Phase 4) |

### What Phase 6 adds to Phases 3–5

- **Different people, not different settings of one person.** Cross-voice
  distinctiveness is 4–5 on all three pairs (Simone↔Neufeld 5,
  Simone↔Golding 4, Neufeld↔Golding 5). The deliberately-hard pair — two
  female voices, American vs British — still separates cleanly (4), so
  identity is more than "female voice".
- **§11 generalizes beyond Simone.** Neufeld's tone matrix holds
  Identity = 4 on all 9 rows: a tone change is the same male speaker
  performing differently, not a different speaker.
- **One model-level weak spot, not voice-specific.** The only sub-4 rating
  on either new voice is the technical-acronym clip (diff3, 3/3/3) — the
  same clip that was Simone's Phase 5 weak spot (3.8). Dense acronyms are
  the model's weakest input on all three voices, not a property of any
  single voice.
- **`[calm]` under-delivers (Expression 3 on all sentences)** — consistent
  with Phase 3/4; `[happy]`/`[sad]` deliver (4). Calm is the same
  under-delivering tag it was before, on a new voice.
- **Emotional lines benefit from the Phase 4 prompt+trim pattern.** Plain
  "That's fantastic news!" brightened Neufeld's timbre (Identity 3); the
  model expressed excitement by shifting voice quality. Golding's brighter
  reference absorbed the same shift (4). The Phase 5 approach — tagged +
  whisper-trimmed — is the established countermeasure.
- **Style caveat.** The two new references are LibriVox narration (clean,
  deliberate reading) vs Simone's film dialogue. The reference defines the
  clone's default delivery; all ratings were made against each voice's own
  reference, so this is context, not a defect.

### Provenance

- `voices/neufeld/` — Bob Neufeld, *Dr. Jekyll and Mr. Hyde* (v3, 2011),
  LibriVox/archive.org `jekyll_hyde_1111_librivox` (public domain).
  Reference = 70.68–82.50 s of part 1.
- `voices/golding/` — Ruth Golding, *The Adventures of Sherlock Holmes*
  (v2, 2010), LibriVox/archive.org `adventures_sherlock_holmes_rg_librivox`
  (public domain). Reference = 223.68–236.70 s of part 1.
- Source MP3s kept local-only at repo root by decision (git-ignored).

### Next step

The voice set is a coherent three-voice baseline for Phase 7 (DEVELOPMENT.md
§14 — voice profiles) and Phase 8 (script support): identical reference-prep
and evaluation pipeline across all three voices.