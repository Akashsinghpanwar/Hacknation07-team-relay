"""General business questions, answered only from the business profile by the local LLM."""

import json
import urllib.request

from coop_assistant.config import BUSINESS_FILE, OLLAMA_URL, QA_MODEL
from coop_assistant.nlu.extract import numbers_in

PROFILE_PATH = BUSINESS_FILE
PROFILE = PROFILE_PATH.read_text(encoding="utf-8")
LANG_NAMES = {"en": "English", "hi": "Hindi", "sw": "Swahili", "zh": "Simplified Chinese", "ko": "Korean"}

SCHEMA = {
    "type": "object",
    "properties": {"answer": {"type": "string"}, "found": {"type": "boolean"}},
    "required": ["answer", "found"],
}


# Kept identical across calls so Ollama can reuse the cached prompt prefix.
SYSTEM = f"""You are the friendly phone assistant for the business described below.
Answer the caller ONLY with facts from the business profile. Keep numbers, prices and times exactly as written there,
and give complete details (for example both opening and closing times).
If the profile does not contain the answer, set found to false and leave answer empty. Never guess or invent anything.
Never give medical, legal or financial advice, and never ask for passwords or PINs.
Sound like a warm, helpful human receptionist on the phone: one to three short sentences, no lists, no markdown.

BUSINESS PROFILE:
{PROFILE}"""


def _ask(question, lang, timeout=90):
    language = LANG_NAMES.get(lang, "the same language as the caller")
    body = json.dumps({
        "model": QA_MODEL,
        "stream": False,
        "keep_alive": "30m",
        "format": SCHEMA,
        "options": {"temperature": 0, "num_predict": 160},
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Caller: {question}\n\n(Write the answer in {language}.)"},
        ],
    }).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(json.loads(resp.read())["message"]["content"])


def answer(question, lang):
    """Returns ("ANSWER" | "NO_INFO", text or None)."""
    try:
        data = _ask(question, lang)
    except (OSError, ValueError, KeyError):
        return "NO_INFO", None
    text = (data.get("answer") or "").strip()
    if not data.get("found") or not text:
        return "NO_INFO", None
    if not numbers_in(text) <= numbers_in(PROFILE) | numbers_in(question):
        return "NO_INFO", None
    return "ANSWER", text
