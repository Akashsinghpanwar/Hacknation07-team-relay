# 60-second technical video: prompts and script

Three ways to use this file:

- **All-in-one AI video tool** (InVideo AI, HeyGen, Synthesia, Pictory): paste the **master prompt**.
- **Clip generator** (Veo, Sora, Runway, Kling): generate the **six B-roll shots** one by one, then cut them together with the voiceover.
- **Most accurate (recommended):** AI B-roll for the human scenes, plus the repo's **real** charts and a **real screen recording** for every number and UI shot. AI video tools invent text and numbers on screens, so don't let them draw the results.

---

## 1. Master prompt (copy everything in the box)

```text
Create a 60-second, 16:9, 1080p technical explainer video with a professional male or female
voiceover (warm, clear, confident, international English, ~160 words per minute) and subtle
modern ambient-electronic background music that ducks under the voice.

PRODUCT: "Relay" - an offline, multilingual Small AI voice assistant for farmer cooperatives.
AUDIENCE: hackathon judges (technical). TONE: precise, human, no hype.

VISUAL STYLE: cinematic documentary B-roll for human scenes (Kenyan coffee highlands, warm
early-morning light, real-looking people, no brand logos on any phone or device), mixed with
clean dark-mode motion graphics: rounded boxes, thin animated connector lines with moving
dots, palette coffee brown #5D4037, leaf green #2E7D32 (local/offline), sky blue #1565C0
(online/optional, dashed), amber #F9A825, red #C62828 (guardrails), indigo #3949AB (human).
Sans-serif type (Inter). Large readable on-screen text, max 7 words per caption.

STORYBOARD AND VOICEOVER (follow timings and use the voiceover text exactly):

[0:00-0:06] Close-up of a smallholder coffee farmer (woman, 40s) at a farm gate in the Kenyan
highlands holding a basic keypad phone; a buyer beside a pickup truck with coffee sacks.
On-screen: "105 KES/kg - fair?"
VO: "A coffee farmer in Kenya is offered 105 shillings a kilo. Is that fair? She has a basic
phone, and no internet."

[0:06-0:14] Cut to a small cooperative office: a laptop on a wooden desk, solar battery
beside it, coffee sacks in the corner. Title animates in: "Relay - Small AI, fully offline".
VO: "Meet Relay: a small AI that runs on one laptop at her co-op, completely offline."

[0:14-0:28] Motion-graphic pipeline, left to right, boxes lighting up in sequence with a
moving dot: "Voice in 5 languages" -> "Whisper speech-to-text + language ID" ->
"Fine-tuned 0.5B model extracts price, type, grade, district". Show five speech bubbles in
English, Swahili, Hindi (Devanagari), Chinese, Korean.
VO: "She speaks in Swahili, Hindi, English, Chinese or Korean. Whisper turns her speech into
text and detects the language. Our fine-tuned half-billion-parameter model pulls out the
price, coffee type, grade and district."

[0:28-0:40] Motion graphic: a database card "Co-op record - dated, sourced" feeds a "Rule
engine" box; the numbers 120, 105 and 15 fly from the record into a speech bubble. Then a
red guard icon and an indigo "Ask a person" box for the uncertain path.
On-screen: "Numbers from records, never the model"
VO: "A rule engine checks a dated co-op record, so every number she hears comes from that
record, never from the model. If the data is old, thin or missing, Relay says 'I'm not
sure' and connects her to a person."

[0:40-0:52] Clean animated bar chart, three bars growing: "Base 0.5B: 56.8%",
"Fine-tuned 0.5B: 94.6%" (green, highlighted), "Zero-shot 3B: 81.1%". Small badges:
"3x faster", "0.53 GB", "trained on a laptop CPU in 40 min".
VO: "We fine-tuned it on a laptop CPU in forty minutes. On our synthetic test set it beats a
three-billion-parameter model, runs three times faster, and fits in half a gigabyte."

[0:52-0:60] Back to the farmer, listening to her phone, then speaking confidently to the
buyer. End card: "Relay - AI informs. The farmer decides." Small footer text:
"Prototype - all prices shown are synthetic demo data."
VO: "Relay informs. The farmer decides. Small AI, where people actually are."

RULES: show every number exactly as written above and no other numbers; no company or
phone logos; don't show real people's names; keep the footer disclaimer visible in the
last shot.
```

---

## 2. Voiceover only (for ElevenLabs)

Paste into ElevenLabs Text-to-Speech, model **Multilingual v2**, stability ≈ 0.45, style ≈ 0.3. About 160 words, which is 60 s at a natural pace. If it runs long, cut "completely" and "actually".

```text
A coffee farmer in Kenya is offered 105 shillings a kilo. Is that fair? She has a basic phone, and no internet.

Meet Relay: a small AI that runs on one laptop at her co-op, completely offline.

She speaks in Swahili, Hindi, English, Chinese or Korean. Whisper turns her speech into text and detects the language. Our fine-tuned half-billion-parameter model pulls out the price, coffee type, grade and district.

A rule engine checks a dated co-op record, so every number she hears comes from that record, never from the model. If the data is old, thin or missing, Relay says "I'm not sure" and connects her to a person.

We fine-tuned it on a laptop CPU in forty minutes. On our synthetic test set it beats a three-billion-parameter model, runs three times faster, and fits in half a gigabyte.

Relay informs. The farmer decides. Small AI, where people actually are.
```

---

## 3. B-roll shot prompts (Veo / Sora / Runway, one clip each, 6–8 s)

1. **Farm gate.** *Cinematic documentary shot, Kenyan highlands coffee farm at sunrise, a woman in her 40s in practical work clothes holds a simple keypad phone, looking uncertain; behind her a buyer stands by a pickup truck loaded with coffee sacks, gesturing a price with his fingers. Shallow depth of field, warm natural light, slow push-in, no logos, no text.*
2. **Calling.** *Close-up of a weathered hand pressing keys on a basic keypad phone, ripe red coffee cherries blurred in the background, then the phone raised to her ear. Natural light, 35 mm look, no brand marks.*
3. **Co-op hub.** *Small rural cooperative office with a mud-brick wall, a laptop open on a wooden desk next to a compact solar battery pack, jute coffee sacks in the corner, a cooperative officer typing. Soft daylight through a window, slow dolly left, screen content not readable, no logos.*
4. **Languages.** *Five people of different backgrounds each speaking into a phone, quick match-cuts, each with a floating speech bubble in a different script (Latin, Devanagari, Chinese, Hangul). Clean, warm, documentary style.*
5. **Officer callback.** *A cooperative officer at the desk picks up a phone and smiles while taking notes, a ledger and coffee sample bags on the desk, natural light, no logos.*
6. **Outcome.** *The same farmer listens to her phone, nods, then speaks confidently to the buyer at the farm gate, who nods back. Golden-hour light, slow pull-out, hopeful tone, no text.*

---

## 4. Real visuals from this repo (use these for every technical shot)

| Timecode | Use | File |
|---|---|---|
| 0:06–0:10 | Title card | `assets/banner.svg` (open it in a browser and screen-record; it animates) |
| 0:14–0:28 | Pipeline | `assets/pipeline.svg` (animated) |
| 0:28–0:40 | Live demo | Screen-record `python -m coop_assistant.apps.web_ui` with Wi-Fi **off**: one price answer showing the evidence panel, then `Parchment grade A in Kiambu` → "out of date" |
| 0:40–0:52 | Results | `assets/results.svg` and `assets/per_language.svg` (animated bars) |
| Optional | Proof | `notebooks/02_speech_offline.ipynb` cell 3: "non-local connection attempts: none" |

To record an SVG animation: open the file in Edge or Chrome, press `Win + Alt + R` (Xbox Game Bar) or use the Clipchamp screen recorder.

## 5. Assembly checklist

- [ ] Voiceover first (ElevenLabs), then cut visuals to it
- [ ] Every number on screen matches: 105 · 120 · 15 · 56.8% · 94.6% · 81.1% · 3× · 0.53 GB · 40 min
- [ ] The "synthetic demo data" footer is visible in the final shot
- [ ] No logos on phones or laptops; no real names
- [ ] Captions burned in (many judges watch muted)
- [ ] Export 1080p MP4 and add the link to `docs/SUBMISSION.md`, then re-run `python scripts/readiness_check.py`

> This is the 60-second technical cut. The brief's submission video must be 2–5 minutes and cover five parts; the full script is in [`SUBMISSION.md`](SUBMISSION.md).
