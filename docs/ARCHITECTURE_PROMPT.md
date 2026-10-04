# Prompt: end-to-end architecture document (PDF) for the coffee price-check Small AI prototype

Copy everything below the line into your document or diagram tool.

---

You are a technical designer producing a polished architecture document (PDF, A4 portrait, 12-16 pages) and the diagrams inside it, for a hackathon submission to the **2026 Small AI for Development Hackathon**. Readers are hackathon judges: technical, time-poor, and scoring on Small AI fidelity (25%), development relevance (20%), data grounding (15%), evidence it works (15%), clarity/design/inclusivity and AI value (15%), scalability (10%), plus a pass/fail Responsible AI gate.

## Hard rules

1. Use only the facts in this prompt. Do not invent metrics, users, partners, deployments, accuracy figures or prices.
2. Every price shown anywhere must carry the label **"SYNTHETIC DEMO DATA"**. Never present a price as real or live.
3. Label the phone channel exactly as stated below: it is built and tested in simulation; a live call was blocked by Twilio trial-account restrictions. Do not show it as deployed.
4. Mark each component as **Local (offline)** or **Online (optional)** using the colour legend below. This boundary is the core of the story.
5. People in images are generic and fictional. No real people, no brand logos (no phone makers, no telecom brands, no company logos).
6. Diagrams must read in greyscale too: pair every colour with a label or icon.

## The project in one paragraph

A smallholder coffee farmer in rural Kenya (fictional persona "Amani") is offered a price by a buyer and has no independent way to check it. She has a basic phone and patchy internet. Our prototype lets her ask, by voice or text, in her own language, whether the offer is fair. A laptop acting as a local "AI hub" (for example at a cooperative office) recognises the speech, extracts the price, coffee type, grade and district, and checks it against a dated local price record. It replies in the same language with the reference price, the date, the source and the gap from the offer, or it says "I am not sure, check with your co-op" and offers a human. The AI never decides to sell; the farmer does.

## Facts to use (all verified in the prototype)

**Languages (tested end to end):** English, Hindi, Swahili, Chinese, Korean. Language is detected automatically from speech.

**Pipeline stages, in order:**

| # | Stage | Technology | Runs | Measured on laptop CPU (Intel Core Ultra 5, 47 GB RAM) |
|---|---|---|---|---|
| 1 | Input | Microphone or typed text in a local web app (Gradio); or a phone call (Twilio) | Local / phone online | - |
| 2 | Speech to text + language ID | faster-whisper "small", int8, domain hotwords (Nyeri, parchment, grade A...) | Local, offline | ~4-6 s per question |
| 3 | Slot extraction, rules first | Multilingual keyword and number rules | Local, offline | ~0 s |
| 4 | Slot extraction, LLM only if rules leave gaps | Qwen2.5 3B via Ollama, JSON-schema output, temperature 0 | Local, offline | ~5-10 s |
| 5 | Safety guard on extraction | A price is accepted only if those digits were actually spoken; unknown units ignored | Local | - |
| 6 | Decision engine | Deterministic Python rules | Local | instant |
| 7 | Evidence store | SQLite, 4 synthetic records with full provenance fields | Local | instant |
| 8 | Reply | Pre-approved templates in 5 languages; numbers filled only from the stored record and the farmer's own words | Local | instant |
| 9 | Text to speech | ElevenLabs (online, optional) with automatic fallback to Piper voices (local) for en/hi/sw/zh/ko; Swahili always local | Online optional / local fallback | ~3 s (Piper) |
| 10 | Output | Spoken answer + screen showing transcript, extracted fields, decision state and the evidence record ID | Local | - |

**Footprint:** Whisper small + 5 Piper voices about 0.8 GB; Qwen2.5 3B about 1.9 GB. Everything is pre-downloaded; the core runs with Wi-Fi off. No paid cloud AI is needed for the core.

**Decision states (the safety contract):**
- **ANSWER** - only with a matching record (same district, coffee form, grade, unit kg, currency KES), inside its validity window and with at least 3 samples. Carries a mandatory evidence ID.
- **CLARIFY** - asks only for the missing field (coffee type, grade, district, or price per kg). Remembers earlier answers in the conversation.
- **ABSTAIN** - out-of-date record, too few samples, no data, wrong grade, wrong currency, or an out-of-scope question (for example crop disease). Gives no number.
- **REFER** - the farmer asks for a person; a co-op officer follows up with consent.

**Synthetic demo records (show as a table, labelled SYNTHETIC DEMO DATA):**

| Record | District | Form / grade | Price (KES/kg) | Samples | Status |
|---|---|---|---|---|---|
| DEMO-NYR-PARCH-A | Nyeri | Parchment A | 120 | 12 | Valid, observed 2 days ago -> ANSWER |
| DEMO-NYR-CHERRY | Nyeri | Cherry | 65 | 9 | Valid -> ANSWER |
| DEMO-KMB-PARCH-A-STALE | Kiambu | Parchment A | 110 | 8 | Expired 30 days ago -> ABSTAIN |
| DEMO-KRN-PARCH-A-SPARSE | Kirinyaga | Parchment A | 125 | 1 | Too few samples -> ABSTAIN |
| (none) | Murang'a | - | - | - | No data -> ABSTAIN |

Record fields: id, country, district, market, crop, product_form, grade, currency, unit, observed_at, valid_until, price_value, sample_count, source_name, source_contact, usage_permission, imported_at.

**Example interaction (use as a storyboard):**
- Farmer (Swahili): "Mnunuzi ametoa shilingi 105 kwa kilo kwa kahawa ya parchment daraja A huko Nyeri."
- System (Swahili): "[DATA YA MAJARIBIO] The reference price for parchment grade A in Nyeri is KES 120 per kg (Demo Co-op Nyeri, observed <date>). The buyer's offer of 105 is KES 15 below. This is information only; the decision to sell is yours."
- Same question about Kiambu: "My latest record for Kiambu is out of date, so I cannot give a current price. Please check with your co-op."

**Phone channel (built, simulation-tested, not live):**
- Inbound: any phone -> Twilio number -> Cloudflare quick tunnel (HTTPS) -> FastAPI call server on the laptop. Flow: consent greeting -> beep -> record question -> laptop downloads the recording, deletes it from Twilio, runs stages 2-9 -> plays the answer -> "ask another question" -> press 0 for a person.
- Callback mode: the laptop asks Twilio to ring the farmer, so the farmer pays nothing (a "missed call, call back" pattern).
- Security: every Twilio request is signature-checked (HMAC); unsigned requests get 403; audio files have random names; secrets live only in environment variables.
- Status: tested end to end with simulated signed Twilio requests and recorded audio. The Cloudflare tunnel was verified reachable from the internet. A live call was blocked because the Twilio trial account only allows Twilio's own demo templates; upgrading the account removes this.

**Testing evidence:** 19 automated tests pass (all decision states, the number guard, multilingual rendering with exact numbers, two-turn clarification, out-of-scope handling). Round-trip test synthesised a question in each language and transcribed it back: language ID correct in all 5.

**Honest limits (must appear in the document):**
- Speech accuracy varies by language; Swahili, Chinese and Korean need real-speaker testing. In one synthetic test Whisper heard "105" as "150" in Chinese, which is why every reply repeats the offer it heard so the farmer can catch errors.
- Reply wording in Hindi, Swahili, Chinese and Korean needs native-speaker review.
- All prices are synthetic. A pilot needs a dated, permitted price feed from a cooperative or market partner.
- The phone channel needs internet (Twilio + tunnel). A field version replaces this with a local SIM/GSM gateway + Asterisk, so calls work without internet while mobile voice coverage exists.
- The hackathon's strict rule is "on the user's own device, no connection". The laptop hub is local edge inference, not on the farmer's phone; the document must say so plainly.

## Document outline

1. **Cover** - title "Coffee Price Check: a Small AI that knows when it doesn't know", subtitle "Offline, multilingual price reference for smallholder farmers", hero image (Image 1).
2. **The problem** - Amani's story in 4 short beats; why a price list by SMS is not enough (she speaks, in her language, about her own offer).
3. **Solution at a glance** - one sentence, Figure 1, three bullets on what is local.
4. **End-to-end pipeline** - Figure 2 with the stage table above.
5. **Decision engine and safety** - Figure 3 (decision flow) and Figure 4 (four states with example replies).
6. **Data grounding** - synthetic record table, record schema, Figure 5 (provenance from source to spoken sentence), data gaps.
7. **Multilingual design** - Figure 6 (one question, five languages, one record).
8. **Access channels** - Figure 7 (browser/smartphone, inbound call, callback, future GSM gateway) with status badges.
9. **Phone call sequence** - Figure 8 (sequence diagram).
10. **Small AI footprint and performance** - Figure 9 (model sizes and per-stage latency bars using only the numbers above).
11. **Responsible AI** - consent, transient audio, human decides, abstention, fairness testing plan, Figure 10 (guardrail checklist).
12. **Evidence it works** - tests, round-trip results, screenshots of the app (placeholders labelled "insert screenshot").
13. **Limits and roadmap** - honest limits; roadmap: real co-op data, native-speaker review, GSM gateway, Android on-device app, crop-advice referral.
14. **Appendix** - technology list, decision-state contract (JSON), glossary.

## Figures to draw

**Figure 1 - System context.** Left: farmer with a basic phone and a shared smartphone. Centre: "Local AI Hub (laptop at co-op office)". Right: "Co-op officer (human)". Top, dashed: "Optional online services: ElevenLabs voice, Twilio phone routing". Bottom: "Synthetic price records (SQLite)". Arrows labelled "speak / type", "answer + date + source", "referral with consent".

**Figure 2 - End-to-end pipeline.** Horizontal left-to-right flow of the 10 stages in the table. Green boxes for local/offline, blue dashed boxes for online/optional. Under each box: the technology and the measured time. Show the branch at stage 3/4: "rules complete -> skip LLM" vs "gaps -> Qwen2.5 3B". Show a red guard icon at stage 5 ("number must be spoken") and stage 6 ("evidence required").

**Figure 3 - Decision flowchart.** Start "intent?" -> HUMAN -> REFER; UNKNOWN -> ABSTAIN (out of scope); PRICE_CHECK -> "missing type/district/grade?" -> CLARIFY -> "unit is kg?" no -> CLARIFY -> "currency KES?" no -> ABSTAIN -> "record for district+form?" no -> ABSTAIN (no data) -> "grade matches?" no -> ABSTAIN (no grade) -> "still valid?" no -> ABSTAIN (stale) -> "samples >= 3?" no -> ABSTAIN (sparse) -> ANSWER (with evidence ID).

**Figure 4 - Four response states.** Four cards: ANSWER (green), CLARIFY (amber), ABSTAIN (red), REFER (indigo). Each with an icon, the rule, and one example reply from this prompt.

**Figure 5 - Provenance chain.** "Co-op price record (future) / synthetic fixture (now)" -> SQLite record with fields -> decision engine -> template -> spoken sentence, with arrows showing that the numbers 120, 105 and 15 come from the record and the farmer's own words, never from a model.

**Figure 6 - One question, five languages.** Five speech bubbles (EN, HI in Devanagari, SW, ZH in Chinese characters, KO in Hangul) all pointing to one record "DEMO-NYR-PARCH-A, 120 KES/kg", and five reply bubbles coming back.

**Figure 7 - Access channels matrix.** Columns: Browser on laptop/smartphone; Inbound phone call; Callback call; Future GSM/SIM gateway. Rows: needs internet?, needs smartphone?, cost to farmer, status. Status badges: "Working", "Built - simulation tested", "Built - blocked by trial account", "Roadmap".

**Figure 8 - Phone call sequence diagram.** Lifelines: Farmer phone, Twilio, Cloudflare tunnel, Call server (laptop), Whisper, Engine + SQLite, TTS. Messages: dial -> webhook /voice (signed) -> greeting + beep -> record -> /turn -> "one moment" + redirect -> download recording -> delete from Twilio -> transcribe -> decide -> synthesize -> /result returns Play -> farmer hears answer -> "ask another or press 0".

**Figure 9 - Footprint and latency.** Left: stacked bar of on-disk size (Whisper small + voices ~0.8 GB, Qwen2.5 3B ~1.9 GB). Right: horizontal bars per stage: STT 4-6 s, rules ~0 s, LLM 5-10 s (only when needed), engine instant, TTS ~3 s. Caption: "Measured on a laptop CPU, no GPU."

**Figure 10 - Responsible AI checklist.** Ticks: consent prompt; raw audio deleted after transcription; recordings deleted from Twilio; synthetic data labelled; evidence ID on every answer; no number when uncertain; farmer makes the decision; human referral; out-of-scope refusal. Open items (unticked): native-speaker review; real-speaker accuracy by gender and accent; real data partner.

## Illustrative images (photorealistic or warm editorial illustration)

- **Image 1 (cover):** A smallholder coffee farmer, a woman in her 40s, standing between rows of coffee bushes with ripe red cherries on a green hillside in the Kenyan highlands, early morning light, holding a simple keypad phone to her ear and smiling slightly. No logos. Space at the top for a title.
- **Image 2 (problem):** At the farm gate, a buyer with a pickup truck and sacks of coffee holds up fingers to show a price while the farmer looks uncertain. Documentary style, natural colours.
- **Image 3 (hub):** A small cooperative office with a mud-brick wall, a laptop on a wooden desk next to a small solar battery pack, coffee sacks in the corner, a cooperative officer at the desk. No screen text, no logos.
- **Image 4 (multilingual):** Five diverse hands holding phones, each with a speech bubble in a different script (Latin, Devanagari, Chinese, Hangul), flat illustration.
- **Image 5 (outcome):** The farmer listening to her phone, then confidently talking to the buyer; split-panel illustration.

## Visual style

- Palette: coffee brown #5D4037 (headings), leaf green #2E7D32 (local/offline), sky blue #1565C0 (online/optional, dashed borders), amber #F9A825 (clarify), red #C62828 (abstain/guards), indigo #3949AB (human/refer), warm off-white #FAF7F2 background.
- Font: a clean sans-serif (Inter or Source Sans). Headings bold, body 10-11 pt.
- Diagrams: flat, rounded rectangles, thin arrows with verb labels, a legend on every figure (green = local offline, blue dashed = online optional).
- Each page: one key message in a sentence at the top, then the figure, then at most 5 bullets.
- Footer on every page: "Prototype - all prices are synthetic demo data".
