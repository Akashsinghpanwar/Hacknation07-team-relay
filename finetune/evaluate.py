"""Score an Ollama model on the held-out set, before or after fine-tuning.

extract: intent accuracy and exact match of all six slots after the app's own normalisation.
qa:      found/not-found accuracy, and how often a "found" answer only uses numbers from the profile.
Usage: python finetune/evaluate.py --extract-model qwen2.5:3b --qa-model gemma3:4b [--limit 0]
"""

import argparse
import json
import pathlib
import time
import urllib.request

from coop_assistant.config import OLLAMA_URL
from coop_assistant.nlu import business_qa
from coop_assistant.nlu.extract import SCHEMA as EXTRACT_SCHEMA
from coop_assistant.nlu.extract import normalize, numbers_in

HERE = pathlib.Path(__file__).parent


def chat(model, messages, schema):
    body = json.dumps({"model": model, "stream": False, "keep_alive": "30m", "format": schema,
                       "options": {"temperature": 0}, "messages": messages}).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(json.loads(resp.read())["message"]["content"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(HERE / "data" / "eval.jsonl"))
    parser.add_argument("--extract-model", default="qwen2.5:3b")
    parser.add_argument("--qa-model", default="gemma3:4b")
    parser.add_argument("--limit", type=int, default=0, help="0 = all samples")
    parser.add_argument("--out", default=str(HERE / "results"))
    args = parser.parse_args()

    rows = [json.loads(line) for line in open(args.data, encoding="utf-8")]
    rows = rows[: args.limit] if args.limit else rows
    stats = {"extract": {"n": 0, "intent": 0, "exact": 0, "secs": 0.0},
             "qa": {"n": 0, "found_ok": 0, "found": 0, "grounded": 0, "secs": 0.0}}
    failures = []

    for row in rows:
        prompt, target = row["messages"][:2], json.loads(row["messages"][2]["content"])
        user = prompt[1]["content"]
        start = time.time()
        if row["task"] == "extract":
            got = chat(args.extract_model, prompt, EXTRACT_SCHEMA)
            s = stats["extract"]
            want_intent, want_slots = normalize(target, user)
            got_intent, got_slots = normalize(got, user)
            s["intent"] += got_intent == want_intent
            exact = got_intent == want_intent and got_slots == want_slots
            s["exact"] += exact
            if not exact:
                failures.append({"task": "extract", "input": user, "want": target, "got": got})
        else:
            got = chat(args.qa_model, prompt, business_qa.SCHEMA)
            s = stats["qa"]
            s["found_ok"] += bool(got.get("found")) == target["found"]
            if got.get("found"):
                s["found"] += 1
                s["grounded"] += numbers_in(got.get("answer", "")) <= numbers_in(business_qa.PROFILE) | numbers_in(user)
            if bool(got.get("found")) != target["found"]:
                failures.append({"task": "qa", "input": user, "want": target, "got": got})
        s["n"] += 1
        s["secs"] += time.time() - start

    e, q = stats["extract"], stats["qa"]
    report = {
        "extract_model": args.extract_model, "qa_model": args.qa_model, "samples": len(rows),
        "extract_intent_accuracy": round(e["intent"] / e["n"], 3) if e["n"] else None,
        "extract_exact_match": round(e["exact"] / e["n"], 3) if e["n"] else None,
        "extract_avg_seconds": round(e["secs"] / e["n"], 1) if e["n"] else None,
        "qa_found_accuracy": round(q["found_ok"] / q["n"], 3) if q["n"] else None,
        "qa_grounded_rate": round(q["grounded"] / q["found"], 3) if q["found"] else None,
        "qa_avg_seconds": round(q["secs"] / q["n"], 1) if q["n"] else None,
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    name = f"{args.extract_model}__{args.qa_model}".replace(":", "-").replace("/", "-")
    (out / f"{name}.json").write_text(json.dumps({"report": report, "failures": failures}, indent=2,
                                                  ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
