"""All runtime settings in one place. Every value can be overridden with an environment variable."""

import os
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]

_default_cache = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home() / ".cache")) / "coffee-price-ai"
MODEL_DIR = pathlib.Path(os.environ.get("MODEL_DIR", _default_cache))
DB_PATH = pathlib.Path(os.environ.get("DB_PATH", MODEL_DIR / "prices.db"))
BUSINESS_FILE = pathlib.Path(os.environ.get("BUSINESS_FILE", PROJECT_ROOT / "data" / "business.json"))

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
# Fine-tuned 0.5B extractor (finetune/), with the zero-shot 3B as fallback when it is not installed.
EXTRACT_MODEL = os.environ.get("OLLAMA_MODEL", "coop-extract")
EXTRACT_FALLBACK_MODEL = os.environ.get("OLLAMA_FALLBACK_MODEL", "qwen2.5:3b")
QA_MODEL = os.environ.get("QA_MODEL", "gemma3:4b")

WHISPER_SIZE = os.environ.get("WHISPER_SIZE", "small")

ELEVENLABS_MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
ELEVENLABS_TIMEOUT = float(os.environ.get("ELEVENLABS_TIMEOUT", "12"))
# Swahili is not in eleven_multilingual_v2, so it stays on the local Piper voice.
ELEVENLABS_LANGS = set(os.environ.get("ELEVENLABS_LANGS", "en,hi,zh,ko").split(","))

PIPER_VOICES = {
    "en": "en_US-lessac-medium",
    "hi": "hi_IN-priyamvada-medium",
    "sw": "sw_CD-lanfrica-medium",
    "zh": "zh_CN-huayan-medium",
    "ko": "ko_KR-kss-medium",
}
