"""Probe every .avi under data/raw. Exit non-zero unless OpenCV can read them.

This is the gate in front of the detection batch. It does not start that batch.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.probe import probe_tree, require_readable  # noqa: E402


def main() -> int:
    raw = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (ROOT / "data" / "raw").resolve()
    expect = int(sys.argv[2]) if len(sys.argv) > 2 else None
    records = probe_tree(raw)
    default_raw = (ROOT / "data" / "raw").resolve()
    out_name = "probe.jsonl" if raw == default_raw else "probe-readable.jsonl"
    out = ROOT / "outputs" / "ingest" / out_name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    passed = sum(1 for record in records if record.get("opencv_ok"))
    failed = len(records) - passed
    if not records:
        print(f"no .avi under {raw}; batch not started")
        return 2
    print(f"probed {len(records)} avi file(s); opencv_ok={passed}; failed={failed}")
    if expect is not None and len(records) != expect:
        print(f"expected {expect} file(s); found {len(records)}")
        return 3
    try:
        require_readable(records)
    except RuntimeError as exc:
        print(exc)
        return 3
    codecs = sorted({record["codec_name"] for record in records})
    print(f"gate passed; codecs={codecs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
