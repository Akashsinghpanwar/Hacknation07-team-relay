# Model card: `coop-extract` (Qwen2.5-0.5B-Instruct + LoRA)

| | |
|---|---|
| Base model | [Qwen/Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct), Apache-2.0 |
| Method | LoRA SFT (r 16, alpha 32, dropout 0.05, all attention and MLP projections), merged into the base |
| Training data | `finetune/data/train.jsonl`, extract task only: 215 synthetic rows in 5 languages (see [DATA_CARD](../docs/DATA_CARD.md)) |
| Hardware | Laptop CPU (Intel Core Ultra 5 235U, 12 threads), no GPU |
| Training | 1 epoch, 27 optimiser steps, effective batch 8, LR 3e-4 cosine, loss on the assistant's JSON only |
| Export | Merged → GGUF `q8_0` with llama.cpp `convert_hf_to_gguf.py` → `ollama create coop-extract` |
| Size | 0.53 GB GGUF q8_0 (494M parameters, 24 layers), down from 1.9 GB for the 3B it replaces |
| Weights published? | No. The weights are rebuilt locally with `train_lora.py` + `export_ollama.py` and are not committed (see `.gitignore`) |

## Intended use

It turns one caller sentence about a coffee buyer's offer into the JSON slots the decision engine needs: `intent, quote, currency, unit, product_form, grade, district`. It never produces answers for callers. Every output goes through the app's normalisation, the "price must be spoken" guard, and then the deterministic engine, which abstains when a slot is missing or wrong.

## Results

**Training:** 40.5 min on CPU. Final training loss 0.030. On the held-out set, eval loss was 0.0031 and token accuracy 99.95%.

**Held-out extraction set:** 37 rows, scored by `finetune/evaluate.py` with the app's own normalisation.

| Model | Size | Intent accuracy | All-slot exact match | Seconds / sentence (CPU) |
|---|---|---|---|---|
| `qwen2.5:0.5b`, same base, no fine-tune | 0.40 GB | 94.6% | 56.8% | 3.4 |
| **`coop-extract`, this model** | **0.53 GB** | **97.3%** | **94.6%** | **3.3** |
| `qwen2.5:3b`, zero-shot, previous default | 1.9 GB | 100% | 81.1% | 9.9 |

The fine-tune took the 0.5B base from 56.8% to 94.6% exact match. That beats the 3B model it replaces, runs 3× faster per sentence, and is 3.6× smaller on disk.

**Remaining errors (2 of 37):**
1. *"A trader wants to pay 155 per kilo for my cherry here in Murang'a"*: it added `currency: KES`, which the caller never said. This is harmless here because KES is the only currency the engine accepts, but it is a guess.
2. *"Naomba kuongea na afisa wa ushirika"* (Swahili: "I'd like to speak to a co-op officer"): classed as `UNKNOWN` instead of `HUMAN`. In the app this never reaches the model, because the keyword router catches "afisa" first and returns `REFER`.

> **Read these numbers with care.** The eval rows come from the same 12 templates as the training rows; only the prices, grades and districts differ. 94.6% shows the model learned the task format and vocabulary. It is **not** an estimate of accuracy on real callers.

## Limitations

- Trained only on templated synthetic sentences, so real speech with fillers, code-switching or spoken numbers may fail. Failures lead to a clarifying question or an abstention, never to a made-up price.
- One epoch on CPU, as a working proof of the fine-tune → quantise → serve loop, not a tuned model. More epochs, real transcripts and a GPU are the next step.
- Not trained for business Q&A, which stays on `gemma3:4b`.
- Uses the same five languages as the app. Gĩkũyũ and other unsupported languages are not covered.
