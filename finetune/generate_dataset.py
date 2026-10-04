"""Build chat-format SFT data for the two LLM tasks: multilingual slot extraction and grounded business Q&A.

Targets are produced by code from templates and data/business.json, so every label is exact.
Usage: python finetune/generate_dataset.py [--per-template 20] [--seed 7]
"""

import argparse
import json
import pathlib
import random

from coop_assistant.nlu import business_qa
from coop_assistant.nlu.extract import PROMPT as EXTRACT_PROMPT

OUT = pathlib.Path(__file__).parent / "data"
DISTRICTS = ["Nyeri", "Kiambu", "Murang'a", "Kirinyaga"]
NATIVE_NYERI = {"hi": "न्येरी", "zh": "涅里", "ko": "니에리"}

# (language, template, fields the template states). {q}=price, {g}=grade, {d}=district.
PRICE_TEMPLATES = [
    ("en", "The buyer offered {q} shillings per kg for grade {g} parchment coffee in {d}. Is that fair?",
     dict(form="parchment", grade=True, unit="kg", currency="KES")),
    ("en", "A trader wants to pay {q} per kilo for my cherry here in {d}.",
     dict(form="cherry", unit="kg")),
    ("en", "He offered {q} per bag for grade {g} parchment in {d}.",
     dict(form="parchment", grade=True, unit="bag")),
    ("en", "Someone offered me {q} for my parchment in {d}, what do you think?",
     dict(form="parchment")),
    ("hi", "व्यापारी ने {d} में ग्रेड {g} पार्चमेंट कॉफ़ी के लिए {q} शिलिंग प्रति किलो बोला है।",
     dict(form="parchment", grade=True, unit="kg", currency="KES")),
    ("hi", "{d} में चेरी के लिए खरीदार {q} शिलिंग किलो दे रहा है, ठीक है क्या?",
     dict(form="cherry", unit="kg", currency="KES")),
    ("sw", "Mnunuzi ametoa shilingi {q} kwa kilo kwa kahawa ya parchment daraja {g} huko {d}.",
     dict(form="parchment", grade=True, unit="kg", currency="KES")),
    ("sw", "Wanunuzi wanalipa shilingi {q} kwa kilo ya matunda ya kahawa huko {d}.",
     dict(form="cherry", unit="kg", currency="KES")),
    ("zh", "买家给{d}的{g}级羊皮纸咖啡豆每公斤出价{q}先令。",
     dict(form="parchment", grade=True, unit="kg", currency="KES")),
    ("zh", "在{d}，商人给咖啡鲜果每公斤{q}先令，合理吗？",
     dict(form="cherry", unit="kg", currency="KES")),
    ("ko", "구매자가 {d}의 {g}등급 파치먼트 커피에 kg당 {q}실링을 제시했어요.",
     dict(form="parchment", grade=True, unit="kg", currency="KES")),
    ("ko", "{d}에서 상인이 커피 체리를 킬로당 {q}실링에 사겠대요.",
     dict(form="cherry", unit="kg", currency="KES")),
]

HUMAN = [
    ("en", "Can I talk to an officer please?"), ("en", "I want to speak to a real person."),
    ("hi", "क्या मैं किसी अधिकारी से बात कर सकता हूँ?"), ("sw", "Naomba kuongea na afisa wa ushirika."),
    ("zh", "我想和工作人员通话。"), ("ko", "상담원과 통화하고 싶어요."),
]
UNKNOWN = [
    ("en", "What will the weather be like tomorrow?"), ("en", "My coffee leaves have brown spots."),
    ("hi", "कल बारिश होगी क्या?"), ("sw", "Mvua itanyesha kesho?"),
    ("zh", "明天天气怎么样？"), ("ko", "내일 날씨 어때요?"),
]


def _extract_sample(text, target):
    return {"task": "extract", "messages": [
        {"role": "system", "content": EXTRACT_PROMPT},
        {"role": "user", "content": text},
        {"role": "assistant", "content": json.dumps(target, ensure_ascii=False)},
    ]}


def extraction_samples(rng, per_template):
    rows = []
    for lang, template, spec in PRICE_TEMPLATES:
        for _ in range(per_template):
            q, g, d = rng.choice(range(60, 260, 5)), rng.choice("AB"), rng.choice(DISTRICTS)
            shown = NATIVE_NYERI[lang] if d == "Nyeri" and lang in NATIVE_NYERI and rng.random() < 0.3 else d
            rows.append(_extract_sample(template.format(q=q, g=g, d=shown), {
                "intent": "PRICE_CHECK", "quote": q, "currency": spec.get("currency"), "unit": spec.get("unit"),
                "product_form": spec["form"], "grade": g if spec.get("grade") else None, "district": d,
            }))
    empty = {"quote": None, "currency": None, "unit": None, "product_form": None, "grade": None, "district": None}
    rows += [_extract_sample(t, {"intent": "HUMAN", **empty}) for _, t in HUMAN]
    rows += [_extract_sample(t, {"intent": "UNKNOWN", **empty}) for _, t in UNKNOWN]
    return rows


def _qa_pairs(p):
    hours, intake, pay, member = p["opening_hours"], p["coffee_intake"], p["payments"], p["membership"]
    services = {s["name"]: s for s in p["services"]}
    seed = services["Seedling sales"]
    pairs = [
        (["What are your opening hours on weekdays?", "When are you open Monday to Friday?"],
         f"We're open Monday to Friday from {hours['monday_to_friday']}."),
        (["What time do you open on Saturday?", "Are you open on Saturdays?"],
         f"On Saturdays we're open from {hours['saturday']}."),
        (["Are you open on Sunday?", "Can I come on a public holiday?"],
         "Sorry, we're closed on Sundays and public holidays."),
        (["When can I deliver my cherry?", "What are the cherry delivery hours?"],
         f"You can deliver cherry {intake['cherry_delivery_hours']}, at the {intake['where'].lower()}."),
        (["When do you pay farmers?", "How do members get paid?"], f"{pay['schedule']}."),
        (["Can I get an advance?", "How much advance can I request?"], f"Yes. {pay['advance']}."),
        (["How do I get my delivery statement?", "Does a statement cost anything?"], f"{pay['statement']}."),
        (["How do I become a member?", "What do I need to join the co-op?"],
         f"{member['how']} with your {member['documents']}. There's a {member['fee']}."),
        (["How much is the joining fee?", "What does membership cost?"], f"It's a {member['fee']}."),
        (["Do you sell coffee seedlings?", "How much are seedlings?"],
         f"Yes, seedlings are {seed['price']}. {seed['details']}."),
        (["Can I get fertiliser on credit?", "How does fertiliser credit work?"],
         f"Yes, it's {services['Fertiliser on credit']['price'].lower()}. "
         f"{services['Fertiliser on credit']['details']}."),
        (["Can an extension officer visit my farm?", "How do I book an agronomy visit?"],
         f"Agronomy visits are {services['Agronomy visit']['price'].lower()}. "
         f"{services['Agronomy visit']['details']}."),
        (["Will you ever ask for my mobile money PIN?"], p["policies"][0]),
    ]
    negatives = ["Do you sell tractors?", "What is the interest rate on loans?", "How much is a bag of fertiliser?",
                 "Will it rain tomorrow?", "Can you pay my school fees?", "What's the price of maize?"]
    return pairs, negatives


def _qa_sample(question, answer, found):
    return {"task": "qa", "messages": [
        {"role": "system", "content": business_qa.SYSTEM},
        {"role": "user", "content": f"Caller: {question}\n\n(Write the answer in English.)"},
        {"role": "assistant", "content": json.dumps({"answer": answer if found else "", "found": found})},
    ]}


def qa_samples():
    pairs, negatives = _qa_pairs(json.loads(business_qa.PROFILE))
    rows = [_qa_sample(q, a, True) for questions, a in pairs for q in questions]
    return rows + [_qa_sample(q, "", False) for q in negatives]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-template", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--eval-fraction", type=float, default=0.15)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = extraction_samples(rng, args.per_template) + qa_samples()
    rng.shuffle(rows)
    cut = int(len(rows) * (1 - args.eval_fraction))
    OUT.mkdir(parents=True, exist_ok=True)
    for name, part in (("train", rows[:cut]), ("eval", rows[cut:])):
        with open(OUT / f"{name}.jsonl", "w", encoding="utf-8") as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in part)
        tasks = {t: sum(r["task"] == t for r in part) for t in ("extract", "qa")}
        print(f"{name}: {len(part)} samples {tasks}")


if __name__ == "__main__":
    main()
