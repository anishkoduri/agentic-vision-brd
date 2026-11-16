"""ffprobe plus an OpenCV first-frame read. The batch cannot start without both."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.probe import probe_video, require_readable  # noqa: E402


def _ffmpeg() -> str:
    import static_ffmpeg

    static_ffmpeg.add_paths()
    from shutil import which

    binary = which("ffmpeg")
    if not binary:
        raise RuntimeError("ffmpeg was not installed into the project venv")
    return binary


def _write_avi(path: Path) -> None:
    frame = b"\x10\x80\x20" * (64 * 48)
    subprocess.run(
        [
            _ffmpeg(),
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            "64x48",
            "-r",
            "10",
            "-i",
            "pipe:0",
            "-frames:v",
            "5",
            "-c:v",
            "mpeg4",
            str(path),
        ],
        input=frame * 5,
        check=True,
        capture_output=True,
    )


class ProbeTests(unittest.TestCase):
    def test_mpeg4_avi_is_probed_and_opened_by_opencv(self) -> None:
        path = ROOT / "outputs" / "ingest" / "fixture-mpeg4.avi"
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_avi(path)
        record = probe_video(path)
        self.assertEqual(record["suffix"], ".avi")
        self.assertEqual(record["codec_name"], "mpeg4")
        self.assertEqual(record["width"], 64)
        self.assertEqual(record["height"], 48)
        self.assertTrue(record["opencv_ok"], record["opencv_error"])
        self.assertEqual(record["opencv_width"], 64)
        self.assertEqual(record["opencv_height"], 48)
        require_readable([record])

    def test_missing_file_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            probe_video(ROOT / "outputs" / "ingest" / "no-such-file.avi")

    def test_batch_refuses_a_failed_opencv_read(self) -> None:
        bad = {"path": "night.avi", "suffix": ".avi", "codec_name": "h264", "opencv_ok": False, "opencv_error": "no frame"}
        with self.assertRaises(RuntimeError) as caught:
            require_readable([bad])
        self.assertIn("h264", str(caught.exception))

    def test_batch_refuses_when_no_avi_has_been_probed(self) -> None:
        with self.assertRaises(RuntimeError):
            require_readable([])


if __name__ == "__main__":
    unittest.main()
