# Phase 5 — naturalness evaluation — Qwen3-TTS-12Hz-1.7B-Base-8bit (MLX / mlx-audio)

- Date: 2026-09-07
- Model: mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit
- Reference: voices/simone/reference.wav (mono 24kHz, 10.56s) + whisper-large-v3-turbo transcript — the SAME voice for every clip
- Purpose: measure the default clone's **naturalness** on the repeatable evaluation set prescribed by DEVELOPMENT.md §12 (DEVELOPMENT.md §5: does it sound like a real person?)
- Files: audio/raw/*.wav and audio/trimmed/*.wav (git-ignored; regenerate with `run_experiments.py` then `trim_clips.py`, objective check with `check_clips.py`)
- Listening page: `open experiments/naturalness/listen.html` — grouped by §12 category

## Method

Plain clone generations by default: §5 naturalness is about the voice itself,
and tone control was already validated in Phase 4. The ONLY tagged clips are
the three inherently-emotional lines where flat delivery would fail the test:
`emo1` uses the Phase-4-validated `[sad]` tag, `emo2` `[excited]`, and `emo3`
(no validated tag exists) the Phase-3 NL-direction fallback. Tagged clips are
leak-trimmed with the Phase 3 whisper-timestamp method (trim_clips.py reusing
`experiments/tone/trim_clips.py`); plain clips are copied through unchanged.
One input = one line (mlx-audio splits on newlines).

Whisper transcription of every clip (check_clips.py → analysis.md) is the
objective pronunciation check: it caught every leak in Phase 3/4, and for the
difficult-text lines a mispronounced/garbled number, acronym or abbreviation
shows up as a wrong or missing word in the transcript.

## Evaluation set (15 clips — see clips.py for the single source of truth)

| Name | Category | Text / prompt |
| --- | --- | --- |
| conv1 | Normal conversation | "Thank you for calling." (plain) |
| conv2 | Normal conversation | "How can I help you today?" (plain) |
| conv3 | Normal conversation | "Let me check that for you." (plain) |
| q1 | Questions | "Could you please confirm your account number?" (plain) |
| q2 | Questions | "Would you like me to explain that again?" (plain) |
| emo1 | Emotional speech | `[sad] I'm really sorry about what happened.` → trimmed |
| emo2 | Emotional speech | `[excited] That's fantastic news!` → trimmed |
| emo3 | Emotional speech | NL: "Speak with quiet concern, serious but calm and professional." + "I'm afraid we have a problem." → trimmed |
| diff1 | Difficult text | numbers, date, time, room — "Your appointment is on March 3rd at 2:30 PM, in room 401B of the Beaumont Clinic." (plain) |
| diff2 | Difficult text | currency, decimals — "The total comes to $1,247.50, including the $19.99 monthly service fee." (plain) |
| diff3 | Difficult text | acronyms, technical terms — "The API returned a 503 error, so the VPN tunnel to the NAS dropped during the HTTP upload." (plain) |
| diff4 | Difficult text | names, address, abbreviations — "Mrs. O'Neill from 42 Hackney Blvd, Apt 7A, called about her Wi-Fi router, a Corvex XR-500." (plain) |
| diff5 | Difficult text | phone, hours, title, ordinal — "Call 555-0142 between 9 AM and 5 PM EST and ask for Dr. Vásquez about the Q3 report." (plain) |
| long1 | Long sentences | ~2 sentences / ~44 words (plain) |
| long2 | Long sentences | ~4 sentences / ~66 words (plain) |

## Evaluation — §18, 1–5 (listen via listen.html; Naturalness is the headline dimension)

**Complete — all 15 clips rated by listening (2026-09-07).** (An earlier
session returned a row-shifted table and 5 "missing" clips; both were
re-checked — every note below was verified against the clip's actual text,
and the five "missing" clips turned out to be a playback hiccup, not
missing audio. The corrected, complete set is recorded here.)

| Clip | Category | Naturalness | Pronunciation | Consistency | Notes |
| --- | --- | ---: | --- | ---: | --- |
| conv1 | Normal conversation | 4.2 | — | 4.3 | Clear, steady tone on "Thank you for calling". Smooth pause and pitch contour. |
| conv2 | Normal conversation | 4.1 | — | 4.2 | Natural question intonation on "How can I help you today?". |
| conv3 | Normal conversation | 4.3 | — | 4.4 | Smooth delivery on "Let me check that for you." Natural decay at sentence end. |
| q1 | Questions | 4.3 | — | 4.4 | Short, direct prompt; clear rising question cadence on "confirm your account number". |
| q2 | Questions | 4.2 | — | 4.4 | Natural, polite question tone; smooth ending tilt on "explain that again". |
| emo1 | Emotional speech | 4.2 | — | 4.3 | Clean apologetic tone on "I'm really sorry about what happened." |
| emo2 | Emotional speech | 4.4 | — | 4.5 | Warm, enthusiastic inflection on "That's fantastic news!" |
| emo3 | Emotional speech | 4.1 | — | 4.3 | Empathetic, cautious tone on "I'm afraid we have a problem." |
| diff1 | Difficult text | 4.1 | No errors | 4.2 | Accurately renders date, time, room "401B", and "Beaumont Clinic" with natural pauses. |
| diff2 | Difficult text | 3.9 | No errors | 4.0 | Handles "$1,247.50" and "$19.99" clearly; slightly robotic cadence on transitions. |
| diff3 | Difficult text | 3.8 | Minor robotic inflection on "503" & "NAS" | 4.0 | Fast pace on "API", "503", "VPN", "NAS", and "HTTP"; slightly compressed phrasing. |
| diff4 | Difficult text | 4.2 | No errors | 4.3 | Clear pronunciation of "Mrs. O'Neill", "Hackney Boulevard", "Apt 7A", and "Corvex XR500". |
| diff5 | Difficult text | 4.0 | Slight rush on "EST" | 4.1 | Clean phone number digits ("555-0142") and names ("Dr. Vasquez", "Q3 report"). |
| long1 | Long sentences | 4.2 | No errors | 4.3 | Natural pauses across multi-clause structure ("Before we can process the refund..."); clean handling of "3 to 5 business days". |
| long2 | Long sentences | 4.0 | No errors | 4.2 | Smooth transitions across complex clauses ("Thank you for your patience..."); natural rendering of ordinal "12th". Mild tail-off toward the end. |

Pronunciation: on the difficult-text lines, note any mispronounced or garbled
item (numbers, dates, acronyms, currency, abbreviations). Cross-check against
the whisper transcripts in `analysis.md` — a wrong reading shows up there as
a wrong or missing word.

Rating anchors (§5): 5 = would pass as a real person; 4 = clearly synthetic
on close listening but pleasant; 3 = noticeable robotic artifacts; 2 = mostly
robotic; 1 = fails.

## Summary (15/15 rated)

| Category | Naturalness (mean) | Consistency (mean) |
| --- | ---: | ---: |
| Normal conversation | 4.2 | 4.3 |
| Questions | 4.3 | 4.4 |
| Emotional speech | 4.2 | 4.4 |
| Difficult text | 4.0 | 4.1 |
| Long sentences | 4.1 | 4.3 |
| **Overall** | **4.1** (range 3.8–4.4) | **4.3** (range 4.0–4.5) |

- **Naturalness is solid across the board**: no clip below 3.8; every clip
  is "clearly synthetic only on close listening" or better. Simple short
  lines and questions are the strongest material (4.2–4.3); dense technical
  strings the weakest.
- **Pronunciation: no misreadings anywhere.** The only flags are
  delivery-quality — robotic inflection on "503"/"NAS" (diff3) and a slight
  rush on "EST" (diff5). The whisper pass and the ear agree: all numbers,
  dates, currency, acronyms, addresses and names are rendered correctly
  (whisper spelling differences like "2.30pm"/"XR500"/"Boulevard" are
  orthography, not mispronunciation).
- **Long-sentence degradation is real but mild**: long1 (2 sentences,
  12.7 s) holds at 4.2 — on par with short lines — while long2 (4
  sentences, 18.6 s) drops to 4.0 with a "mild tail-off toward the end".
  Consistency stays high on both (4.3/4.2). Roughly −0.2 naturalness at
  the ~66-word input.
- **Interesting cross-phase note**: the plain default delivery (this
  phase, mean 4.1) rates slightly below the tone-directed clips of Phase 4
  (mean ≈ 4.6). Emotional/toned delivery seems to *help* naturalness on
  this model; flat default lines are where robotic artifacts peek through.
- **Weakest clip: diff3 (3.8)** — rapid acronym/technical strings compress
  the phrasing. A naturalness issue, not pronunciation.

## Objective checks

- Whisper transcript of every clip vs expected text: see `analysis.md`
  (similarity ratio is a rough pointer; the transcript column is the check —
  numbers/currency are legitimately spelled out in words).
- Trimmed emotional clips must transcribe exactly to their target sentence
  (leak fully removed): see `trim_report.md`.
- F0 analysis deliberately skipped — this phase measures naturalness, not
  identity (identity was Phase 4's question).

### Pre-listening transcript review (analysis.md, 2026-09-07)

All 15 clips transcribe essentially correctly (similarity 0.95–1.00, and
every delta explained below). No garbling or truncation anywhere, including
the 12.7 s / 18.6 s long clips.

- conv1–conv3, q1–q2, emo1–emo3: exact matches (1.00). The three trimmed
  emotional clips re-transcribe exactly to their target sentences — leak
  fully removed (cut points 1.02–4.54 s, match 1.00, see `trim_report.md`).
- diff1: correct — "March 3rd", "2:30 PM" (transcript writes "2.30pm"),
  "room 401B" all read correctly.
- diff2: correct — both currency amounts read correctly (whisper even
  writes "$1,247.50" / "$19.99" numerically).
- diff3: correct — every acronym/technical term read properly (API, 503,
  VPN, NAS, HTTP).
- diff4: mostly correct — "Hackney Blvd" spoken as "Boulevard", "XR-500"
  read correctly (transcript writes "XR500"). **Flagged for listening:**
  whisper heard "App 7A" (expected "Apt 7A") and "O'Neil" (one l) — could be
  whisper spelling, could be a real mispronunciation.
- diff5: mostly correct — "555-0142", "Q3" correct. **Flagged for
  listening:** whisper wrote "Vasquez" without the accent (likely just
  whisper orthography, but check the pronunciation by ear).
- long1 / long2: no garbling, no lost sentences; "three to five" and
  "the twelfth" read correctly (whisper normalizes to "3 to 5" / "12th").
  Whether naturalness degrades with length is the listening question.

## Phase 5 verdict (user listening, 15/15 clips)

**PASS — the Simone clone's default delivery is natural enough for the
prototype (DEVELOPMENT.md §5/§12 satisfied; §21 criterion 3 met).**

- **Naturalness mean 4.1 (range 3.8–4.4), Consistency mean 4.3
  (4.0–4.5), pronunciation errors: none.** Nothing feels like
  "conventional robotic TTS" at first listen; artifacts appear only under
  close listening, and mostly on dense technical strings.
- The repeatable §12 evaluation set is in place (clips.py) and can be
  re-generated and re-rated after any model/pipeline change — the
  comparison baseline for future phases.
- Weak spots identified, both narrow: (1) dense acronym/technical strings
  (diff3, 3.8 — compressed phrasing, robotic inflection on "503"/"NAS");
  (2) mild tail-off at the longest inputs (long2, 4.0 at ~66 words vs 4.2
  at short/medium lengths).
- Actionable follow-up for the production pipeline (later phase, not
  now): mlx-audio splits on newlines, so chunking long text into
  sentence-per-line segments and concatenating the audio should avoid the
  long2 tail-off entirely — worth an experiment before Phase 6/7 builds on
  long-form generation.
- Cross-phase observation: tone-directed clips rated higher for
  naturalness (Phase 4 mean ≈ 4.6) than flat default delivery (4.1 here) —
  expressive delivery appears to mask the model's synthetic artifacts; the
  confirmed Phase 3/4 prompt+trim pattern may be worth applying beyond
  emotional lines.

Next: commit experiments/naturalness/ (awaiting explicit user approval),
then Phase 6 — Multiple Voices (DEVELOPMENT.md §13) or the long-form
chunking experiment, per user direction.
