import unittest

from src.assemble import dedupe_second_look


def row(clip, cow, minute, behavior, conf):
    return {"clip": clip, "cow_id": cow, "minute": minute, "behavior": behavior, "confidence": conf}


class DedupeTests(unittest.TestCase):
    def test_second_look_replaces_coarse_in_place(self):
        rows = [row("a", "t1", 5, "standing", 0.3), row("a", "t2", 5, "lying", 0.9), row("a", "t1", 5, "walking", 0.8)]
        out = dedupe_second_look(rows)
        self.assertEqual([(r["cow_id"], r["behavior"]) for r in out], [("t1", "walking"), ("t2", "lying")])

    def test_same_track_minute_in_other_clip_is_kept(self):
        rows = [row("a", "t1", 5, "standing", 0.3), row("b", "t1", 5, "standing", 0.3)]
        self.assertEqual(len(dedupe_second_look(rows)), 2)

    def test_input_is_not_mutated(self):
        rows = [row("a", "t1", 5, "standing", 0.3), row("a", "t1", 5, "walking", 0.8)]
        dedupe_second_look(rows)
        self.assertEqual(rows[0]["behavior"], "standing")


if __name__ == "__main__":
    unittest.main()
