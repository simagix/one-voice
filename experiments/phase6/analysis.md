# Phase 6 — objective checks (whisper transcription of every clip)

`Similarity` is a rough normalized-text ratio: 1.00 = the transcript matches the written text word-for-word. Difficult-text lines legitimately score lower (the model spells numbers/currency out in words) — read the transcript column to judge the pronunciation. Tone-tagged clips are the neufeld sanity check, leak-trimmed.

| Clip | Dur (s) | Similarity | Expected text | Transcript |
| --- | ---: | ---: | --- | --- |
| neufeld_conv1 | 2.1 | 1.00 | Thank you for calling. | Thank you for calling. |
| neufeld_conv2 | 2.2 | 1.00 | How can I help you today? | How can I help you today? |
| neufeld_conv3 | 2.3 | 1.00 | Let me check that for you. | Let me check that for you. |
| neufeld_q1 | 3.1 | 1.00 | Could you please confirm your account number? | "'Could you please confirm your account number?' |
| neufeld_q2 | 2.6 | 1.00 | Would you like me to explain that again? | Would you like me to explain that again?" |
| neufeld_emo1 | 2.6 | 1.00 | I'm really sorry about what happened. | I'm really sorry about what happened." |
| neufeld_emo2 | 2.6 | 1.00 | That's fantastic news! | That's fantastic news. |
| neufeld_emo3 | 2.7 | 0.96 | I'm afraid we have a problem. | i am afraid we have a problem |
| neufeld_diff1 | 6.7 | 0.89 | Your appointment is on March 3rd at 2:30 PM, in room 401B of the Beaumont Clinic. | your appointment is on march third at two thirty p m in room 401 b of the beaumont clinic |
| neufeld_diff2 | 8.6 | 1.00 | The total comes to $1,247.50, including the $19.99 monthly service fee. | The total comes to $1,247.50, including the $19.99 monthly service fee. |
| neufeld_diff3 | 7.7 | 1.00 | The API returned a 503 error, so the VPN tunnel to the NAS dropped during the HTTP upload. | The API returned a 503 error, so the VPN tunnel to the NAS dropped during the HTTP upload. |
| neufeld_diff4 | 9.2 | 0.78 | Mrs. O'Neill from 42 Hackney Blvd, Apt 7A, called about her Wi-Fi router, a Corvex XR-500. | mrs o'neill from forty two hackney boulevard apart to seven a called about her wi-fi router a corvex xr five hundred |
| neufeld_diff5 | 11.0 | 0.96 | Call 555-0142 between 9 AM and 5 PM EST and ask for Dr. Vásquez about the Q3 report. | call 555-0142 between 9 a.m. and 5 p.m. East T and ask for Dr. Vazquez about the Q3 report. |
| neufeld_long1 | 14.4 | 1.00 | Before we can process the refund, I'll need to verify a few details on your account, so please bear with me for just a moment. Once everything checks out, the money should appear on your card within three to five business days. | before we can process the refund i'll need to verify a few details on your account so please bear with me for just a moment once everything checks out the money should appear on your card within three to five business days |
| neufeld_long2 | 22.9 | 0.99 | Thank you for your patience while I looked into this for you. I can see that the payment left your account on the twelfth, but our system never received the confirmation from the bank. I'll raise this with our payments team right now, and someone will call you back before the end of the day. In the meantime, please keep your reference number handy in case you need to contact us again. | Thank you for your patience while I looked into this for you. I can see that the payment left your account on the 12th, but our system never received the confirmation from the bank. I'll raise this with our payments team right now, and someone will call you back before the end of the day. In the meantime, please keep your reference number handy in case you need to contact us again. |
| golding_conv1 | 1.8 | 1.00 | Thank you for calling. | Thank you for calling. |
| golding_conv2 | 2.2 | 1.00 | How can I help you today? | How can I help you today? |
| golding_conv3 | 1.9 | 1.00 | Let me check that for you. | Let me check that for you. |
| golding_q1 | 2.9 | 1.00 | Could you please confirm your account number? | Could you please confirm your account number? |
| golding_q2 | 2.8 | 1.00 | Would you like me to explain that again? | Would you like me to explain that again?" |
| golding_emo1 | 2.5 | 1.00 | I'm really sorry about what happened. | I'm really sorry about what happened. |
| golding_emo2 | 2.6 | 1.00 | That's fantastic news! | That's fantastic news! |
| golding_emo3 | 2.2 | 1.00 | I'm afraid we have a problem. | I'm afraid we have a problem. |
| golding_diff1 | 7.2 | 0.99 | Your appointment is on March 3rd at 2:30 PM, in room 401B of the Beaumont Clinic. | Your appointment is on March 3rd at 2.30pm in room 401b of the Beaumont Clinic. |
| golding_diff2 | 8.7 | 1.00 | The total comes to $1,247.50, including the $19.99 monthly service fee. | The total comes to $1,247.50, including the 1999 monthly service fee. |
| golding_diff3 | 8.2 | 1.00 | The API returned a 503 error, so the VPN tunnel to the NAS dropped during the HTTP upload. | The API returned a 503 error, so the VPN tunnel to the NAS dropped during the HTTP upload. |
| golding_diff4 | 9.4 | 0.95 | Mrs. O'Neill from 42 Hackney Blvd, Apt 7A, called about her Wi-Fi router, a Corvex XR-500. | Mrs. O'Neill from 42 Hackney Boulevard, a Part 7A, called about her Wi-Fi router, a Corvex XR500. |
| golding_diff5 | 10.4 | 0.99 | Call 555-0142 between 9 AM and 5 PM EST and ask for Dr. Vásquez about the Q3 report. | Call 555-0142 between 9am and 5pm EST and ask for Dr. Vásquez about the Q3 report. |
| golding_long1 | 14.8 | 1.00 | Before we can process the refund, I'll need to verify a few details on your account, so please bear with me for just a moment. Once everything checks out, the money should appear on your card within three to five business days. | before we can process the refund i'll need to verify a few details on your account so please bear with me for just a moment once everything checks out the money should appear on your card within three to five business days |
| golding_long2 | 25.0 | 0.99 | Thank you for your patience while I looked into this for you. I can see that the payment left your account on the twelfth, but our system never received the confirmation from the bank. I'll raise this with our payments team right now, and someone will call you back before the end of the day. In the meantime, please keep your reference number handy in case you need to contact us again. | Thank you for your patience while I looked into this for you. I can see that the payment left your account on the 12th, but our system never received the confirmation from the bank. I'll raise this with our payments team right now, and someone will call you back before the end of the day. In the meantime, please keep your reference number handy in case you need to contact us again. |
| neufeld_tone_base_s1 | 4.2 | 1.00 | Thank you for calling. How may I help you today? | thank you for calling how may i help you today |
| neufeld_tone_tag_calm_s1_trim | 4.1 | 1.00 | Thank you for calling. How may I help you today? | Thank you for calling. How may I help you today? |
| neufeld_tone_tag_happy_s1_trim | 3.2 | 1.00 | Thank you for calling. How may I help you today? | Thank you for calling. How may I help you today? |
| neufeld_tone_tag_sad_s1_trim | 4.3 | 0.96 | Thank you for calling. How may I help you today? | had. Thank you for calling. How may I help you today?" |
| neufeld_tone_base_s2 | 3.1 | 1.00 | Well, that certainly went according to plan. | well that certainly went according to plan |
| neufeld_tone_tag_calm_s2_trim | 2.9 | 1.00 | Well, that certainly went according to plan. | Well, that certainly went according to plan. |
| neufeld_tone_tag_happy_s2_trim | 3.0 | 1.00 | Well, that certainly went according to plan. | Well, that certainly went according to plan. |
| neufeld_tone_tag_sad_s2_trim | 2.9 | 1.00 | Well, that certainly went according to plan. | Well, that certainly went according to plan |
| neufeld_tone_base_s3 | 2.8 | 1.00 | I need you to listen to me. | I need you to listen to me. |
| neufeld_tone_tag_calm_s3_trim | 2.2 | 1.00 | I need you to listen to me. | "'I need you to listen to me.' |
| neufeld_tone_tag_happy_s3_trim | 2.0 | 1.00 | I need you to listen to me. | I need you to listen to me." |
| neufeld_tone_tag_sad_s3_trim | 2.0 | 1.00 | I need you to listen to me. | I need you to listen to me." |
