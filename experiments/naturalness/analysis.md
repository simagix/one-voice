# Phase 5 — objective checks (whisper transcription of every clip)

`Similarity` is a rough normalized-text ratio: 1.00 = transcript matches the written text word-for-word. Difficult-text lines legitimately score lower (the model spells numbers/currency out in words) — read the transcript column to judge the actual pronunciation.

| Clip | Dur (s) | Similarity | Expected text | Transcript |
| --- | ---: | ---: | --- | --- |
| conv1 | 1.1 | 1.00 | Thank you for calling. | Thank you for calling. |
| conv2 | 1.5 | 1.00 | How can I help you today? | How can I help you today? |
| conv3 | 2.2 | 1.00 | Let me check that for you. | Let me check that for you. |
| q1 | 2.6 | 1.00 | Could you please confirm your account number? | Could you please confirm your account number? |
| q2 | 2.0 | 1.00 | Would you like me to explain that again? | Would you like me to explain that again? |
| emo1_trim | 2.0 | 1.00 | I'm really sorry about what happened. | I'm really sorry about what happened. |
| emo2_trim | 2.0 | 1.00 | That's fantastic news! | That's fantastic news. |
| emo3_trim | 1.9 | 1.00 | I'm afraid we have a problem. | I'm afraid we have a problem. |
| diff1 | 5.6 | 0.99 | Your appointment is on March 3rd at 2:30 PM, in room 401B of the Beaumont Clinic. | Your appointment is on March 3rd at 2.30pm in room 401B of the Beaumont Clinic. |
| diff2 | 8.0 | 1.00 | The total comes to $1,247.50, including the $19.99 monthly service fee. | The total comes to $1,247.50, including the $19.99 monthly service fee. |
| diff3 | 6.2 | 1.00 | The API returned a 503 error, so the VPN tunnel to the NAS dropped during the HTTP upload. | The API returned a 503 error, so the VPN tunnel to the NAS dropped during the HTTP upload. |
| diff4 | 7.8 | 0.95 | Mrs. O'Neill from 42 Hackney Blvd, Apt 7A, called about her Wi-Fi router, a Corvex XR-500. | Mrs. O'Neil from 42 Hackney Boulevard, App 7A, called about her Wi-Fi router, a Corvex XR500. |
| diff5 | 8.7 | 0.99 | Call 555-0142 between 9 AM and 5 PM EST and ask for Dr. Vásquez about the Q3 report. | Call 555-0142 between 9 a.m. and 5 p.m. EST and ask for Dr. Vasquez about the Q3 report. |
| long1 | 12.7 | 0.97 | Before we can process the refund, I'll need to verify a few details on your account, so please bear with me for just a moment. Once everything checks out, the money should appear on your card within three to five business days. | Before we can process the refund, I'll need to verify a few details on your account. So please bear with me for just a moment. Once everything checks out, the money should appear on your card within 3 to 5 business days. |
| long2 | 18.6 | 0.99 | Thank you for your patience while I looked into this for you. I can see that the payment left your account on the twelfth, but our system never received the confirmation from the bank. I'll raise this with our payments team right now, and someone will call you back before the end of the day. In the meantime, please keep your reference number handy in case you need to contact us again. | Thank you for your patience while I looked into this for you. I can see that the payment left your account on the 12th, but our system never received the confirmation from the bank. I'll raise this with our payments team right now, and someone will call you back before the end of the day. In the meantime, please keep your reference number handy in case you need to contact us again. |
