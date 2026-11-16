"""Watch Chrome Downloads for finished Problem 2 zips and extract them.

Does not start a download. Ignores .crdownload files and the 11 MB BRD-papers zip.
"""

from __future__ import annotations

import json
import sys
import time
import zipfile
from pathlib import Path

DOWNLOADS = Path.home() / "Downloads"
ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "raw"
LEDGER_PATH = ROOT / "outputs" / "ingest" / "unzip-ledger.json"
LOG_PATH = ROOT / "outputs" / "ingest" / "watch-log.txt"
PAPERS = "drive-download-20261114T210441Z-1-001.zip"
STABLE_SECONDS = 15
POLL_SECONDS = 30


def log(line: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp} {line}\n")
    print(f"{stamp} {line}", flush=True)


def load_ledger() -> dict:
    if not LEDGER_PATH.exists():
        return {"extracted": []}
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def save_ledger(ledger: dict) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2), encoding="utf-8")


def is_problem_zip(path: Path) -> bool:
    if path.suffix.lower() != ".zip":
        return False
    if path.name == PAPERS:
        return False
    name = path.name.lower()
    if "crdownload" in name:
        return False
    return "problem 2" in name and "agentic" in name


def crdownload_stats() -> str:
    parts = list(DOWNLOADS.glob("*.crdownload"))
    total = sum(p.stat().st_size for p in parts)
    return f"crdownload count={len(parts)} bytes={total}"


def stable(path: Path) -> bool:
    if not path.exists():
        return False
    size = path.stat().st_size
    if size <= 0:
        return False
    time.sleep(STABLE_SECONDS)
    if not path.exists():
        return False
    return path.stat().st_size == size


def extract(path: Path, ledger: dict) -> None:
    target = DEST / path.stem
    target.mkdir(parents=True, exist_ok=True)
    log(f"extract start {path.name} -> {target}")
    with zipfile.ZipFile(path) as archive:
        archive.extractall(target)
    names = [p for p in target.rglob("*") if p.is_file()]
    ledger["extracted"].append(
        {
            "zip": path.name,
            "bytes": path.stat().st_size,
            "dest": str(target),
            "files": len(names),
            "finished": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    save_ledger(ledger)
    log(f"extract done {path.name} files={len(names)}")
    _probe_new_avi(target)


def _probe_new_avi(target: Path) -> None:
    """ffprobe + OpenCV on each unpacked .avi. A failure is logged, not fatal to the unzip."""
    sys.path.insert(0, str(ROOT))
    from src.probe import probe_video

    manifest = ROOT / "outputs" / "ingest" / "probe.jsonl"
    avis = [path for path in target.rglob("*") if path.suffix.lower() == ".avi"]
    if not avis:
        log(f"no avi in {target.name}")
        return
    with manifest.open("a", encoding="utf-8") as handle:
        for video in avis:
            try:
                record = probe_video(video)
            except (OSError, RuntimeError, json.JSONDecodeError) as exc:
                log(f"probe failed {video.name}: {exc}")
                continue
            handle.write(json.dumps(record) + "\n")
            state = "opencv_ok" if record["opencv_ok"] else "opencv_FAIL"
            log(f"probe {video.name} codec={record['codec_name']} {record['width']}x{record['height']} {state}")


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    log(f"watcher start dest={DEST}")
    log(crdownload_stats())
    while True:
        ledger = load_ledger()
        done = {row["zip"] for row in ledger["extracted"]}
        log(crdownload_stats())
        for path in sorted(DOWNLOADS.glob("*.zip")):
            if not is_problem_zip(path) or path.name in done:
                continue
            log(f"candidate {path.name} bytes={path.stat().st_size}")
            if not stable(path):
                log(f"skip unstable {path.name}")
                continue
            try:
                extract(path, ledger)
                done.add(path.name)
            except zipfile.BadZipFile:
                log(f"bad zip, left in Downloads: {path.name}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
