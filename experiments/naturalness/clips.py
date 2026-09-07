"""Phase 5 evaluation set (DEVELOPMENT.md section 12) — single source of truth.

Shared by run_experiments.py (generation), trim_clips.py (leak trim for the
tagged emotional clips) and check_clips.py (whisper pronunciation check), so
the expected text for every clip lives in exactly one place.

Rules encoded here:

- Plain clone generations by default: §5 naturalness is about the voice
  itself, and tone control was already validated in Phase 4.
- The only tagged clips are the inherently-emotional lines where flat
  delivery would fail the test. Tags are the Phase-4-validated ones
  ([sad], [excited]); the third emotional line has no validated tag, so it
  uses NL direction — the Phase 3 fallback for under-delivering tags.
- One input = one line: mlx-audio splits the text on newlines and generates
  each line as a separate audio segment, so no clip may contain a newline.

The difficult-text lines cover the full §12 checklist: numbers, dates,
names, acronyms, technical terms, addresses, currency, abbreviations.
"""

PROMPT_SAD = "[sad]"
PROMPT_EXCITED = "[excited]"
PROMPT_CONCERN_NL = (
    "Speak with quiet concern, serious but calm and professional."
)

CLIPS = [
    # --- Normal conversation (§12) — plain clone ---
    {
        "name": "conv1",
        "category": "Normal conversation",
        "text": "Thank you for calling.",
        "prompt": None,
    },
    {
        "name": "conv2",
        "category": "Normal conversation",
        "text": "How can I help you today?",
        "prompt": None,
    },
    {
        "name": "conv3",
        "category": "Normal conversation",
        "text": "Let me check that for you.",
        "prompt": None,
    },
    # --- Questions (§12) — plain clone ---
    {
        "name": "q1",
        "category": "Questions",
        "text": "Could you please confirm your account number?",
        "prompt": None,
    },
    {
        "name": "q2",
        "category": "Questions",
        "text": "Would you like me to explain that again?",
        "prompt": None,
    },
    # --- Emotional speech (§12) — tagged, then leak-trimmed ---
    {
        "name": "emo1",
        "category": "Emotional speech",
        "text": "I'm really sorry about what happened.",
        "prompt": PROMPT_SAD,
    },
    {
        "name": "emo2",
        "category": "Emotional speech",
        "text": "That's fantastic news!",
        "prompt": PROMPT_EXCITED,
    },
    {
        "name": "emo3",
        "category": "Emotional speech",
        "text": "I'm afraid we have a problem.",
        "prompt": PROMPT_CONCERN_NL,
    },
    # --- Difficult text (§12) — plain clone; whisper checks pronunciation ---
    {
        "name": "diff1",
        "category": "Difficult text",
        "text": (
            "Your appointment is on March 3rd at 2:30 PM, "
            "in room 401B of the Beaumont Clinic."
        ),
        "prompt": None,
    },
    {
        "name": "diff2",
        "category": "Difficult text",
        "text": (
            "The total comes to $1,247.50, including the "
            "$19.99 monthly service fee."
        ),
        "prompt": None,
    },
    {
        "name": "diff3",
        "category": "Difficult text",
        "text": (
            "The API returned a 503 error, so the VPN tunnel to the NAS "
            "dropped during the HTTP upload."
        ),
        "prompt": None,
    },
    {
        "name": "diff4",
        "category": "Difficult text",
        "text": (
            "Mrs. O'Neill from 42 Hackney Blvd, Apt 7A, called about her "
            "Wi-Fi router, a Corvex XR-500."
        ),
        "prompt": None,
    },
    {
        "name": "diff5",
        "category": "Difficult text",
        "text": (
            "Call 555-0142 between 9 AM and 5 PM EST and ask for "
            "Dr. Vásquez about the Q3 report."
        ),
        "prompt": None,
    },
    # --- Long sentences (§12) — plain clone; does naturalness degrade? ---
    {
        "name": "long1",
        "category": "Long sentences",
        "text": (
            "Before we can process the refund, I'll need to verify a few "
            "details on your account, so please bear with me for just a "
            "moment. Once everything checks out, the money should appear "
            "on your card within three to five business days."
        ),
        "prompt": None,
    },
    {
        "name": "long2",
        "category": "Long sentences",
        "text": (
            "Thank you for your patience while I looked into this for you. "
            "I can see that the payment left your account on the twelfth, "
            "but our system never received the confirmation from the bank. "
            "I'll raise this with our payments team right now, and someone "
            "will call you back before the end of the day. In the meantime, "
            "please keep your reference number handy in case you need to "
            "contact us again."
        ),
        "prompt": None,
    },
]

CATEGORY_ORDER = [
    "Normal conversation",
    "Questions",
    "Emotional speech",
    "Difficult text",
    "Long sentences",
]

# Text actually sent to the model: prompt and text on the SAME line (mlx-audio
# newline-splitting — Phase 3/4 lesson).
def generate_text(clip: dict) -> str:
    if clip["prompt"] is None:
        return clip["text"]
    return f"{clip['prompt']} {clip['text']}"


# Name of the listening clip in audio/trimmed/: plain clips are copied
# through unchanged; tagged clips are trimmed and get the _trim suffix
# (Phase 4 convention).
def listening_name(clip: dict) -> str:
    return clip["name"] if clip["prompt"] is None else f"{clip['name']}_trim"
