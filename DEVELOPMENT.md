# OneVoice — Development Plan

## 1. Project Goal

OneVoice is an experimental local text-to-speech project using Qwen-TTS.

The goal is to determine whether Qwen-TTS can produce **natural, consistent, customer-quality voices** from text while allowing the voice identity and speaking style to be controlled independently.

The project has three primary goals:

1. **Voice Cloning** — preserve the vocal character of a reference speaker.
2. **Voice Direction** — control how the voice speaks using emotions, tones, and natural-language descriptions.
3. **Natural Speech** — produce speech that sounds human and conversational rather than robotic or synthetic.

The project should be developed incrementally. Each phase should produce something that can be tested by listening to actual generated audio.

---

## 2. Core Concept

OneVoice separates:

```text
VOICE = Who is speaking?
TONE  = How are they speaking?
TEXT  = What are they saying?
```

For example:

```text
Voice: Professional female voice
Tone:  Calm, friendly, confident
Text:  "Thank you for calling. How may I help you today?"
```

The same voice should be able to say the same text in different ways:

```text
calm
happy
angry
frustrated
excited
sad
professional
friendly
sarcastic
deadpan
```

Voice identity should remain stable while the performance changes.

---

## 3. Primary Requirements

### 3.1 Voice Cloning

Given a WAV recording of a person speaking, OneVoice should be able to generate new speech using the vocal characteristics of that person.

Example:

```text
Reference recording
        ↓
     Voice A
        ↓
"Thank you for calling."
```

The generated speech should sound recognizably like the reference speaker.

#### Questions to investigate

* How much reference audio is required?
* What recording quality is required?
* How accurately does Qwen-TTS preserve speaker identity?
* Does reference length affect quality?
* How consistent is the cloned voice across multiple generations?
* How does the voice behave with different emotions and speaking styles?

---

## 4. Voice Direction

Voice identity alone is not sufficient.

OneVoice must be able to control the **performance** of a voice.

The initial experiments should investigate both simple tags and natural-language instructions.

### Simple tags

```text
[happy]
Thank you for calling.

[angry]
I have already explained this three times.

[calm]
Let me help you resolve this issue.

[sarcastic]
Well, that certainly went according to plan.
```

### Natural-language instructions

```text
Speak in a calm, professional and reassuring manner.

Sound frustrated and impatient, but remain controlled.

Deliver the sentence with dry, understated sarcasm.

Sound genuinely excited and enthusiastic.
```

The project should determine which approach produces the most reliable results.

---

## 5. Naturalness

Natural speech is a **core requirement**, not an optional enhancement.

Generated speech should:

* sound human
* have natural rhythm
* use appropriate pauses
* have natural emphasis
* vary intonation appropriately
* avoid monotonous delivery
* avoid robotic pronunciation
* avoid unnatural pauses
* avoid obvious artifacts

A technically successful generation is not necessarily a successful result.

The final test is:

> Would a customer believe this is a real person speaking?

---

## 6. Development Philosophy

### 6.1 Listen before building

TTS quality is ultimately judged by listening.

Do not build complicated infrastructure before determining whether the underlying model produces satisfactory speech.

Every major phase should produce audio that can be evaluated.

### 6.2 Experiment first

When investigating a capability, create small experiments rather than immediately turning the idea into production architecture.

For example, to investigate tone:

```text
Voice
  ├── neutral.wav
  ├── happy.wav
  ├── angry.wav
  ├── calm.wav
  └── sarcastic.wav
```

Listen to the results and compare them.

Keep useful experiments so they can be reproduced later.

### 6.3 Keep the project small

This is an experimental project.

Do not introduce unnecessary:

* databases
* web servers
* GUIs
* APIs
* cloud infrastructure
* authentication
* multi-user architecture
* complex frameworks

The initial project should be a simple local tool.

---

## 7. Target Platform

The primary development platform is:

* macOS
* Apple Silicon
* Python
* local inference
* MLX where appropriate

Apple Silicon performance should be considered when selecting the Qwen-TTS implementation.

Do not optimize for CUDA/Linux unless explicitly required.

---

## 8. Phase 1 — Basic Text-to-Speech

### Objective

Prove that Qwen-TTS can generate good-quality speech locally.

Start with the simplest possible workflow:

```text
Text
  ↓
Qwen-TTS
  ↓
WAV
```

Example:

```bash
onevoice generate \
    --text "Thank you for calling. How may I help you today?" \
    --output output/test.wav
```

### Acceptance criteria

The system must:

* load the model locally
* generate speech successfully
* save a playable WAV file
* produce intelligible speech
* produce reasonably natural speech

### Important checkpoint

**Stop and listen to the generated audio before proceeding.**

If the base TTS output is not satisfactory, investigate the model and implementation before building additional functionality.

---

## 9. Phase 2 — Voice Cloning

### Objective

Add the ability to use a reference WAV recording to create new speech with the characteristics of the reference speaker.

Example:

```bash
onevoice clone \
    --reference voices/person1/reference.wav \
    --text "Thank you for calling." \
    --output output/person1.wav
```

Investigate:

* reference duration
* recording quality
* speaker similarity
* pronunciation
* consistency
* generation speed

Generate multiple sentences using the same reference.

The voice should remain recognizable across all of them.

---

## 10. Phase 3 — Tone and Expression

### Objective

Determine how effectively Qwen-TTS can control speaking style.

Begin with a small set of tones:

```text
neutral
happy
sad
angry
calm
excited
frustrated
friendly
professional
sarcastic
deadpan
```

Do not assume these labels will work equally well.

Test several prompt styles.

### Experiment A — Simple tag

```text
[angry]
I need you to listen to me.
```

### Experiment B — Natural-language instruction

```text
Speak with controlled anger. Sound frustrated and firm,
but remain professional.
```

### Experiment C — Detailed performance direction

```text
Deliver this with controlled frustration.
Speak firmly and slightly faster.
Emphasize "need" and "listen".
Do not shout.
```

Compare the results.

The goal is to discover what gives the most reliable control.

---

## 11. Phase 4 — Voice + Tone

### Objective

Verify that voice identity and tone can be controlled independently.

For example:

```text
              Voice A
                 │
       ┌─────────┼─────────┐
       │         │         │
     Calm      Happy     Angry
       │         │         │
       ▼         ▼         ▼
    Audio A    Audio B   Audio C
```

The three recordings should sound like the **same person performing differently**.

This is a critical OneVoice requirement.

A tone change should not unintentionally change the speaker's identity.

---

## 12. Phase 5 — Naturalness Evaluation

Create a repeatable evaluation set.

The test set should include:

### Normal conversation

```text
Thank you for calling.
How can I help you today?
Let me check that for you.
```

### Questions

```text
Could you please confirm your account number?
Would you like me to explain that again?
```

### Emotional speech

```text
I'm really sorry about what happened.
That's fantastic news!
I'm afraid we have a problem.
```

### Difficult text

Include:

* numbers
* dates
* names
* acronyms
* technical terms
* addresses
* currency
* abbreviations

### Long sentences

Test whether naturalness deteriorates as the input becomes longer.

---

## 13. Phase 6 — Multiple Voices

Once cloning works reliably, create several reference voices.

Example:

```text
voices/
├── voice-a/
│   └── reference.wav
├── voice-b/
│   └── reference.wav
└── voice-c/
    └── reference.wav
```

Test whether each voice remains:

* recognizable
* natural
* consistent
* independently controllable

The goal is not necessarily to find one perfect voice.

OneVoice should eventually be capable of maintaining a **set of high-quality approved voices**.

---

## 14. Phase 7 — Voice Profiles

Once the underlying experiments are successful, introduce reusable voice profiles.

Example:

```text
voices/
└── voice-a/
    ├── reference.wav
    └── voice.yaml
```

Possible configuration:

```yaml
name: Voice A
reference: reference.wav
description: Professional, friendly female voice
```

Do not over-design the configuration format at this stage.

Only add fields that are actually needed.

---

## 15. Phase 8 — Script Support

After individual voice generation works well, support simple scripts.

Example:

```text
[Voice A | friendly]
Thank you for calling.

[Voice A | professional]
Let me look into that for you.

[Voice A | reassuring]
I'll make sure we get this resolved.
```

The parser should identify:

```text
voice
tone
text
```

and generate each line independently.

---

## 16. Phase 9 — Audio Assembly

Combine generated lines into a single recording.

The system should eventually support:

* configurable pauses
* natural transitions
* silence between speakers
* basic volume normalization
* WAV output

Individual generated segments should be preserved.

If one sentence is bad, it should be possible to regenerate that sentence without regenerating the entire recording.

---

## 17. Phase 10 — Call-Center Experiment

Only after the voice-generation technology is working should the project investigate the original OneVoice use case.

The conceptual workflow is:

```text
Call-center worker
        │
        ▼
     Speech
        │
        ▼
 Voice transformation
        │
        ▼
Approved OneVoice
        │
        ▼
     Customer
```

The purpose is to provide customers with a **consistent, clear and natural voice experience**, while allowing different workers to use different approved voices.

The objective is not to eliminate the worker's identity or personality.

The objective is to make the customer-facing speech:

* clear
* natural
* understandable
* professional
* consistent

Real-time speech-to-speech conversion should be treated as a later research phase.

Do not build the real-time call-center system during the initial TTS experiments.

---

## 18. Evaluation Criteria

Each phase should be evaluated against four major dimensions.

### Voice Identity

Does the generated speech sound like the reference speaker?

### Naturalness

Does it sound like a real person?

### Expression

Does the requested tone actually come through?

### Consistency

Can the system reproduce the same voice and style across many sentences?

A simple evaluation table can be maintained:

| Test      | Voice Identity | Naturalness | Expression | Consistency |
| --------- | -------------: | ----------: | ---------: | ----------: |
| Neutral   |                |             |            |             |
| Happy     |                |             |            |             |
| Angry     |                |             |            |             |
| Calm      |                |             |            |             |
| Sarcastic |                |             |            |             |

Use a 1–5 rating initially.

The ratings are subjective, but they provide a useful way to compare experiments.

---

## 19. Experiments Directory

Keep model and prompt experiments separate from production code.

Suggested structure:

```text
experiments/
├── basic-tts/
├── voice-cloning/
├── tone/
├── naturalness/
└── long-form/
```

Each experiment should record:

* model
* input text
* reference voice
* prompt/instruction
* relevant parameters
* output audio
* observations

The purpose is to make successful experiments reproducible.

---

## 20. What Not to Build Yet

Do not build the following until the underlying voice quality has been demonstrated:

* GUI
* web application
* real-time call integration
* SIP/VoIP integration
* telephony integration
* cloud deployment
* database
* authentication
* multi-user support
* automatic emotion detection
* automatic voice selection
* automatic quality scoring
* video generation
* lip synchronization

These may become valuable later, but they are not part of the initial research.

---

## 21. Success Criteria for the Prototype

The initial OneVoice prototype will be considered successful if it can demonstrate:

### 1. Voice cloning

A reference speaker can be used to generate new speech with convincing speaker similarity.

### 2. Tone control

The same voice can produce noticeably different performances based on tone or natural-language direction.

### 3. Naturalness

The resulting speech sounds sufficiently human that it does not immediately feel like conventional robotic TTS.

### 4. Consistency

The voice remains recognizable and natural across many different sentences and tones.

### 5. Reproducibility

Successful experiments can be repeated using the same model, voice, text, and instructions.

---

## 22. Development Rule

At every stage, ask:

> **Does this make the generated voice better?**

If the answer is no, do not add the complexity.

The primary product of OneVoice is not the Python code.

**The primary product is the quality of the voice.**