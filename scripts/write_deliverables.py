"""Rebuild risk, budgets, and traces from the finished batch. Does not read video."""

from __future__ import annotations

import csv
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.assemble import HERD_ID, write_budgets  # noqa: E402
from src.evidence import (  # noqa: E402
    assessable, clip_link, first_minute, group_tracklets, herd_stats, qualified_id, reasons_text,
    top_anomalies,
)
from src.risk import rank_minutes  # noqa: E402
from src.traces import write_traces  # noqa: E402

BATCH = ROOT / "outputs" / "batch"


def main() -> int:
    rows = _load(BATCH / "activity.csv")
    _archive()
    qualified = [_qualify(row) for row in rows]
    cards = rank_minutes(qualified)
    tracklets = group_tracklets(rows)
    stats = herd_stats(tracklets)
    observed = {qualified_id(t["clip"], t["cow_id"]): reasons_text(t, stats) for t in tracklets}
    _write_risk(cards, BATCH / "brd_risk.csv", observed)
    write_budgets(qualified, BATCH / "time_budgets.csv")
    _write_camera_budgets(rows, BATCH / "time_budgets_by_camera.csv")
    write_traces(BATCH / "checkpoints", BATCH / "frames", BATCH / "traces")
    empty = _empty_checkpoints()
    (BATCH / "empty_clips.txt").write_text("\n".join(empty) + ("\n" if empty else ""), encoding="utf-8")
    summary = _summary(rows, cards, empty)
    (BATCH / "deliverable-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_cards(tracklets, stats, summary, ROOT / "docs" / "risk-cards.md")
    print(json.dumps(summary))
    return 0


def _load(path: Path) -> list[dict]:
    loaded: list[dict] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for raw in csv.DictReader(handle):
            loaded.append({
                **raw,
                "day": int(raw["day"]),
                "minute": int(raw["minute"]),
                "confidence": float(raw["confidence"]),
                "visible": raw["visible"] == "True",
                "alone": raw["alone"] == "True",
            })
    return loaded


def _qualify(row: dict) -> dict:
    stem = Path(row["clip"]).stem
    return {**row, "cow_id": f"{stem}|{row['cow_id']}"}


def _archive() -> None:
    dest = BATCH / "audit"
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("brd_risk.csv", "time_budgets.csv"):
        source = BATCH / name
        target = dest / name
        if source.exists() and not target.exists():
            shutil.copyfile(source, target)


def _write_risk(cards: list[dict], path: Path, observed: dict[str, str]) -> None:
    fields = (
        "cow_id",
        "score",
        "rank",
        "top_reasons",
        "single_out",
        "single_out_reason",
        "visible_fraction",
        "risk_all",
        "stability",
    )
    body = []
    for card in cards:
        score = card["risk_visible"]
        body.append({
            **card,
            "score": "" if score is None else score,
            "rank": "" if card["rank"] is None else card["rank"],
            "top_reasons": observed[card["cow_id"]],
        })
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(body)


CAMERA_FIELDS = ("day", "camera", "part", "behavior", "track_minutes", "n_tracks", "mean_minutes_per_track")
HERD_CAMERA = f"all_cameras ({HERD_ID})"


def _write_camera_budgets(rows: list[dict], path: Path) -> None:
    """Track-minutes by day, camera, and clock part (night = 20:00-06:00), with per-track means.

    `n_tracks` counts clip-qualified tracks active in that group, so the mean is per track, not per
    cow. The HERD_CAMERA rows pool all cameras and match the HERD_AVERAGE rows in time_budgets.csv.
    """
    counts: Counter[tuple] = Counter()
    members: dict[tuple, set] = {}
    for row in rows:
        part = "night" if _night(row["minute"]) else "day"
        track = _qualify(row)["cow_id"]
        for camera in (row["cameras"], HERD_CAMERA):
            counts[(row["day"], camera, part, row["behavior"])] += 1
            members.setdefault((row["day"], camera, part), set()).add(track)
    behaviors = sorted({key[3] for key in counts})
    body = []
    for key, count in sorted(counts.items()):
        n = len(members[key[:3]])
        body.append(_camera_row(key, count, n))
    for (day, camera, part), tracks in sorted(members.items()):
        if camera != HERD_CAMERA:
            continue
        for behavior in behaviors:
            if (day, camera, part, behavior) not in counts:
                body.append(_camera_row((day, camera, part, behavior), 0, len(tracks)))
    body.sort(key=lambda r: (r["camera"] == HERD_CAMERA, r["day"], r["camera"], r["part"], r["behavior"]))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CAMERA_FIELDS)
        writer.writeheader()
        writer.writerows(body)


def _camera_row(key: tuple, count: int, n_tracks: int) -> dict:
    return {
        "day": key[0], "camera": key[1], "part": key[2], "behavior": key[3],
        "track_minutes": count, "n_tracks": n_tracks, "mean_minutes_per_track": round(count / n_tracks, 4),
    }


def _empty_checkpoints() -> list[str]:
    names: list[str] = []
    for path in sorted((BATCH / "checkpoints").glob("*.json")):
        if path.read_text(encoding="utf-8").strip() == "[]":
            names.append(path.stem)
    return names


def _summary(rows: list[dict], cards: list[dict], empty: list[str]) -> dict:
    singled = [card for card in cards if card["single_out"] == "yes"]
    frames = BATCH / "frames"
    dense = len(list(frames.glob("*-dense-*"))) if frames.exists() else 0
    return {
        "activity_rows": len(rows),
        "qualified_tracks": len(cards),
        "singled_out": len(singled),
        "refused": len(cards) - len(singled),
        "empty_clips": len(empty),
        "checkpoints": len(list((BATCH / "checkpoints").glob("*.json"))),
        "dense_windows": dense,
        "behaviors": dict(Counter(row["behavior"] for row in rows)),
        "evidence": dict(Counter(row["evidence"] for row in rows)),
    }


def _write_cards(tracklets: list[dict], stats: dict, summary: dict, path: Path) -> None:
    tested = sum(assessable(t) for t in tracklets)
    lines = [
        "# Anomaly tracklet evidence",
        "",
        "These are the most anomalous tracklets observed: for each camera, the three tracklets "
        "whose behavior deviates most from the herd mean for that camera and day (method in "
        "`docs/anomaly-report.md`). They are clip-level evidence only. A tracklet is one tracker "
        "number inside one clip; the same number in another clip is a different tracking event, "
        "not the same animal. They do not identify individual cows, they are not linked across "
        "clips or days, and no ordering of individual cows is claimed. A deviation is not a diagnosis, and "
        "some, all, or none of the cattle may have BRD.",
        "",
        f"Tracklets in the batch: {len(tracklets):,}. Compared with the herd: {tested:,} "
        f"(at least 4 tracked minutes and mean confidence 0.5 or higher). Individual cows "
        f"singled out: {summary['singled_out']}.",
        "",
    ]
    for number, camera in enumerate(("back_cam", "front_cam_1", "front_cam_2"), start=1):
        lines.extend(_card(number, camera, top_anomalies(tracklets, stats, 3, cameras=(camera,))))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _card(number: int, camera: str, tracklets: list[dict]) -> list[str]:
    lines = [f"## Card {number} — {camera}", ""]
    if not tracklets:
        return lines + ["No tracklet could be compared with the herd on this camera.", ""]
    for t in tracklets:
        name = Path(t["clip"]).name
        lines += [
            f"### {name}",
            "",
            f"- Clip: {clip_link(t['clip'], ROOT)}",
            f"- Camera, day, minute: {camera}, Day {t['day']}, {first_minute(t)} (first minute of the behavior)",
            f"- Track number: {t['track']} (clip-local, not a cow ID)",
            f"- Observed behavior: {t['behavior']} in {t['minutes']} of {t['n']} tracked minutes "
            f"({100 * t['share']:.0f}%)",
            f"- Versus herd: the {camera} Day {t['day']} herd mean is {100 * t['herd_mean']:.1f}% of "
            f"minutes ({t['expected_minutes']:.2f} min for a {t['n']}-minute tracklet); "
            f"deviation z = {t['z']:+.1f}",
            "",
        ]
    return lines


def _night(minute: int) -> bool:
    hour = minute // 60
    return hour >= 20 or hour < 6


if __name__ == "__main__":
    sys.exit(main())
