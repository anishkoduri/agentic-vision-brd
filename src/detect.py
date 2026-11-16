"""Sample 1 frame / 10 s and track cows. One YOLO model. No VLM in this module."""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.behavior import label_box, minute_row
from src.cameras import clip_info
from src.remux import ffmpeg_bin

COW = 19
WEIGHTS = "yolo11s.pt"
FRAME = "640x480"
COARSE_S = 10.0


def require_gpu() -> str:
    """Refuse the batch unless this process sees the RTX 4060."""
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available; the batch does not start on CPU")
    name = torch.cuda.get_device_name(0)
    if "4060" not in name:
        raise RuntimeError(f"expected the RTX 4060 Laptop, found {name}")
    return name


def load_yolo():
    from ultralytics import YOLO

    model = YOLO(WEIGHTS)
    model.to("cuda")
    return model


def release_yolo(model) -> None:
    import torch

    del model
    torch.cuda.empty_cache()


def sample_frames(video: Path, dest: Path, every_s: float = COARSE_S) -> list[Path]:
    """Write scaled JPEGs. The original video is not modified."""
    return _sample(video, dest, f"fps=1/{every_s}" if every_s >= 1 else f"fps={1.0 / every_s}", "f%04d.jpg")


def sample_window(video: Path, dest: Path, start_s: float) -> list[Path]:
    """3 fps for 4 seconds. Used only when a coarse box is under 0.45 confidence."""
    dest.mkdir(parents=True, exist_ok=True)
    pattern = dest / "d%04d.jpg"
    try:
        _ffmpeg(
            [
                "-ss",
                f"{start_s:.1f}",
                "-t",
                "4",
                "-hwaccel",
                "cuda",
                "-c:v",
                "hevc_cuvid",
                "-resize",
                FRAME,
                "-i",
                str(video),
                "-vf",
                "fps=3",
                "-q:v",
                "8",
                str(pattern),
            ],
            leading_input=False,
        )
    except subprocess.CalledProcessError:
        _clear_frames(dest, "d")
        _ffmpeg(
            ["-ss", f"{start_s:.1f}", "-t", "4", "-i", str(video), "-vf", "fps=3,scale=640:-2", "-q:v", "8", str(pattern)],
            leading_input=False,
        )
    return sorted(dest.glob("d*.jpg"))


def track_frames(model, frames: list[Path], tracker: str = "bytetrack.yaml") -> list[list[dict]]:
    """One list of boxes per frame. One tracker pass for the whole clip."""
    if not frames:
        return []
    model.predictor = None
    results = model.track(
        source=[str(frame) for frame in frames],
        persist=True,
        tracker=tracker,
        classes=[COW],
        verbose=False,
        device=0,
        half=True,
        imgsz=640,
        stream=True,
    )
    return [_boxes(result) for result in results]


def rows_for_clip(
    info: dict,
    frames: list[Path],
    tracks: list[list[dict]],
    step_s: float = COARSE_S,
    origin_s: float = 0.0,
) -> list[dict]:
    """Minute rows for one clip. cow_id is the track id inside this camera."""
    by_minute: dict[tuple[str, int], list[dict]] = {}
    previous: dict[int, tuple[float, float]] = {}
    width, height = _size(frames[0]) if frames else (640, 480)
    for index, boxes in enumerate(tracks):
        minute = info["minute"] + int((origin_s + index * step_s) // 60)
        centers = [_center(box["box"], width, height) for box in boxes]
        for box in boxes:
            center = _center(box["box"], width, height)
            neighbor = any(_close(center, other) for other in centers if other != center)
            label = label_box(box["box"], previous.get(box["id"]), info["role"], width, height, box["conf"], neighbor)
            previous[box["id"]] = label["center"]
            cow_id = f"{info['camera']}-t{box['id']}"
            by_minute.setdefault((cow_id, minute), []).append(label)
    built: list[dict] = []
    for (cow_id, minute), samples in sorted(by_minute.items()):
        summary = minute_row(samples)
        built.append({
            "cow_id": cow_id,
            "day": info["day"],
            "minute": minute,
            "behavior": summary["behavior"],
            "cameras": info["role"],
            "confidence": summary["confidence"],
            "visible": summary["visible"],
            "evidence": summary["evidence"],
            "alone": summary["alone"],
            "clip": str(info["path"]),
        })
    return built


def _sample(video: Path, dest: Path, rate: str, name: str) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    pattern = str(dest / name)
    try:
        _ffmpeg(
            ["-hwaccel", "cuda", "-c:v", "hevc_cuvid", "-resize", FRAME, "-i", str(video), "-vf", rate, "-q:v", "8", pattern],
            leading_input=False,
        )
    except subprocess.CalledProcessError:
        _clear_frames(dest, name[0])
        _ffmpeg([str(video), "-vf", f"{rate},scale=640:-2", "-q:v", "8", pattern])
    return sorted(dest.glob(f"{name[0]}*.jpg"))


def _ffmpeg(tail: list[str], leading_input: bool = True) -> None:
    head = ["-i"] if leading_input else []
    subprocess.run(
        [ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", *head, *tail],
        check=True,
        capture_output=True,
        timeout=600,
    )


def _clear_frames(dest: Path, prefix: str) -> None:
    for path in dest.glob(f"{prefix}*.jpg"):
        path.unlink()


def _boxes(result) -> list[dict]:
    boxes = result.boxes
    if boxes is None or boxes.xyxy is None or len(boxes) == 0:
        return []
    found: list[dict] = []
    ids = boxes.id
    for index, xyxy in enumerate(boxes.xyxy.tolist()):
        track_id = index if ids is None else int(ids[index])
        found.append({"id": track_id, "box": tuple(xyxy), "conf": float(boxes.conf[index])})
    return found


def _size(frame: Path) -> tuple[int, int]:
    import cv2

    image = cv2.imread(str(frame))
    if image is None:
        raise RuntimeError(f"could not read {frame.name}")
    height, width = image.shape[:2]
    return width, height


def _center(box: tuple[float, float, float, float], width: int, height: int) -> tuple[float, float]:
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2.0 / width, (y1 + y2) / 2.0 / height)


def _close(a: tuple[float, float], b: tuple[float, float]) -> bool:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return (dx * dx + dy * dy) ** 0.5 < 0.12
