"""Download every model the assistant needs, once, while online. Afterwards everything runs offline.

Usage: python scripts/download_models.py [--skip-ollama] [--whisper small]
"""

import argparse
import shutil
import subprocess
import sys

from coop_assistant.config import EXTRACT_FALLBACK_MODEL, MODEL_DIR, PIPER_VOICES, QA_MODEL


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--whisper", default="small")
    parser.add_argument("--skip-ollama", action="store_true")
    args = parser.parse_args()

    print(f"Model folder: {MODEL_DIR}")
    from faster_whisper import WhisperModel
    WhisperModel(args.whisper, device="cpu", compute_type="int8", download_root=str(MODEL_DIR / "models"))
    print(f"Whisper {args.whisper}: ok")

    subprocess.run([sys.executable, "-m", "piper.download_voices", "--download-dir", str(MODEL_DIR / "voices"),
                    *PIPER_VOICES.values()], check=True)
    print("Piper voices: ok")

    if args.skip_ollama:
        return
    ollama = shutil.which("ollama")
    if not ollama:
        print("Ollama not found: install it from https://ollama.com, then rerun or run `ollama pull` yourself.")
        return
    for model in dict.fromkeys([EXTRACT_FALLBACK_MODEL, QA_MODEL]):
        subprocess.run([ollama, "pull", model], check=True)
    print("Ollama models: ok. Build the fine-tuned 'coop-extract' with finetune/README.md; until then "
          f"extraction falls back to {EXTRACT_FALLBACK_MODEL}.")


if __name__ == "__main__":
    main()
