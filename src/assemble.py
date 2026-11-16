"""Write the batch tables from minute rows. Does not read video."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.risk import rank_minutes

ACTIVITY_FIELDS = (
    "cow_id",
    "day",
    "minute",
    "behavior",
    "cameras",
    "confidence",
    "visible",
    "evidence",
    "alone",
    "clip",
)


def dedupe_second_look(rows: list[dict]) -> list[dict]:
    """One row per (clip, track, minute). A later row for a key is the 3 fps second look and replaces
    the coarse row in the coarse row's position; keys seen once keep their only row."""
    kept: dict[tuple, dict] = {}
    for row in rows:
        kept[(row["clip"], row["cow_id"], row["minute"])] = row
    return list(kept.values())


def write_activity(rows: list[dict], path: Path) -> None:
    _write_csv(path, ACTIVITY_FIELDS, dedupe_second_look(rows))


HERD_ID = "HERD_AVERAGE"
BUDGET_FIELDS = ("cow_id", "day", "part", "behavior", "minutes", "n_tracks")


def write_budgets(rows: list[dict], path: Path) -> None:
    """Per-track day/night minutes, plus one HERD_AVERAGE row per (day, part, behavior).

    `cow_id` is a clip-local track label, not a stable animal. The herd average is the mean
    minutes per track over the tracks that have at least one row in that day and part
    (`n_tracks` of them), counting 0 for a track that never showed the behavior.
    """
    counts: dict[tuple, int] = {}
    for row in rows:
        key = (row["cow_id"], row["day"], _part(int(row["minute"])), row["behavior"])
        counts[key] = counts.get(key, 0) + 1
    body = [
        {"cow_id": key[0], "day": key[1], "part": key[2], "behavior": key[3], "minutes": count, "n_tracks": 1}
        for key, count in sorted(counts.items())
    ]
    _write_csv(path, BUDGET_FIELDS, body + herd_average_rows(counts))


def herd_average_rows(counts: dict[tuple, int]) -> list[dict]:
    behaviors = sorted({key[3] for key in counts})
    tracks: dict[tuple, set] = {}
    totals: dict[tuple, int] = {}
    for (cow, day, part, behavior), minutes in counts.items():
        tracks.setdefault((day, part), set()).add(cow)
        totals[(day, part, behavior)] = totals.get((day, part, behavior), 0) + minutes
    return [
        {
            "cow_id": HERD_ID, "day": day, "part": part, "behavior": behavior,
            "minutes": round(totals.get((day, part, behavior), 0) / len(members), 4), "n_tracks": len(members),
        }
        for (day, part), members in sorted(tracks.items())
        for behavior in behaviors
    ]


def _part(minute: int) -> str:
    return "night" if _night(minute) else "day"


def write_risk(rows: list[dict], path: Path) -> None:
    cards = rank_minutes(rows)
    fields = (
        "cow_id",
        "rank",
        "risk_visible",
        "risk_all",
        "visible_fraction",
        "single_out",
        "single_out_reason",
        "stability",
    )
    _write_csv(path, fields, cards)


def write_traces(rows: list[dict], dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    visible = [row for row in rows if row.get("visible")]
    success = max(visible, key=lambda row: float(row["confidence"]), default=None)
    failure = min(rows, key=lambda row: float(row["confidence"]), default=None)
    night = next((row for row in rows if _night(int(row["minute"]))), None)
    _trace(dest / "success.json", "success", success, "Highest-confidence visible minute in this run.")
    _trace(dest / "failure.json", "failure", failure, "Lowest-confidence minute. The tracker label stands.")
    if night is None:
        (dest / "night.json").write_text(
            json.dumps({"kind": "night", "observed": False, "note": "This run had no night minute. Nothing was invented."}, indent=2),
            encoding="utf-8",
        )
        return
    _trace(dest / "night.json", "night", night, "A minute between 20:00 and 06:00.")


def save_id_frame(frame: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(frame.read_bytes())


def _night(minute: int) -> bool:
    hour = minute // 60
    return hour >= 20 or hour < 6


def _trace(path: Path, kind: str, row: dict | None, note: str) -> None:
    body = {"kind": kind, "note": note, "row": row, "vlm": "not called; tracker label kept"}
    path.write_text(json.dumps(body, indent=2), encoding="utf-8")


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
