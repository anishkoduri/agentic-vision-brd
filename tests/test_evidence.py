import unittest
from pathlib import Path

from src.evidence import (
    assessable, deviations, group_tracklets, herd_stats, reasons_text, top_anomalies,
)

ROOT = Path("/pen")


def _rows(clip: str, cow: str, behaviors: list[str], conf: float = 0.8) -> list[dict]:
    return [
        {"clip": str(ROOT / clip), "cow_id": cow, "day": "1", "minute": str(i), "behavior": b,
         "cameras": "back_cam", "confidence": str(conf)}
        for i, b in enumerate(behaviors)
    ]


def _herd() -> list[dict]:
    rows = []
    for i in range(12):  # varied peers so the spread is non-zero
        mix = ["standing"] * 3 + ["lying"] if i % 2 else ["lying"] * 3 + ["standing"]
        rows += _rows(f"c{i}.avi", "Cam 03-t1", mix)
    rows += _rows("odd.avi", "Cam 03-t2", ["walking"] * 4)
    rows += _rows("short.avi", "Cam 03-t3", ["walking", "walking"])
    rows += _rows("dim.avi", "Cam 03-t4", ["walking"] * 4, conf=0.2)
    return rows


class EvidenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tl = group_tracklets(_herd())
        self.stats = herd_stats(self.tl)
        self.by_clip = {Path(t["clip"]).name: t for t in self.tl}

    def test_short_and_low_confidence_tracklets_are_not_tested(self) -> None:
        self.assertFalse(assessable(self.by_clip["short.avi"]))
        self.assertFalse(assessable(self.by_clip["dim.avi"]))
        self.assertEqual(deviations(self.by_clip["short.avi"], self.stats), [])
        self.assertIn("not tested", reasons_text(self.by_clip["short.avi"], self.stats))

    def test_walking_tracklet_is_notable_with_minutes_vs_herd(self) -> None:
        text = reasons_text(self.by_clip["odd.avi"], self.stats)
        self.assertIn("walking 4 min vs herd mean", text)
        self.assertNotIn("no notable deviation", text)

    def test_typical_tracklet_has_no_notable_deviation(self) -> None:
        text = reasons_text(self.by_clip["c1.avi"], self.stats)
        self.assertTrue(text.startswith("no notable deviation from herd"))

    def test_top_anomaly_is_the_walking_tracklet(self) -> None:
        top = top_anomalies(self.tl, self.stats, 3)
        self.assertEqual(Path(top[0]["clip"]).name, "odd.avi")
        self.assertEqual(top[0]["behavior"], "walking")


if __name__ == "__main__":
    unittest.main()
