"""Camera roles from the pen-map comparison on 2026-11-15.

Cam 03 looks from the rear toward the bunk shelter, so it is the back cam.
Cam 01 sits under the bunk roof and looks down the pen, chute side on the left.
Cam 02 is the other bunk camera: the trough fills the frame.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

ROLES = {
    "Cam 01": "front_cam_1",
    "Cam 02": "front_cam_2",
    "Cam 03": "back_cam",
}
TAILS = {"006": "Cam 01", "017": "Cam 02", "003": "Cam 03"}
_EVENT = re.compile(r"Event(\d{14})(\d{3})", re.IGNORECASE)


def clip_info(path: Path) -> dict:
    """Day, camera folder, role, and minute-of-day from a path or an Event filename."""
    video = Path(path)
    day_folder = next((part for part in video.parts if part.startswith("Day ")), "")
    cam_folder = next((part for part in video.parts if part.startswith("Cam ")), "")
    match = _EVENT.search(video.name)
    if not match:
        raise ValueError(f"not an event clip: {video.name}")
    stamp = datetime.strptime(match.group(1), "%Y%m%d%H%M%S")
    tail = match.group(2)
    camera = cam_folder or TAILS.get(tail, "")
    if not camera:
        raise ValueError(f"no camera for tail {tail} in {video.name}")
    day = 1 if stamp.day == 7 or day_folder == "Day 1" else 2
    if day_folder == "Day 1":
        day = 1
    elif day_folder == "Day 2":
        day = 2
    return {
        "path": video,
        "camera": camera,
        "role": ROLES[camera],
        "day": day,
        "minute": stamp.hour * 60 + stamp.minute,
        "stamp": stamp,
        "tail": tail,
    }
