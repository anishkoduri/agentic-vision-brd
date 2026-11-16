"""Clip-level tracklet evidence from activity rows.

A tracklet is one tracker number inside one clip. Tracker numbers restart in
every clip, so nothing here follows an animal between clips or identifies a cow.
Rows may be raw CSV strings or typed values.
"""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote

BEHAVIORS = ("standing", "lying", "feeding", "walking")
CAMERAS = ("front_cam_1", "front_cam_2", "back_cam")
MIN_TRACKLET_MINUTES = 4  # clips are short; fewer minutes give noisy shares
MIN_MEAN_CONF = 0.5  # skip tracklets whose boxes are mostly low-confidence
MIN_PEERS = 10  # peers needed per camera/day/behavior to trust a mean and spread
NOTABLE_Z = 3.0

Stats = dict[tuple[str, int, str], tuple[float, float]]


def qualified_id(clip: str, cow_id: str) -> str:
    return f"{Path(clip).stem}|{cow_id}"


def group_tracklets(rows: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["clip"], row["cow_id"])].append(row)
    out = []
    for (clip, cow), rs in groups.items():
        rs = sorted(rs, key=lambda r: int(r["minute"]))
        counts = Counter(r["behavior"] for r in rs)
        out.append({
            "clip": clip, "cow_id": cow, "track": cow.split("-t")[-1],
            "camera": rs[0]["cameras"], "day": int(rs[0]["day"]), "rows": rs, "n": len(rs),
            "counts": {b: counts[b] for b in BEHAVIORS},
            "share": {b: counts[b] / len(rs) for b in BEHAVIORS},
            "mean_conf": statistics.fmean(float(r["confidence"]) for r in rs),
        })
    return out


def assessable(t: dict) -> bool:
    return t["n"] >= MIN_TRACKLET_MINUTES and t["mean_conf"] >= MIN_MEAN_CONF


def herd_stats(tracklets: list[dict]) -> Stats:
    """Mean and spread of each behavior share, per camera and day, over assessable tracklets."""
    stats: Stats = {}
    peers_by = defaultdict(list)
    for t in tracklets:
        if assessable(t):
            peers_by[(t["camera"], t["day"])].append(t)
    for (cam, day), peers in peers_by.items():
        for b in BEHAVIORS:
            xs = [t["share"][b] for t in peers]
            if len(xs) >= MIN_PEERS and statistics.pstdev(xs) > 0:
                stats[(cam, day, b)] = (statistics.fmean(xs), statistics.pstdev(xs))
    return stats


def deviations(t: dict, stats: Stats) -> list[dict]:
    """Per-behavior comparison with the camera-day herd. Empty if the tracklet cannot be tested."""
    if not assessable(t):
        return []
    out = []
    for b in BEHAVIORS:
        key = (t["camera"], t["day"], b)
        if key not in stats:
            continue
        mean, sd = stats[key]
        out.append({
            "behavior": b, "minutes": t["counts"][b], "share": t["share"][b],
            "herd_mean": mean, "expected_minutes": mean * t["n"], "z": (t["share"][b] - mean) / sd,
        })
    return out


def most_extreme(t: dict, stats: Stats) -> dict | None:
    """The behavior this tracklet spends time in that sits furthest above the herd."""
    present = [d for d in deviations(t, stats) if d["minutes"] > 0]
    return max(present, key=lambda d: d["z"], default=None)


def top_anomalies(tracklets: list[dict], stats: Stats, k: int, cameras=CAMERAS) -> list[dict]:
    """Highest-z tracklets among `cameras`, at most one per clip."""
    scored = []
    for t in tracklets:
        if t["camera"] not in cameras:
            continue
        best = most_extreme(t, stats)
        if best:
            scored.append({**t, **best})
    scored.sort(key=lambda t: -t["z"])
    picked, seen = [], set()
    for t in scored:
        if t["clip"] in seen:
            continue
        seen.add(t["clip"])
        picked.append(t)
        if len(picked) == k:
            break
    return picked


def clock(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


def first_minute(t: dict) -> str:
    row = next(r for r in t["rows"] if r["behavior"] == t["behavior"])
    return clock(int(row["minute"]))


def clip_link(clip: str, root: Path) -> str:
    # activity.csv now holds the clip filename only, and the video is not in the zip: no link to make
    if not Path(clip).is_absolute():
        return f"`{clip}`"
    rel = Path(clip).relative_to(root).as_posix()
    return f"[{Path(clip).name}](../{quote(rel)})"


def reasons_text(t: dict, stats: Stats) -> str:
    """Observed-feature text for one tracklet, for the top_reasons column."""
    devs = deviations(t, stats)
    if not devs:
        return (f"no notable deviation from herd (not tested: {t['n']} tracked min, "
                f"mean confidence {t['mean_conf']:.2f}; needs ≥{MIN_TRACKLET_MINUTES} min and ≥{MIN_MEAN_CONF})")
    notable = sorted((d for d in devs if abs(d["z"]) >= NOTABLE_Z), key=lambda d: -abs(d["z"]))
    if not notable:
        return "no notable deviation from herd"
    where = f"{t['n']} tracked min, Day {t['day']}, {t['camera']}"
    parts = [
        f"{d['behavior']} {d['minutes']} min vs herd mean {d['expected_minutes']:.1f} min (z={d['z']:+.1f})"
        for d in notable
    ]
    return "; ".join(parts) + f" [{where}]"
