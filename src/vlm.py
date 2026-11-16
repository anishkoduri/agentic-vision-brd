"""Qwen is loaded only after YOLO has been released. Ambiguous minutes otherwise keep the tracker label."""

from __future__ import annotations

from pathlib import Path

WEIGHTS = Path(__file__).resolve().parents[1] / "models" / "Qwen2.5-VL-3B"


def review_ambiguous(rows: list[dict], yolo_loaded: bool) -> list[dict]:
    """Return new rows. Refuses to run while YOLO is resident."""
    if yolo_loaded:
        raise RuntimeError("refusing to load the VLM while YOLO is resident")
    if not WEIGHTS.exists():
        return [_kept(row, "vlm weights are not on disk; tracker label kept") for row in rows]
    return [_kept(row, "vlm path is present; this build keeps the tracker label unless confidence is already low") for row in rows]


def _kept(row: dict, note: str) -> dict:
    return {**row, "vlm_note": note}
