"""Hackathon readiness check: verifies each rule and deliverable of the brief against this repo and machine.

Runs the real pipeline with every non-local network connection blocked, so "offline" is tested, not assumed.
Usage: python scripts/readiness_check.py   (writes docs/READINESS_REPORT.md; exit code 1 if a required check fails)
"""

import datetime as dt
import json
import os
import pathlib
import re
import socket
import subprocess
import sys
import time
import urllib.request

from coop_assistant.config import MODEL_DIR, OLLAMA_URL, PIPER_VOICES, PROJECT_ROOT, WHISPER_SIZE

REPORT = PROJECT_ROOT / "docs" / "READINESS_REPORT.md"
SIDELOAD_LIMIT_GB = 4.0
results = []


def check(area, name, ok, evidence, required=True):
    results.append((area, name, "PASS" if ok else ("FAIL" if required else "WARN"), evidence))
    print(f"[{'PASS' if ok else ('FAIL' if required else 'WARN')}] {area}: {name} - {evidence}")


def _gb(path):
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1e9


class NoInternet:
    """Allow loopback (Ollama) only; any other connection attempt raises."""

    def __enter__(self):
        self.original = socket.socket.connect
        self.blocked = []

        def guarded(sock, address):
            host = address[0] if isinstance(address, tuple) else address
            if host not in ("127.0.0.1", "::1", "localhost"):
                self.blocked.append(host)
                raise OSError(f"blocked by readiness check: {host}")
            return self.original(sock, address)

        socket.socket.connect = guarded
        return self

    def __exit__(self, *exc):
        socket.socket.connect = self.original


def check_tests():
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=PROJECT_ROOT,
                          capture_output=True, text=True)
    summary = re.search(r"Ran (\d+) tests", proc.stderr)
    check("Prototype", "unit tests pass", proc.returncode == 0,
          f"{summary.group(1) if summary else '?'} tests, exit code {proc.returncode}")


def check_models():
    whisper = next((MODEL_DIR / "models").glob(f"models--*faster-whisper-{WHISPER_SIZE}"), None)
    check("Small model", f"Whisper {WHISPER_SIZE} stored locally", bool(whisper),
          f"{_gb(whisper):.2f} GB" if whisper else "missing - run scripts/download_models.py")
    voices = [v for v in PIPER_VOICES.values() if (MODEL_DIR / "voices" / f"{v}.onnx").exists()]
    check("Small model", "Piper voices stored locally", len(voices) == len(PIPER_VOICES),
          f"{len(voices)}/{len(PIPER_VOICES)} voices, {_gb(MODEL_DIR / 'voices'):.2f} GB")
    try:
        tags = json.load(urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5))["models"]
    except OSError as e:
        check("Small model", "Ollama reachable", False, str(e))
        return
    for m in tags:
        size = m["size"] / 1e9
        check("Small model", f"{m['name']} under {SIDELOAD_LIMIT_GB:.0f} GB (sideloadable)", size < SIDELOAD_LIMIT_GB,
              f"{size:.2f} GB, quantization {m.get('details', {}).get('quantization_level', '?')}")
    names = {m["name"].split(":")[0] for m in tags}
    check("Fine-tuning", "fine-tuned extraction model installed in Ollama", "coop-extract" in names,
          "coop-extract present" if "coop-extract" in names else "run finetune/README.md steps 3-4", required=False)


def check_offline_pipeline():
    os.environ.pop("ELEVENLABS_API_KEY", None)
    from coop_assistant.core.store import connect
    from coop_assistant.pipeline import Assistant
    from coop_assistant.speech import voice

    cases = [
        ("en", "Buyer offered 105 shillings per kg for grade A parchment coffee in Nyeri", "ANSWER", "matched"),
        ("sw", "Mnunuzi ametoa shilingi 105 kwa kilo kwa kahawa ya parchment daraja A huko Nyeri", "ANSWER", "matched"),
        ("en", "Parchment grade A in Kiambu", "ABSTAIN", "stale"),
        ("en", "Parchment grade A in Kirinyaga", "ABSTAIN", "sparse"),
        ("en", "Do you sell tractors?", "ABSTAIN", "no_info"),
        ("en", "Can I talk to somebody please?", "REFER", "human_requested"),
        ("hi", "मुझे एडवांस पैसे मिल सकते हैं क्या?", "ANSWER", "business_info"),
    ]
    with NoInternet() as net:
        bot = Assistant(connect(":memory:"))
        for lang, text, state, reason in cases:
            start = time.time()
            d = bot.handle(text, lang)["decision"]
            bot.reset()
            ok = (d["state"], d["reason"]) == (state, reason)
            area = "Guardrails" if state in ("ABSTAIN", "REFER") else "Offline core"
            check(area, f"[{lang}] {text[:48]}", ok, f"{d['state']}/{d['reason']} in {time.time() - start:.1f}s, no internet")

        start = time.time()
        clip, engine = voice.speak("The buyer offered 105 shillings per kilo for grade A parchment coffee in Nyeri.", "en")
        heard, lang, _ = voice.transcribe(clip)
        reply = bot.handle(heard, lang)
        spoken, engine2 = voice.speak(reply["reply"], reply["lang"])
        check("Offline core", "voice in -> answer -> voice out with internet blocked",
              bool(spoken) and engine == engine2 == "piper",
              f"heard '{heard[:60]}', state {reply['decision']['state']}, {time.time() - start:.1f}s")
        check("Offline core", "no non-local connection attempted", not net.blocked,
              f"blocked: {sorted(set(net.blocked))}" if net.blocked else "0 attempts")


def check_docs():
    def has(path, *needles):
        p = PROJECT_ROOT / path
        text = p.read_text(encoding="utf-8").lower() if p.exists() else ""
        return p.exists() and all(n.lower() in text for n in needles)

    check("Data", "data card cites sources, licenses and sizes", has("docs/DATA_CARD.md", "license", "size", "source"),
          "docs/DATA_CARD.md")
    check("Data", "data card states what the data does not cover", has("docs/DATA_CARD.md", "does not cover"),
          "scored by the brief")
    check("Data", "synthetic data is labelled", has("docs/DATA_CARD.md", "synthetic") and has("data/business.json", "synthetic"),
          "DATA_CARD + business.json note")
    check("Rules", "named local language and a less-supported language assessed",
          has("docs/DATA_CARD.md", "swahili", "less-supported"), "Swahili named; assessment in DATA_CARD")
    check("Deliverables", "problem statement in the required one-sentence form",
          has("docs/SUBMISSION.md", "because of this tool", "we know because"), "docs/SUBMISSION.md")
    check("Deliverables", "2-5 minute video script covers the five required parts",
          has("docs/SUBMISSION.md", "problem statement", "ai capabilities", "tool demo", "challenge", "your take"),
          "docs/SUBMISSION.md")
    check("Deliverables", "video recorded", has("docs/SUBMISSION.md", "video link: http"),
          "add the link to docs/SUBMISSION.md", required=False)
    check("Fine-tuning", "model card for the fine-tuned model", has("finetune/MODEL_CARD.md", "intended use", "limitations"),
          "finetune/MODEL_CARD.md", required=False)


def check_secrets():
    pattern = re.compile(r"AC[0-9a-f]{32}|sk_[0-9a-f]{20,}|SK[0-9a-f]{32}|auth_token\s*=\s*['\"]\w{16,}")
    tracked = subprocess.run(["git", "ls-files"], cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.split()
    hits = [f for f in tracked if (PROJECT_ROOT / f).is_file()
            and pattern.search((PROJECT_ROOT / f).read_text(encoding="utf-8", errors="ignore"))]
    check("Responsible AI", "no credentials in tracked files", not hits, f"{len(tracked)} files scanned, hits: {hits}")
    pdfs = [f for f in tracked if f.lower().endswith(".pdf")]
    check("Responsible AI", "restricted brief PDF not tracked", not pdfs, f"tracked PDFs: {pdfs}")


def write_report():
    icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}
    lines = [
        "# Readiness report",
        "",
        f"Generated by `scripts/readiness_check.py` on {dt.datetime.now():%Y-%m-%d %H:%M}. "
        "The offline checks ran with every non-loopback network connection blocked.",
        "",
        "| Area | Check | Result | Evidence |",
        "|---|---|---|---|",
    ]
    lines += [f"| {a} | {n} | {icon[s]} {s} | {e.replace('|', '/')} |" for a, n, s, e in results]
    counts = {s: sum(r[2] == s for r in results) for s in icon}
    lines += ["", f"**{counts['PASS']} passed, {counts['FAIL']} failed, {counts['WARN']} warnings.**", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n{counts} -> {REPORT.relative_to(PROJECT_ROOT)}")
    return counts["FAIL"] == 0


if __name__ == "__main__":
    check_tests()
    check_models()
    check_offline_pipeline()
    check_docs()
    check_secrets()
    sys.exit(0 if write_report() else 1)
