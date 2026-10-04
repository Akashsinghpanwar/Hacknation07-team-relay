"""One conversation: coffee price checks go to the deterministic engine, everything else to grounded business Q&A."""

import re

from coop_assistant.core import decision as engine
from coop_assistant.core.responses import SUPPORTED, T, render
from coop_assistant.core.store import connect
from coop_assistant.nlu import business_qa, extract


class Assistant:
    def __init__(self, conn=None, use_llm=True):
        self.conn = conn or connect()
        self.use_llm = use_llm
        self.reset()

    def reset(self):
        self.slots = engine.empty_slots()
        self.pending = False

    def _is_price_check(self, transcript):
        text = transcript.lower()
        raw = extract.regex_extract(transcript)
        if self.pending:
            return any(raw.get(k) for k in ("product_form", "grade", "district", "quote", "unit"))
        priced = re.search(extract.PRICE_WORDS, text) or raw.get("quote") or (raw.get("product_form") and raw.get("district"))
        context = raw.get("product_form") or raw.get("grade") or re.search(extract.BUYER_WORDS, text)
        return bool(priced and context)

    def _result(self, transcript, lang, method, decision, reply=None):
        return {"transcript": transcript, "lang": lang, "method": method, "decision": decision,
                "reply": reply or render(decision, lang)}

    def _decision(self, state, reason, intent, facts=None, evidence_id=None):
        return {"state": state, "reason": reason, "intent": intent, "slots": self.slots,
                "evidence_id": evidence_id, "facts": facts or {}}

    def handle(self, transcript, lang="en"):
        lang = lang if lang in SUPPORTED else "en"
        if not transcript.strip():
            return self._result(transcript, lang, None, self._decision("CLARIFY", "not_understood", "UNKNOWN"))
        if extract.regex_extract(transcript).get("intent") == "HUMAN":
            self.reset()
            return self._result(transcript, lang, "regex", self._decision("REFER", "human_requested", "HUMAN"))
        if not self._is_price_check(transcript):
            return self._business(transcript, lang)

        intent, new_slots, method = extract.extract(transcript, self.use_llm)
        if intent == "UNKNOWN" and self.pending and any(v is not None for v in new_slots.values()):
            intent = "PRICE_CHECK"
        if intent == "PRICE_CHECK" and not self.pending:
            self.slots = engine.empty_slots()
        self.slots = engine.merge(self.slots, new_slots)

        decision = engine.decide(intent, self.slots, self.conn)
        self.pending = decision["state"] == "CLARIFY"
        if not self.pending:
            self.slots = engine.empty_slots()
        return self._result(transcript, lang, method, decision)

    def _business(self, transcript, lang):
        self.reset()
        state, text = business_qa.answer(transcript, lang) if self.use_llm else ("NO_INFO", None)
        if state == "ANSWER":
            decision = self._decision("ANSWER", "business_info", "BUSINESS_QUESTION",
                                      {"source": business_qa.PROFILE_PATH.name}, "BUSINESS-PROFILE")
            return self._result(transcript, lang, "llm", decision, text)
        decision = self._decision("ABSTAIN", "no_info", "BUSINESS_QUESTION")
        return self._result(transcript, lang, "llm" if self.use_llm else None, decision, T[lang]["no_info"])
