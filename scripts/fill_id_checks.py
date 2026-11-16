"""One still every 30 minutes per camera. Skips a file that is already there. Does not run detection."""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cameras import clip_info  # noqa: E402
from src.remux import ffmpeg_bin  # noqa: E402

DATES = {1: "20261107", 2: "20261108"}
UNAVAILABLE = "no covering clip — frame not available"
DEST = ROOT / "outputs" / "batch" / "id-checks"


def main() -> int:
    grouped = _clips()
    slots = _slots(grouped)
    wrote = 0
    for slot in slots:
        if slot["status"] != "ready":
            continue
        dest = DEST / slot["file"]
        if dest.exists() and dest.stat().st_size > 0:
            slot["status"] = "kept"
            continue
        if _grab(Path(slot["source"]), float(slot["offset_s"]), dest):
            slot["status"] = "written"
            wrote += 1
        else:
            slot["status"] = "extract_failed"
    _index(slots)
    failed = sum(1 for slot in slots if slot["status"] in {UNAVAILABLE, "extract_failed"})
    print(f"slots={len(slots)} wrote={wrote} failed_or_missing={failed}")
    return 0 if failed == 0 else 1


def _clips() -> dict[tuple[int, str], list[dict]]:
    grouped: dict[tuple[int, str], list[dict]] = {}
    seen: set[str] = set()
    for path in (ROOT / "data" / "readable").rglob("*"):
        if path.suffix.lower() != ".avi":
            continue
        key = str(path.resolve()).lower()
        if key in seen:
            continue
        seen.add(key)
        info = clip_info(path)
        grouped.setdefault((info["day"], info["camera"]), []).append(info)
    return grouped


def _slots(grouped: dict[tuple[int, str], list[dict]]) -> list[dict]:
    slots: list[dict] = []
    for day in (1, 2):
        for camera in ("Cam 01", "Cam 02", "Cam 03"):
            for minute in range(0, 24 * 60, 30):
                slots.append(_one(grouped.get((day, camera), []), day, camera, minute))
    return slots


def _one(clips: list[dict], day: int, camera: str, minute: int) -> dict:
    cover = None
    for info in clips:
        if info["minute"] <= minute < info["minute"] + 5:
            if cover is None or info["minute"] > cover["minute"]:
                cover = info
    hour, mins = divmod(minute, 60)
    file_name = f"{camera}-{DATES[day]}-{hour:02d}{mins:02d}.jpg"
    if cover is None:
        return {"day": day, "camera": camera, "minute": minute, "file": file_name, "status": UNAVAILABLE, "source": "", "offset_s": ""}
    return {
        "day": day,
        "camera": camera,
        "minute": minute,
        "file": file_name,
        "status": "ready",
        "source": str(cover["path"]),
        "offset_s": (minute - cover["minute"]) * 60,
    }


def _grab(video: Path, offset_s: float, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    gpu = ["-hwaccel", "cuda", "-c:v", "hevc_cuvid"]
    if _ffmpeg(video, offset_s, dest, gpu):
        return True
    dest.unlink(missing_ok=True)
    return _ffmpeg(video, offset_s, dest, [])


def _ffmpeg(video: Path, offset_s: float, dest: Path, decoder: list[str]) -> bool:
    command = [
        ffmpeg_bin(),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{offset_s:.1f}",
        *decoder,
        "-i",
        str(video),
        "-frames:v",
        "1",
        "-q:v",
        "3",
        str(dest),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=90)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    return dest.exists() and dest.stat().st_size > 0


def _index(slots: list[dict]) -> None:
    path = DEST / "index.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("day", "camera", "minute", "file", "status", "source", "offset_s"))
        writer.writeheader()
        writer.writerows(slots)


if __name__ == "__main__":
    sys.exit(main())
