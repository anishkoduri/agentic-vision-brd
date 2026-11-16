"""Rank math. Fixtures are synthetic. They are not event video."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.risk import rank_minutes


def row(cow: str, day: int, minute: int, behavior: str, visible: bool = True, alone: bool = False) -> dict:
    return {
        "cow_id": cow,
        "day": day,
        "minute": minute,
        "behavior": behavior,
        "visible": visible,
        "alone": alone,
    }


def block(cow: str, day: int, start: int, count: int, behavior: str, visible: bool = True) -> list[dict]:
    return [row(cow, day, start + index, behavior, visible) for index in range(count)]


class RankTests(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual(rank_minutes([]), [])

    def test_unseen_cow_does_not_outrank_a_visible_drop(self) -> None:
        rows = []
        rows += block("lost", 1, 0, 4, "feeding")
        rows += block("lost", 1, 4, 20, "standing", visible=False)
        rows += block("lost", 2, 0, 4, "feeding")
        rows += block("lost", 2, 4, 20, "standing", visible=False)
        rows += block("steady", 1, 0, 20, "feeding")
        rows += block("steady", 2, 0, 20, "feeding")
        rows += block("dropped", 1, 0, 20, "feeding")
        rows += block("dropped", 2, 0, 4, "feeding")
        rows += block("dropped", 2, 4, 16, "standing")
        ranked = rank_minutes(rows)
        self.assertEqual(ranked[0]["cow_id"], "dropped")
        lost = next(card for card in ranked if card["cow_id"] == "lost")
        self.assertIsNone(lost["risk_visible"])
        self.assertEqual(lost["single_out"], "no")
        self.assertEqual(lost["rank"], None)
        self.assertGreater(lost["visible_fraction"], 0)
        self.assertLess(lost["visible_fraction"], 0.4)

    def test_shared_pen_drop_is_not_a_standout(self) -> None:
        rows = []
        for cow in ("a", "b"):
            rows += block(cow, 1, 0, 20, "feeding")
            rows += block(cow, 2, 0, 10, "feeding")
            rows += block(cow, 2, 10, 10, "standing")
        ranked = rank_minutes(rows)
        self.assertTrue(all(card["single_out"] == "no" for card in ranked))
        self.assertEqual(ranked[0]["single_out_reason"], "pen scores compressed")

    def test_change_minute_is_the_first_window_she_stops(self) -> None:
        rows = []
        rows += block("steady", 1, 0, 30, "feeding")
        rows += block("steady", 1, 600, 30, "feeding")
        rows += block("steady", 2, 0, 30, "feeding")
        rows += block("steady", 2, 600, 30, "feeding")
        rows += block("late", 1, 0, 30, "feeding")
        rows += block("late", 1, 600, 30, "feeding")
        rows += block("late", 2, 0, 30, "feeding")
        rows += block("late", 2, 600, 30, "standing")
        ranked = {card["cow_id"]: card for card in rank_minutes(rows)}
        self.assertEqual(ranked["late"]["change_minute"], 600)
        self.assertIsNone(ranked["steady"]["change_minute"])

    def test_close_feeding_gap_is_fragile(self) -> None:
        rows = []
        rows += block("more", 1, 0, 20, "feeding")
        rows += block("more", 2, 0, 20, "standing")
        rows += block("less", 1, 0, 20, "feeding")
        rows += block("less", 2, 0, 10, "feeding")
        rows += block("less", 2, 10, 10, "standing")
        ranked = rank_minutes(rows)
        self.assertEqual(ranked[0]["cow_id"], "more")
        self.assertEqual(ranked[0]["stability"], "fragile")
        self.assertLess(ranked[0]["minutes_to_swap"], 15)

    def test_skipped_herd_meal_is_named(self) -> None:
        rows = []
        cows = [f"c{index}" for index in range(7)] + ["skipper"]
        for cow in cows:
            rows.append(row(cow, 1, 0, "feeding"))
            behavior = "standing" if cow == "skipper" else "feeding"
            rows.append(row(cow, 2, 0, behavior))
        ranked = {card["cow_id"]: card for card in rank_minutes(rows)}
        self.assertEqual(ranked["skipper"]["meal_skips"], 1.0)
        self.assertEqual(ranked["c0"]["meal_skips"], 0.0)
        self.assertEqual(ranked["skipper"]["rank"], 1)

    def test_one_day_track_is_not_a_pen_rank(self) -> None:
        rows = block("clip-a", 1, 0, 6, "lying")
        ranked = rank_minutes(rows)
        self.assertEqual(ranked[0]["single_out"], "no")
        self.assertEqual(ranked[0]["single_out_reason"], "no day-over-day term")
        self.assertIsNone(ranked[0]["rank"])

    def test_one_hour_is_not_enough_to_single_her_out(self) -> None:
        rows = []
        rows += block("spike", 1, 0, 10, "feeding")
        rows += block("spike", 2, 0, 10, "standing")
        rows += block("steady", 1, 0, 10, "feeding")
        rows += block("steady", 2, 0, 10, "feeding")
        ranked = {card["cow_id"]: card for card in rank_minutes(rows)}
        self.assertEqual(ranked["spike"]["single_out"], "no")
        self.assertEqual(ranked["spike"]["single_out_reason"], "one hour holds the change")


if __name__ == "__main__":
    unittest.main()
