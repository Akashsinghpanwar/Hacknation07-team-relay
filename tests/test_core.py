import datetime as dt
import unittest
from unittest import mock

from coop_assistant.core import decision as engine
from coop_assistant.core.responses import SUPPORTED, render
from coop_assistant.core.store import connect
from coop_assistant.nlu import business_qa as qa
from coop_assistant.nlu.extract import normalize
from coop_assistant.pipeline import Assistant

TODAY = dt.date(2026, 10, 4)


def slots(**kw):
    s = engine.empty_slots()
    s.update(kw)
    return s


class DecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = connect(":memory:", TODAY)

    def decide(self, intent="PRICE_CHECK", **kw):
        return engine.decide(intent, slots(**kw), self.conn, TODAY)

    def test_valid_match_answers_with_evidence(self):
        d = self.decide(quote=105, product_form="parchment", grade="A", district="Nyeri")
        self.assertEqual(d["state"], "ANSWER")
        self.assertEqual(d["evidence_id"], "DEMO-NYR-PARCH-A")
        self.assertEqual(d["facts"]["difference"], -15)

    def test_stale_record_abstains(self):
        d = self.decide(product_form="parchment", grade="A", district="Kiambu")
        self.assertEqual((d["state"], d["reason"], d["evidence_id"]), ("ABSTAIN", "stale", None))

    def test_wrong_grade_abstains(self):
        d = self.decide(product_form="parchment", grade="B", district="Nyeri")
        self.assertEqual((d["state"], d["reason"]), ("ABSTAIN", "no_grade"))

    def test_wrong_unit_clarifies(self):
        d = self.decide(quote=5000, unit="bag", product_form="parchment", grade="A", district="Nyeri")
        self.assertEqual((d["state"], d["reason"]), ("CLARIFY", "unit"))

    def test_no_data_abstains(self):
        d = self.decide(product_form="parchment", grade="A", district="Murang'a")
        self.assertEqual((d["state"], d["reason"]), ("ABSTAIN", "no_data"))

    def test_sparse_abstains(self):
        d = self.decide(product_form="parchment", grade="A", district="Kirinyaga")
        self.assertEqual((d["state"], d["reason"]), ("ABSTAIN", "sparse"))

    def test_missing_grade_clarifies(self):
        d = self.decide(product_form="parchment", district="Nyeri")
        self.assertEqual(d["facts"]["missing"], ["grade"])

    def test_cherry_needs_no_grade(self):
        self.assertEqual(self.decide(product_form="cherry", district="Nyeri")["state"], "ANSWER")

    def test_human_and_out_of_scope(self):
        self.assertEqual(self.decide("HUMAN")["state"], "REFER")
        self.assertEqual(self.decide("UNKNOWN")["reason"], "out_of_scope")

    def test_foreign_currency_abstains(self):
        d = self.decide(currency="INR", product_form="cherry", district="Nyeri")
        self.assertEqual(d["reason"], "currency")


class GuardTests(unittest.TestCase):
    def test_llm_quote_must_be_spoken(self):
        _, s = normalize({"intent": "PRICE_CHECK", "quote": 999}, "buyer offered 105 per kg")
        self.assertIsNone(s["quote"])

    def test_llm_quote_dropped_when_no_digits_spoken(self):
        _, s = normalize({"intent": "PRICE_CHECK", "quote": 1}, "shilingi mia moja na tano")
        self.assertIsNone(s["quote"])

    def test_unknown_unit_is_ignored_not_clarified(self):
        _, s = normalize({"intent": "PRICE_CHECK", "unit": "cherries"}, "")
        self.assertIsNone(s["unit"])

    def test_non_latin_district_does_not_match_everything(self):
        _, s = normalize({"intent": "PRICE_CHECK", "district": "न्येरी"}, "")
        self.assertEqual(s["district"], "न्येरी")


class RenderTests(unittest.TestCase):
    def test_every_language_renders_every_outcome_with_exact_numbers(self):
        conn = connect(":memory:", TODAY)
        cases = [
            slots(quote=105, product_form="parchment", grade="A", district="Nyeri"),
            slots(product_form="parchment", grade="A", district="Kiambu"),
            slots(product_form="parchment", grade="B", district="Nyeri"),
            slots(product_form="parchment", grade="A", district="Murang'a"),
            slots(product_form="parchment", grade="A", district="Kirinyaga"),
            slots(product_form="parchment", district="Nyeri"),
            slots(unit="bag", product_form="cherry", district="Nyeri"),
            slots(product_form="cherry", district="Mombasa"),
        ]
        for lang in SUPPORTED:
            for s in cases:
                text = render(engine.decide("PRICE_CHECK", s, conn, TODAY), lang)
                self.assertTrue(text)
            answer = render(engine.decide("PRICE_CHECK", cases[0], conn, TODAY), lang)
            for number in ("120", "105", "15"):
                self.assertIn(number, answer, lang)
            for intent in ("HUMAN", "UNKNOWN"):
                self.assertTrue(render(engine.decide(intent, slots(), conn, TODAY), lang))


class ConversationTests(unittest.TestCase):
    def test_clarify_then_answer_offline(self):
        bot = Assistant(connect(":memory:"), use_llm=False)
        first = bot.handle("Buyer offered 105 shillings per kg for parchment coffee in Nyeri", "en")
        self.assertEqual(first["decision"]["facts"]["missing"], ["grade"])
        second = bot.handle("grade A", "en")
        self.assertEqual(second["decision"]["state"], "ANSWER")
        self.assertIn("15", second["reply"])

    def test_grade_next_to_cjk_text(self):
        bot = Assistant(connect(":memory:"), use_llm=False)
        r = bot.handle("买家给Nyeri的grade A羊皮纸咖啡豆每公斤出价105先令", "zh")
        self.assertEqual(r["decision"]["state"], "ANSWER")

    def test_non_price_question_goes_to_business_qa(self):
        bot = Assistant(connect(":memory:"), use_llm=False)
        r = bot.handle("My coffee leaves have brown spots, what disease is it?")
        self.assertEqual((r["decision"]["state"], r["decision"]["reason"]), ("ABSTAIN", "no_info"))

    def test_business_answer_is_used_when_grounded(self):
        bot = Assistant(connect(":memory:"))
        with mock.patch.object(qa, "_ask", return_value={"wants_human": False, "found": True,
                                                         "answer": "We're open 08:00 to 17:00 on weekdays."}):
            r = bot.handle("What time do you open?")
        self.assertEqual(r["decision"]["state"], "ANSWER")
        self.assertIn("17:00", r["reply"])

    def test_business_answer_with_invented_number_is_blocked(self):
        bot = Assistant(connect(":memory:"))
        with mock.patch.object(qa, "_ask", return_value={"wants_human": False, "found": True,
                                                         "answer": "Membership costs KES 750."}):
            r = bot.handle("How much is membership?")
        self.assertEqual(r["decision"]["reason"], "no_info")

    def test_talk_to_somebody_refers(self):
        bot = Assistant(connect(":memory:"), use_llm=False)
        self.assertEqual(bot.handle("Can I talk to somebody please?")["decision"]["state"], "REFER")

    def test_new_question_clears_pending_clarification(self):
        bot = Assistant(connect(":memory:"), use_llm=False)
        self.assertEqual(bot.handle("Buyer offered 105 for parchment in Nyeri")["decision"]["state"], "CLARIFY")
        self.assertEqual(bot.handle("When do you pay farmers?")["decision"]["reason"], "no_info")

    def test_delivery_time_with_cherry_word_is_not_price_check(self):
        bot = Assistant(connect(":memory:"), use_llm=False)
        self.assertEqual(bot.handle("Ninaweza kupeleka cherry saa ngapi?", "sw")["decision"]["reason"], "no_info")

    def test_short_price_check_without_price_word(self):
        bot = Assistant(connect(":memory:"), use_llm=False)
        self.assertEqual(bot.handle("Parchment grade A in Kiambu")["decision"]["reason"], "stale")

    def test_seedling_price_is_not_a_coffee_price_check(self):
        bot = Assistant(connect(":memory:"), use_llm=False)
        self.assertEqual(bot.handle("What is the price of seedlings?")["decision"]["reason"], "no_info")

    def test_human_request_refers(self):
        bot = Assistant(connect(":memory:"), use_llm=False)
        self.assertEqual(bot.handle("I want to talk to an officer")["decision"]["state"], "REFER")


if __name__ == "__main__":
    unittest.main()
