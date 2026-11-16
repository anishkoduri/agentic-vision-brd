"""One behavior label from a cow box. Geometry only. A score is not a diagnosis."""

from __future__ import annotations

FEEDING = "feeding"
LYING = "lying"
WALKING = "walking"
STANDING = "standing"
NOT_VISIBLE = "other / not visible"


def label_box(
    box: tuple[float, float, float, float],
    previous: tuple[float, float] | None,
    role: str,
    width: int,
    height: int,
    confidence: float,
    neighbor: bool,
) -> dict:
    """Return a new label dict. Lying, walking, then bunk position."""
    x1, y1, x2, y2 = box
    box_w = max(x2 - x1, 1.0)
    box_h = max(y2 - y1, 1.0)
    center = ((x1 + x2) / 2.0 / width, (y1 + y2) / 2.0 / height)
    moved = _moved(center, previous)
    aspect = box_w / box_h
    behavior, evidence = _pick(center[1], aspect, moved, role)
    conf = confidence if evidence == "observed" else min(confidence, 0.4)
    return {
        "behavior": behavior,
        "confidence": round(conf, 4),
        "evidence": evidence,
        "visible": True,
        "alone": not neighbor,
        "center": center,
    }


def minute_row(samples: list[dict]) -> dict:
    """Mode of the samples in one minute. Empty input is not visible."""
    if not samples:
        return {
            "behavior": NOT_VISIBLE,
            "confidence": 0.0,
            "evidence": "observed",
            "visible": False,
            "alone": True,
        }
    counts: dict[str, int] = {}
    for sample in samples:
        counts[sample["behavior"]] = counts.get(sample["behavior"], 0) + 1
    behavior = max(counts, key=lambda name: (counts[name], name))
    chosen = [sample for sample in samples if sample["behavior"] == behavior]
    confidence = sum(sample["confidence"] for sample in chosen) / len(chosen)
    evidence = "estimated" if any(sample["evidence"] == "estimated" for sample in chosen) else "observed"
    return {
        "behavior": behavior,
        "confidence": round(confidence, 4),
        "evidence": evidence,
        "visible": True,
        "alone": all(sample["alone"] for sample in chosen),
    }


def _pick(y_norm: float, aspect: float, moved: float, role: str) -> tuple[str, str]:
    if moved > 0.05:
        return WALKING, "observed"
    if aspect >= 1.35:
        return LYING, "observed"
    if role.startswith("front") and y_norm > 0.62:
        return FEEDING, "observed"
    if role == "back_cam" and y_norm < 0.28:
        return FEEDING, "estimated"
    return STANDING, "observed"


def _moved(center: tuple[float, float], previous: tuple[float, float] | None) -> float:
    if previous is None:
        return 0.0
    dx = center[0] - previous[0]
    dy = center[1] - previous[1]
    return (dx * dx + dy * dy) ** 0.5
