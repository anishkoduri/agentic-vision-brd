"""Probe a video with ffprobe, then prove OpenCV can read one frame.

The detection batch calls require_readable and stops when this fails.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def ffprobe_bin() -> str:
    found = shutil.which("ffprobe")
    if found:
        return found
    import static_ffmpeg

    static_ffmpeg.add_paths()
    found = shutil.which("ffprobe")
    if not found:
        raise RuntimeError("ffprobe is not on PATH and static-ffmpeg did not provide it")
    return found


def probe_video(path: Path) -> dict:
    """Return codec metadata plus whether OpenCV read the first frame."""
    video = Path(path)
    if not video.is_file():
        raise FileNotFoundError(video)
    stream, fmt = _ffprobe(video)
    opened = _opencv_first_frame(video)
    width = _as_int(stream.get("width"))
    height = _as_int(stream.get("height"))
    shape_ok = opened["ok"] and opened["width"] == width and opened["height"] == height
    return {
        "path": str(video),
        "suffix": video.suffix.lower(),
        "format_name": fmt.get("format_name"),
        "duration_s": _as_float(fmt.get("duration")),
        "codec_name": stream.get("codec_name"),
        "codec_long_name": stream.get("codec_long_name"),
        "pix_fmt": stream.get("pix_fmt"),
        "width": width,
        "height": height,
        "avg_frame_rate": stream.get("avg_frame_rate"),
        "opencv_ok": bool(shape_ok),
        "opencv_error": "" if shape_ok else opened["error"] or "frame shape did not match ffprobe",
        "opencv_width": opened["width"],
        "opencv_height": opened["height"],
        "bytes": video.stat().st_size,
    }


def require_readable(records: list[dict]) -> None:
    """Raise before a batch if any .avi failed, or if nothing was probed."""
    if not records:
        raise RuntimeError("no video has been probed; the batch does not start")
    failed = [record for record in records if record.get("suffix") == ".avi" and not record.get("opencv_ok")]
    if not failed:
        return
    sample = failed[0]
    raise RuntimeError(
        f"{len(failed)} avi file(s) failed the OpenCV read; "
        f"codec={sample.get('codec_name')} error={sample.get('opencv_error')} path={sample.get('path')}"
    )


def probe_tree(root: Path) -> list[dict]:
    videos = sorted(path for path in Path(root).rglob("*") if path.suffix.lower() == ".avi" and path.is_file())
    return [probe_video(path) for path in videos]


def _ffprobe(video: Path) -> tuple[dict, dict]:
    output = subprocess.check_output(
        [
            ffprobe_bin(),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,codec_long_name,width,height,avg_frame_rate,pix_fmt:format=duration,format_name",
            "-of",
            "json",
            str(video),
        ],
        stderr=subprocess.STDOUT,
        timeout=120,
    )
    payload = json.loads(output.decode("utf-8"))
    streams = payload.get("streams") or []
    if not streams:
        raise RuntimeError(f"ffprobe found no video stream in {video.name}")
    return streams[0], payload.get("format") or {}


def _opencv_first_frame(video: Path) -> dict:
    import cv2

    capture = cv2.VideoCapture(str(video))
    try:
        if not capture.isOpened():
            return {"ok": False, "error": "VideoCapture did not open", "width": None, "height": None}
        ok, frame = capture.read()
        if not ok or frame is None:
            return {"ok": False, "error": "first frame read failed", "width": None, "height": None}
        height, width = frame.shape[:2]
        return {"ok": True, "error": "", "width": int(width), "height": int(height)}
    finally:
        capture.release()


def _as_int(value: object) -> int | None:
    if value is None or value == "N/A":
        return None
    return int(value)


def _as_float(value: object) -> float | None:
    if value is None or value == "N/A":
        return None
    return float(value)
