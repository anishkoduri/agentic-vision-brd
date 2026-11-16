import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.assemble import HERD_ID, write_budgets
from src.evidence import clip_link
from src.traces import VLM_STATEMENT, pick_traces, reexamined_pairs, render_markdown, trace_body


def row(cow, minute, behavior, conf, cam="back_cam"):
    return {"cow_id": cow, "day": 1, "minute": minute, "behavior": behavior, "cameras": cam, "confidence": conf}


class TraceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        cp = Path(self.tmp.name)
        # day: confirmed with a big gain; flipped and still weak; night: weak first read, flipped, strong second
        (cp / "A.json").write_text(json.dumps([row("Cam 01-t1", 600, "feeding", 0.2), row("Cam 01-t1", 600, "feeding", 0.8)]))
        (cp / "B.json").write_text(json.dumps([row("Cam 03-t1", 700, "standing", 0.3), row("Cam 03-t1", 700, "walking", 0.1)]))
        (cp / "C.json").write_text(json.dumps([row("Cam 03-t2", 30, "lying", 0.4), row("Cam 03-t2", 30, "standing", 0.8)]))
        (cp / "D.json").write_text(json.dumps([row("Cam 03-t9", 800, "lying", 0.9)]))  # never re-examined
        self.pairs = reexamined_pairs(cp)

    def test_only_repeated_keys_are_pairs(self):
        self.assertEqual(sorted(p["stem"] for p in self.pairs), ["A", "B", "C"])

    def test_picks(self):
        picks = pick_traces(self.pairs)
        self.assertEqual({k: v["stem"] for k, v in picks.items()}, {"success": "A", "failure": "B", "night": "C"})

    def test_markdown_has_all_six_elements_and_vlm_statement(self):
        for kind, pair in pick_traces(self.pairs).items():
            text = render_markdown(trace_body(kind, pair))
            for tag in ("(a)", "(b)", "(c)", "(d)", "(e)", "(f)"):
                self.assertIn(tag, text)
            self.assertIn(VLM_STATEMENT, text)
            self.assertIn("NOT invoked", text)


class ClipLinkTests(unittest.TestCase):
    def test_filename_only_clip_has_no_link(self):
        self.assertEqual(clip_link("Event20261107001407003.Avi", Path.cwd()), "`Event20261107001407003.Avi`")


class BudgetTests(unittest.TestCase):
    def test_herd_average_is_mean_over_active_tracks_with_zeros(self):
        rows = [
            {"cow_id": "t1", "day": 1, "minute": 600, "behavior": "lying"},
            {"cow_id": "t1", "day": 1, "minute": 601, "behavior": "lying"},
            {"cow_id": "t2", "day": 1, "minute": 600, "behavior": "standing"},
            {"cow_id": "t3", "day": 1, "minute": 30, "behavior": "lying"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "b.csv"
            write_budgets(rows, path)
            with path.open(encoding="utf-8") as handle:
                out = list(csv.DictReader(handle))
        herd = {(r["part"], r["behavior"]): (float(r["minutes"]), r["n_tracks"]) for r in out if r["cow_id"] == HERD_ID}
        self.assertEqual(herd[("day", "lying")], (1.0, "2"))      # 2 min over 2 day tracks
        self.assertEqual(herd[("day", "standing")], (0.5, "2"))
        self.assertEqual(herd[("night", "lying")], (1.0, "1"))
        self.assertEqual(herd[("night", "standing")], (0.0, "1"))


if __name__ == "__main__":
    unittest.main()
