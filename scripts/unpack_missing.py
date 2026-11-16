"""Unpack the 26 missing-clip zips. Never deletes or overwrites an existing file."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

DOWNLOADS = Path.home() / "Downloads"
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PREFIX = "Challenge 2 - Missing clips-20261115T045555Z-1-"


def missing_zips() -> list[Path]:
    found = sorted(DOWNLOADS.glob(PREFIX + "*.zip"), key=lambda path: int(path.stem.rsplit("-", 1)[-1]))
    return found


def main() -> int:
    zips = missing_zips()
    print(f"zips={len(zips)}", flush=True)
    if len(zips) != 26:
        print(f"expected 26 missing-clip zips, found {len(zips)}")
        return 2
    listed = 0
    extracted = 0
    skipped = 0
    failures: list[str] = []
    for archive_path in zips:
        dest = RAW / archive_path.stem
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive_path) as archive:
            members = [info for info in archive.infolist() if not info.is_dir() and info.filename.lower().endswith(".avi")]
            listed += len(members)
            print(f"start {archive_path.name} avis={len(members)}", flush=True)
            for info in members:
                target = dest / info.filename
                if target.exists() and target.stat().st_size > 0:
                    skipped += 1
                    continue
                try:
                    archive.extract(info, dest)
                except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
                    failures.append(f"{archive_path.name} {info.filename} {exc}")
                    continue
                if not target.exists() or target.stat().st_size == 0:
                    failures.append(f"{archive_path.name} {info.filename} empty after extract")
                    continue
                extracted += 1
        print(f"done {archive_path.name} extracted_so_far={extracted}", flush=True)
    print(f"listed={listed} extracted={extracted} skipped_existing={skipped} failed={len(failures)}")
    for line in failures:
        print(f"FAIL {line}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
