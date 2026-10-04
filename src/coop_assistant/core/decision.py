"""Deterministic decision engine: every ANSWER is backed by exactly one stored record."""

import datetime as dt

from coop_assistant.core.store import DISTRICTS

MIN_SAMPLES = 3
SLOT_NAMES = ("quote", "currency", "unit", "product_form", "grade", "district")


def empty_slots():
    return {name: None for name in SLOT_NAMES}


def merge(previous, new):
    """Carry earlier answers forward so a CLARIFY turn only needs the missing field."""
    merged = dict(previous or empty_slots())
    merged.update({k: v for k, v in new.items() if k in SLOT_NAMES and v is not None})
    return merged


def _missing(slots):
    needed = ["product_form", "district"]
    if slots.get("product_form") == "parchment":
        needed.append("grade")
    return [name for name in needed if not slots.get(name)]


def decide(intent, slots, conn, today=None):
    today = today or dt.date.today()
    out = {"state": None, "intent": intent, "slots": slots, "evidence_id": None, "reason": None, "facts": {}}

    if intent == "HUMAN":
        return dict(out, state="REFER", reason="human_requested")
    if intent != "PRICE_CHECK":
        return dict(out, state="ABSTAIN", reason="out_of_scope")

    missing = _missing(slots)
    if missing:
        return dict(out, state="CLARIFY", reason="missing", facts={"missing": missing})
    if slots.get("unit") not in (None, "kg"):
        return dict(out, state="CLARIFY", reason="unit")
    if slots.get("currency") not in (None, "KES"):
        return dict(out, state="ABSTAIN", reason="currency")
    if slots["district"] not in DISTRICTS.values():
        return dict(out, state="ABSTAIN", reason="unknown_district")

    grade = slots["grade"] if slots["product_form"] == "parchment" else "ungraded"
    rows = conn.execute(
        "SELECT * FROM prices WHERE crop='coffee' AND district=? AND product_form=? AND unit='kg'",
        (slots["district"], slots["product_form"]),
    ).fetchall()
    if not rows:
        return dict(out, state="ABSTAIN", reason="no_data", facts={"district": slots["district"]})
    match = next((r for r in rows if r["grade"] == grade), None)
    if match is None:
        return dict(out, state="ABSTAIN", reason="no_grade", facts={"grade": grade})

    facts = {
        "record_id": match["id"],
        "reference": match["price_value"],
        "currency": match["currency"],
        "unit": match["unit"],
        "market": match["market"],
        "district": match["district"],
        "product_form": match["product_form"],
        "grade": match["grade"],
        "observed_at": match["observed_at"],
        "valid_until": match["valid_until"],
        "sample_count": match["sample_count"],
        "source": match["source_name"],
    }
    if dt.date.fromisoformat(match["valid_until"]) < today:
        return dict(out, state="ABSTAIN", reason="stale", facts=facts)
    if match["sample_count"] < MIN_SAMPLES:
        return dict(out, state="ABSTAIN", reason="sparse", facts=facts)

    if slots.get("quote") is not None:
        facts["quote"] = float(slots["quote"])
        facts["difference"] = round(facts["quote"] - facts["reference"], 2)
    return dict(out, state="ANSWER", reason="matched", evidence_id=match["id"], facts=facts)
