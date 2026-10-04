# 60-second technical video: prompts and script

Technical content only: architecture, models, guardrails, fine-tuning and evidence. No story scenes or people.

Three ways to use this file:

- **All-in-one AI video tool** (InVideo AI, HeyGen, Synthesia, Pictory): paste the **master prompt**.
- **Clip generator** (Veo, Sora, Runway, Kling): generate the **abstract motion clips** in §3, then cut them with the voiceover.
- **Most accurate (recommended):** use the repo's **real** diagrams, terminal output and notebooks (§4) for every number and screen. AI video tools invent text on screens.

---

## 1. Master prompt (copy everything in the box)

```text
Create a 60-second, 16:9, 1080p TECHNICAL explainer video. Motion graphics and screen-style
visuals only: no people, no story scenes, no stock footage of farms or offices.
Voiceover: calm, precise, technical, international English, ~160 words per minute.
Music: minimal ambient electronic, low, ducking under the voice.

PRODUCT: "Relay", an offline, multilingual Small AI voice assistant in a small box at a
business owner's home; customers reach it with an ordinary phone call to the box's SIM.
AUDIENCE: technical judges.

VISUAL STYLE: dark background #14110F; flat rounded boxes; thin connector lines with moving
dots; monospace code snippets; palette leaf green #66BB6A (local/offline), dashed sky blue
#64B5F6 (online/optional), amber #FFCA28 (routing), red #EF5350 (guardrails), indigo
#7986CB (human hand-off), sand #F3D9B1 (headings). Inter for text, JetBrains Mono for code.
Captions on screen, max 7 words each.

STORYBOARD AND VOICEOVER (follow timings and use the voiceover text exactly):

[0:00-0:07] Title "Relay". Then a simple line diagram: keypad phone icon -> cell tower
("voice call, no internet") -> a house outline containing a small box labelled
"Relay box: mini PC + SIM". Caption: "Runs at home · no GPU · no cloud".
VO: "Relay is an AI box in a business owner's home. Customers call its SIM number from any
phone, over the normal mobile network, with no internet."

[0:07-0:17] Zoom into the box; its inside becomes the pipeline. Highlight in order:
"SIM voice modem + call handler" -> "faster-whisper small: speech-to-text + language ID".
Five language tags pop out: EN, SW, HI, ZH, KO.
VO: "Inside, a call handler answers, and faster-whisper transcribes the caller and detects
the language: English, Swahili, Hindi, Chinese or Korean. All on one CPU."

[0:17-0:29] An amber "Router" box splits into three paths: indigo "Person -> REFER",
green "Price check: rules -> fine-tuned Qwen2.5 0.5B -> JSON slots", green
"Business question: Gemma 3 4B + business.json". Show a small JSON card:
{"quote":105,"product_form":"parchment","grade":"A","district":"Nyeri"}.
VO: "A keyword router sends requests for a person straight to a human. Price checks use
rules first; if fields are missing, our fine-tuned Qwen 0.5B extracts them as schema-
constrained JSON. Business questions go to Gemma 3, grounded in one JSON profile."

[0:29-0:40] Red "Guard" box filters slots: values not found in the transcript are struck
through. A "Decision engine" box reads an "SQLite record · evidence ID" card and outputs
four state chips: ANSWER (green), CLARIFY (amber), ABSTAIN (red), REFER (indigo).
Caption: "Numbers from records, never the model".
VO: "Guards drop any price, coffee type or grade the caller did not actually say. A
deterministic engine answers only from a dated SQLite record with an evidence ID; otherwise
it clarifies, abstains, or refers."

[0:40-0:52] Flow "LoRA SFT on CPU, 40 min" -> "merge" -> "GGUF q8_0, 0.53 GB" -> "Ollama".
Then an animated bar chart: "Base 0.5B 56.8%", "Fine-tuned 0.5B 94.6%" (green, highlighted),
"Zero-shot 3B 81.1%", with badges "3x faster" and "3.6x smaller".
Footer: "Exact match on 37 held-out synthetic sentences".
VO: "We LoRA fine-tuned the half-billion-parameter model on a laptop CPU in forty minutes,
exported it to an eight-bit GGUF and served it with Ollama: ninety-four point six percent
exact match versus eighty-one for a three-billion model, three times faster."

[0:52-0:60] Terminal-style panel: "readiness_check.py - network blocked - 26 passed,
0 failed". Then the voice box: "Piper (local) · ElevenLabs only when online". End card:
"Relay · local inference · evidence or abstain".
VO: "A readiness check runs the whole pipeline with the network blocked: twenty-six checks
pass, none fail. Voices are local Piper; ElevenLabs is optional when online."

RULES: show only the numbers written above, exactly; no logos; no people; keep the
"synthetic" footer visible in the results shot.
```

---

## 2. Voiceover only (for ElevenLabs)

Paste into ElevenLabs Text-to-Speech, model **Multilingual v2**, stability ≈ 0.5, style ≈ 0.2. About 165 words, roughly 60 s. If it runs long, drop the last sentence.

```text
Relay is an AI box in a business owner's home. Customers call its SIM number from any phone, over the normal mobile network, with no internet.

Inside, a call handler answers, and faster-whisper transcribes the caller and detects the language: English, Swahili, Hindi, Chinese or Korean. All on one CPU.

A keyword router sends requests for a person straight to a human. Price checks use rules first; if fields are missing, our fine-tuned Qwen 0.5B extracts them as schema-constrained JSON. Business questions go to Gemma 3, grounded in one JSON profile.

Guards drop any price, coffee type or grade the caller did not actually say. A deterministic engine answers only from a dated SQLite record with an evidence ID; otherwise it clarifies, abstains, or refers.

We LoRA fine-tuned the half-billion-parameter model on a laptop CPU in forty minutes, exported it to an eight-bit GGUF and served it with Ollama: ninety-four point six percent exact match versus eighty-one for a three-billion model, three times faster.

A readiness check runs the whole pipeline with the network blocked: twenty-six checks pass, none fail. Voices are local Piper; ElevenLabs is optional when online.
```

---

## 3. Abstract motion clips (Veo / Sora / Runway, 5–8 s each, no text)

Use these as backgrounds behind the real diagrams. Ask for **no text** in the clips; add captions in the editor.

1. **Local compute.** *Dark studio, a minimal matte laptop outline drawn in thin green light lines, small particles flowing into it from a sound-wave on the left, no internet cloud icon, slow orbit camera, no text, no logos.*
2. **Speech to tokens.** *A glowing audio waveform morphing into a stream of small rounded tokens moving left to right on a dark background, soft green and sand colours, macro depth of field, no readable text.*
3. **Routing.** *A single light pulse travelling along a thin line and splitting into three branches, amber, green and indigo, on a black grid, smooth camera pan, minimalist, no text.*
4. **Guardrail.** *Particles passing through a translucent red filter plane; some particles are blocked and fade out, the rest continue as green, dark background, slow motion, no text.*
5. **Fine-tuning.** *A small neural-network lattice glowing green while thin adapter layers slide into place, then compressing into a compact cube, dark background, elegant, no text.*

---

## 4. Real visuals from this repo (use for every technical shot)

| Timecode | Shot | Source |
|---|---|---|
| 0:00–0:07 | Title + end-to-end story | `assets/banner.svg`, then `assets/story.svg` (phone → tower → Relay box at home, animated) |
| 0:07–0:17 | Inside the box: STT + language ID | `assets/pipeline.svg` (animated); `notebooks/02_speech_offline.ipynb`, the round-trip table (detected language ✔ for all 5) |
| 0:17–0:29 | Router + JSON slots | `notebooks/01_pipeline_walkthrough.ipynb`, the extraction table (method `regex` / `llm`, slots per language); README routing flowchart |
| 0:29–0:40 | Guards + decision states | `notebooks/01`, the decision-engine table (ANSWER / CLARIFY / ABSTAIN / REFER with evidence IDs); `notebooks/02`, the offline two-turn run (CLARIFY → ANSWER, "non-local connection attempts: none") |
| 0:40–0:52 | Fine-tune + results | `assets/results.svg`, `assets/per_language.svg`; `notebooks/03_finetuning.ipynb` export table (coop-extract, Q8_0, 0.53 GB) |
| 0:52–0:60 | Readiness + live UI | `docs/READINESS_REPORT.md` or `notebooks/05`; screen-record `python -m coop_assistant.apps.web_ui` with Wi-Fi off |

Optional code close-ups (2 s each, zoomed, syntax-highlighted):
- `src/coop_assistant/nlu/extract.py`: the `normalize()` guard (`if quote is not None and quote not in said`)
- `src/coop_assistant/core/decision.py`: the `stale` / `sparse` abstain checks
- `src/coop_assistant/nlu/business_qa.py`: the number guard on answers

To record SVG animations: open the file in Edge or Chrome and use `Win + Alt + R` or the Clipchamp screen recorder.

## 5. Assembly checklist

- [ ] Voiceover first, then cut visuals to it
- [ ] Every number on screen matches: 5 languages · 0.5B · 40 min · 0.53 GB · 94.6% · 81.1% · 56.8% · 3× · 3.6× · 26 passed / 0 failed
- [ ] "Exact match on 37 held-out synthetic sentences" footer visible on the results shot
- [ ] No logos, no people
- [ ] Captions burned in
- [ ] Export 1080p MP4; add the link to `docs/SUBMISSION.md`, then re-run `python scripts/readiness_check.py`

> This is the 60-second technical cut. The brief's submission video is 2–5 minutes and needs five parts, including the problem statement; that script is in [`SUBMISSION.md`](SUBMISSION.md).
