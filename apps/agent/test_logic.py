import unittest

from stand_in_logic import HELP_TEXT, RateLimiter, build_request, classify, clip, respond


class Classify(unittest.TestCase):
    def test_greeting_and_short_messages_get_help(self):
        self.assertEqual(classify("hi"), "help")
        self.assertEqual(classify("what can you do"), "help")
        self.assertEqual(classify("prep me"), "help")

    def test_transcript_goes_to_followup(self):
        t = "Priya: we launch March 14\nSam: budget is approved\nPriya: Sam will send the plan by Friday"
        self.assertEqual(classify(t), "followup")
        self.assertEqual(classify("Please summarize this meeting: we talked about pricing and the roadmap"), "followup")

    def test_agenda_goes_to_prepare(self):
        self.assertEqual(classify("Tomorrow I meet the investors about the Falcon launch. Agenda: budget, timeline, hiring."), "prepare")


class Requests(unittest.TestCase):
    def test_prepare_and_followup_prompts(self):
        system, user = build_request("prepare", "agenda: budget")
        self.assertIn("LIKELY QUESTIONS", system)
        self.assertIn("untrusted data", system)
        self.assertEqual(user, "agenda: budget")
        self.assertIn("ACTION ITEMS", build_request("followup", "x")[0])

    def test_clip_removes_controls_and_bounds_size(self):
        self.assertEqual(clip("a\x00b\x07c"), "a b c")
        self.assertEqual(len(clip("x" * 50_000)), 20_000)


class Respond(unittest.TestCase):
    def test_help_needs_no_model(self):
        def boom(*a, **k):
            raise AssertionError("should not call Gemini")

        self.assertEqual(respond("hello", "k", "m", gemini=boom), HELP_TEXT)

    def test_calls_model_with_chosen_job(self):
        seen = {}

        def fake(system, user, key, model):
            seen.update(system=system, user=user, key=key, model=model)
            return "ok"

        text = "Tomorrow I meet the investors about Falcon. Agenda: budget, timeline."
        self.assertEqual(respond(text, "KEY", "gemini-x", gemini=fake), "ok")
        self.assertIn("BRIEFING", seen["system"])
        self.assertEqual((seen["key"], seen["model"]), ("KEY", "gemini-x"))

    def test_model_failure_gives_friendly_message(self):
        def fail(*a, **k):
            raise RuntimeError("secret upstream detail")

        out = respond("Tomorrow I meet the investors about Falcon. Agenda: budget.", "k", "m", gemini=fail)
        self.assertNotIn("secret", out)
        self.assertIn("try again", out)


class Limiter(unittest.TestCase):
    def test_limits_per_sender_per_window(self):
        rl = RateLimiter(limit=2, window_s=100)
        self.assertTrue(rl.allow("a", 0))
        self.assertTrue(rl.allow("a", 1))
        self.assertFalse(rl.allow("a", 2))
        self.assertTrue(rl.allow("b", 2))
        self.assertTrue(rl.allow("a", 200))


if __name__ == "__main__":
    unittest.main()
