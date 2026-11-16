"""Geometry labels. No GPU and no video."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.behavior import label_box, minute_row  # noqa: E402
from src.cameras import clip_info  # noqa: E402


class BehaviorTests(unittest.TestCase):
    def test_wide_box_is_lying(self) -> None:
        label = label_box((0, 0, 200, 80), None, "back_cam", 960, 540, 0.8, False)
        self.assertEqual(label["behavior"], "lying")
        self.assertEqual(label["evidence"], "observed")

    def test_front_bunk_band_is_feeding(self) -> None:
        label = label_box((100, 400, 180, 520), None, "front_cam_2", 640, 640, 0.9, False)
        self.assertEqual(label["behavior"], "feeding")

    def test_minute_mode_ignores_the_minority(self) -> None:
        samples = [
            {"behavior": "lying", "confidence": 0.8, "evidence": "observed", "alone": True},
            {"behavior": "lying", "confidence": 0.6, "evidence": "observed", "alone": True},
            {"behavior": "standing", "confidence": 0.5, "evidence": "observed", "alone": True},
        ]
        row = minute_row(samples)
        self.assertEqual(row["behavior"], "lying")
        self.assertTrue(row["visible"])

    def test_filename_tail_sets_the_camera_when_the_folder_does_not(self) -> None:
        info = clip_info(Path("Event20261107001918006.Avi"))
        self.assertEqual(info["camera"], "Cam 01")
        self.assertEqual(info["role"], "front_cam_1")
        self.assertEqual(info["day"], 1)
        self.assertEqual(info["minute"], 19)


if __name__ == "__main__":
    unittest.main()
