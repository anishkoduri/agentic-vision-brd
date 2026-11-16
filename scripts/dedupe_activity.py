"""Dedupe outputs/batch/activity.csv to one row per (clip, track, minute), keeping the second look.

The pre-dedup file is kept once at outputs/batch/audit/activity.pre-dedup.csv. Does not read video.
"""

from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.assemble import ACTIVITY_FIELDS, dedupe_second_look  # noqa: E402

ACTIVITY = ROOT / "outputs" / "batch" / "activity.csv"
BACKUP = ROOT / "outputs" / "batch" / "audit" / "activity.pre-dedup.csv"


def main() -> int:
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        shutil.copyfile(ACTIVITY, BACKUP)
    with BACKUP.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    kept = dedupe_second_look(rows)
    with ACTIVITY.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ACTIVITY_FIELDS)
        writer.writeheader()
        writer.writerows(kept)
    print(f"rows {len(rows)} -> {len(kept)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
