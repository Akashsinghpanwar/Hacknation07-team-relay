"""Turn a transcript in any language into validated slots. The LLM only extracts; it never answers."""

import json
import re
import urllib.request

from coop_assistant.config import EXTRACT_MODEL, OLLAMA_URL
from coop_assistant.core.store import DISTRICTS

SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ["PRICE_CHECK", "HUMAN", "UNKNOWN"]},
        "quote": {"type": ["number", "null"]},
        "currency": {"type": ["string", "null"]},
        "unit": {"type": ["string", "null"]},
        "product_form": {"type": ["string", "null"], "enum": ["cherry", "parchment", None]},
        "grade": {"type": ["string", "null"]},
        "district": {"type": ["string", "null"]},
    },
    "required": ["intent", "quote", "currency", "unit", "product_form", "grade", "district"],
}

PROMPT = f"""You extract fields from a coffee farmer's message. The message may be in any language.
Return JSON only. Use null for anything the farmer did not clearly say. Never guess or invent values.
- intent: PRICE_CHECK if they ask about a coffee price, a buyer's offer, or answer a follow-up with a
  coffee type, grade, district or price; HUMAN if they ask for a person, officer or operator; else UNKNOWN.
- quote: the price number the buyer offered, as a plain number.
- currency: as said (e.g. shillings, KES, rupees).
- unit: as said (e.g. kg, kilo, bag).
- product_form: "cherry" for fresh coffee cherry/berries, "parchment" for parchment coffee.
- grade: a grade letter such as A or B.
- district: one of {", ".join(DISTRICTS.values())}, written in English, if mentioned in any script."""


def numbers_in(text):
    return {float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text)}


def _norm_district(value):
    if not value:
        return None
    key = re.sub(r"[^a-z]", "", value.lower())
    for k, name in DISTRICTS.items():
        if key and (k in key or (len(key) >= 4 and key in k)):
            return name
    return value.strip().title()


def _norm_unit(value):
    if not value:
        return None
    v = value.lower()
    if re.search(r"kg|kilo|किलो|公斤|千克|킬로", v):
        return "kg"
    if re.search(r"bag|sack|gunia|debe|tin|ton|bori|बोरी|袋|포대", v):
        return v.strip()
    return None


def _norm_currency(value):
    if not value:
        return None
    v = value.lower()
    if re.search(r"kes|ksh|shilling|shilingi|bob|先令|실링|शिलिंग", v):
        return "KES"
    if re.search(r"rupee|rupaye|inr|₹|रुपय|रुपए", v):
        return "INR"
    return v.strip().upper()


def _norm_grade(value):
    if not value:
        return None
    m = re.search(r"\b([A-Ca-c])\b", value) or re.fullmatch(r"\s*([A-Ca-c])\s*", value)
    return m.group(1).upper() if m else None


def normalize(raw, transcript):
    intent = raw.get("intent") if raw.get("intent") in ("PRICE_CHECK", "HUMAN", "UNKNOWN") else "UNKNOWN"
    quote = raw.get("quote")
    said = numbers_in(transcript)
    if quote is not None:
        try:
            quote = float(quote)
        except (TypeError, ValueError):
            quote = None
    if quote is not None and quote not in said:
        quote = None
    form = raw.get("product_form")
    return intent, {
        "quote": quote,
        "currency": _norm_currency(raw.get("currency")),
        "unit": _norm_unit(raw.get("unit")),
        "product_form": form if form in ("cherry", "parchment") else None,
        "grade": _norm_grade(raw.get("grade")),
        "district": _norm_district(raw.get("district")),
    }


def llm_extract(transcript, timeout=60):
    body = json.dumps({
        "model": EXTRACT_MODEL,
        "stream": False,
        "keep_alive": "30m",
        "format": SCHEMA,
        "options": {"temperature": 0},
        "messages": [{"role": "system", "content": PROMPT}, {"role": "user", "content": transcript}],
    }).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(json.loads(resp.read())["message"]["content"])


HUMAN_WORDS = (r"human|person|somebody|someone|officer|operator|agent|talk to|speak to|इंसान|अधिकारी|व्यक्ति|किसी से बात"
               r"|\bmtu\b|afisa|人工|工作人员|真人|상담원|담당자")
BUYER_WORDS = r"buyer|trader|broker|offer|mnunuzi|wanunuzi|व्यापारी|खरीदार|买家|商人|구매자|상인"
FORM_WORDS = {
    "parchment": r"parchment|पार्चमेंट|羊皮纸|파치먼트",
    "cherry": r"cherry|cherries|berries|चेरी|matunda|鲜果|체리",
}
COFFEE_WORDS = r"coffee|kahawa|parchment|cherry|cherries|कॉफ़ी|कॉफी|पार्चमेंट|चेरी|咖啡|羊皮纸|커피|파치먼트|체리"
PRICE_WORDS =r"price|rate|offer|bei|भाव|रेट|दाम|价格|出价|가격"


def regex_extract(transcript):
    text = transcript.lower()
    if re.search(HUMAN_WORDS, text):
        return {"intent": "HUMAN"}
    nums = re.findall(r"\d[\d,]*(?:\.\d+)?", transcript)
    raw = {"quote": nums[0].replace(",", "") if nums else None}
    raw["product_form"] = next((f for f, p in FORM_WORDS.items() if re.search(p, text)), None)
    pricey = re.search(PRICE_WORDS, text) or nums or raw["product_form"]
    raw["intent"] = "PRICE_CHECK" if pricey else "UNKNOWN"
    grade = (re.search(r"(?:grade|daraja|ग्रेड)\s*([abc])(?![a-z])", text)
             or re.search(r"(?<![a-z])([abc])\s*(?:级|등급)", text))
    raw["grade"] = grade.group(1) if grade else None
    raw["district"] = next((name for key, name in DISTRICTS.items() if key in re.sub(r"[^a-z]", "", text)), None)
    unit = re.search(r"kg|kilo|किलो|公斤|킬로|bag|sack|gunia|debe", text)
    raw["unit"] = unit.group(0) if unit else None
    cur = re.search(r"kes|ksh|shilling|shilingi|rupee|rupaye|रुपय|先令|실링", text)
    raw["currency"] = cur.group(0) if cur else None
    return raw


def _complete(intent, slots):
    if intent == "HUMAN":
        return True
    needs_grade = slots["product_form"] == "parchment"
    return (intent == "PRICE_CHECK" and slots["product_form"] and slots["district"]
            and (slots["grade"] or not needs_grade))


def extract(transcript, use_llm=True):
    """Returns (intent, slots, method). Rules first; the LLM only when rules leave gaps."""
    intent, slots = normalize(regex_extract(transcript), transcript)
    if _complete(intent, slots) or not use_llm:
        return intent, slots, "regex"
    try:
        llm_intent, llm_slots = normalize(llm_extract(transcript), transcript)
    except (OSError, ValueError, KeyError):
        return intent, slots, "regex"
    return llm_intent, {k: llm_slots[k] if llm_slots[k] is not None else v for k, v in slots.items()}, "llm"
