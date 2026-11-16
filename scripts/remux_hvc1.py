"""Copy-remux unpacked GHEC AVI clips to hvc1 AVI files under data/readable.

Originals under data/raw are not deleted or rewritten. A zip that is still
extracting is skipped until the unzip ledger marks it finished.
"""

from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.remux import remux_file  # noqa: E402

RAW = ROOT / "data" / "raw"
DEST = ROOT / "data" / "readable"
LEDGER = ROOT / "outputs" / "ingest" / "unzip-ledger.json"
LOG = ROOT / "outputs" / "ingest" / "remux-log.txt"
DOWNLOADS = Path.home() / "Downloads"
WORKERS = 2


def log(line: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    text = f"{stamp} {line}"
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(text + "\n")
    print(text, flush=True)


def finished_dirs() -> list[Path]:
    if not LEDGER.exists():
        return []
    try:
        payload = json.loads(LEDGER.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [Path(item["dest"]) for item in payload.get("extracted", []) if item.get("dest")]


def problem_zip_count() -> int:
    return sum(
        1
        for path in DOWNLOADS.glob("*.zip")
        if "problem 2" in path.name.lower() and "agentic" in path.name.lower()
    )


def sources() -> list[Path]:
    found: list[Path] = []
    for folder in finished_dirs():
        if not folder.is_dir():
            continue
        found.extend(
            path for path in folder.rglob("*") if path.is_file() and path.suffix.lower() == ".avi"
        )
    return sorted(found)


def dest_for(source: Path) -> Path:
    return DEST / source.relative_to(RAW)


def pending(videos: list[Path]) -> list[Path]:
    waiting: list[Path] = []
    for source in videos:
        dest = dest_for(source)
        if not (dest.is_file() and dest.stat().st_size > 0):
            waiting.append(source)
    return waiting


def _one(source: Path) -> tuple[str, str]:
    dest = dest_for(source)
    remux_file(source, dest)
    return source.name, str(dest)


def remux_batch(videos: list[Path]) -> tuple[int, list[Path]]:
    ok = 0
    failed: list[Path] = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(_one, source): source for source in videos}
        for future in as_completed(futures):
            source = futures[future]
            try:
                name, _dest = future.result()
            except (OSError, RuntimeError) as exc:
                failed.append(source)
                log(f"FAIL {source.name} {exc}")
                continue
            ok += 1
            done = ok + len(failed)
            if done == len(videos) or done % 25 == 0:
                log(f"progress {done}/{len(videos)} last={name}")
    return ok, failed


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    expected_zips = problem_zip_count()
    log(f"remux start dest={DEST} workers={WORKERS} zips_in_downloads={expected_zips}")
    idle_rounds = 0
    total_ok = 0
    failed_paths: set[Path] = set()
    while True:
        videos = sources()
        waiting = [source for source in pending(videos) if source not in failed_paths]
        extracted = len(finished_dirs())
        if waiting:
            idle_rounds = 0
            log(f"batch extracted_zips={extracted}/{expected_zips} avis={len(videos)} pending={len(waiting)}")
            ok, failed = remux_batch(waiting)
            total_ok += ok
            failed_paths.update(failed)
            continue
        if expected_zips and extracted >= expected_zips:
            log(f"remux complete avis={len(videos)} new_ok={total_ok} new_fail={len(failed_paths)}")
            print(f"remuxed_tree={len(videos)} new_ok={total_ok} new_fail={len(failed_paths)}")
            return 0 if not failed_paths else 1
        idle_rounds += 1
        log(f"waiting extracted_zips={extracted}/{expected_zips} avis={len(videos)}")
        if idle_rounds >= 24:
            log(f"stalled extracted_zips={extracted}/{expected_zips} avis={len(videos)}")
            print(f"remux stalled avis={len(videos)} new_ok={total_ok} new_fail={len(failed_paths)}")
            return 4
        time.sleep(15)


if __name__ == "__main__":
    sys.exit(main())
