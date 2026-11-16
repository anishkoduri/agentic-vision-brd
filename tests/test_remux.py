"""The hvc1 remux is a stream copy. OpenCV must open the copy; the source stays."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.probe import probe_video  # noqa: E402
from src.remux import remux_argv, remux_file  # noqa: E402


class RemuxTests(unittest.TestCase):
    def test_command_copies_and_retags_hvc1(self) -> None:
        argv = remux_argv("ffmpeg", Path("in.Avi"), Path("out.avi"))
        self.assertEqual(argv[argv.index("-c") + 1], "copy")
        self.assertEqual(argv[argv.index("-tag:v") + 1], "hvc1")
        self.assertNotIn("libx265", argv)
        self.assertNotIn("libx264", argv)

    def test_one_event_clip_opens_after_remux(self) -> None:
        matches = list(Path(ROOT / "data" / "raw").rglob("Event20261108214940017.Avi"))
        if not matches:
            self.skipTest("sample clip is not unpacked")
        source = matches[0]
        before = source.stat().st_size
        dest = ROOT / "outputs" / "ingest" / "remux-one.avi"
        if dest.exists():
            dest.unlink()
        remux_file(source, dest)
        self.assertEqual(source.stat().st_size, before)
        record = probe_video(dest)
        self.assertEqual(record["codec_name"], "hevc")
        self.assertTrue(record["opencv_ok"], record["opencv_error"])
        self.assertEqual(record["opencv_width"], 2592)
        self.assertEqual(record["opencv_height"], 1944)


if __name__ == "__main__":
    unittest.main()
