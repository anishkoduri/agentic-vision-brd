"""Coarse detection batch. Does not delete source video.

Load YOLO, track, write tables, release YOLO, then the VLM hook.
The two models are never resident together.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.assemble import save_id_frame, write_activity, write_budgets, write_risk, write_traces  # noqa: E402
from src.cameras import clip_info  # noqa: E402
from src.detect import COARSE_S, load_yolo, release_yolo, require_gpu, rows_for_clip, sample_frames, sample_window, track_frames  # noqa: E402
from src.vlm import review_ambiguous  # noqa: E402


def main() -> int:
    args = _args()
    gpu = require_gpu()
    print(f"gpu={gpu}", flush=True)
    clips = _clips(args)
    if not clips:
        print("no clips")
        return 2
    out = args.out
    rows: list[dict] = []
    model = load_yolo()
    try:
        for index, clip in enumerate(clips, start=1):
            marker = out / "checkpoints" / f"{clip.stem}.json"
            if marker.exists() and not args.force:
                rows.extend(json.loads(marker.read_text(encoding="utf-8")))
                print(f"skip {index}/{len(clips)} {clip.name}", flush=True)
                continue
            info = clip_info(clip)
            frames = sample_frames(clip, out / "frames" / clip.stem)
            tracks = track_frames(model, frames, "bytetrack.yaml")
            if _fragmented(tracks):
                model.predictor = None
                tracks = track_frames(model, frames, "botsort.yaml")
            clip_rows = rows_for_clip(info, frames, tracks)
            for weak in _uncertain_minutes(tracks):
                dense_frames = sample_window(clip, out / "frames" / f"{clip.stem}-dense-{int(weak)}", weak)
                dense_tracks = track_frames(model, dense_frames)
                clip_rows.extend(rows_for_clip(info, dense_frames, dense_tracks, step_s=1 / 3, origin_s=weak))
            if frames and info["minute"] % 30 == 0:
                save_id_frame(frames[0], out / "id-checks" / f"{info['camera']}-{info['stamp']:%Y%m%d-%H%M}.jpg")
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(json.dumps(clip_rows), encoding="utf-8")
            rows.extend(clip_rows)
            print(f"clip {index}/{len(clips)} {clip.name} rows={len(clip_rows)}", flush=True)
    finally:
        release_yolo(model)
        del model
    reviewed = review_ambiguous(rows, yolo_loaded=False)
    write_activity(reviewed, out / "activity.csv")
    write_budgets(reviewed, out / "time_budgets.csv")
    write_risk(reviewed, out / "brd_risk.csv")
    write_traces(reviewed, out / "traces")
    print(f"wrote {len(reviewed)} rows under {out}")
    return 0


def _clips(args: argparse.Namespace) -> list[Path]:
    if args.clip:
        return [Path(args.clip).resolve()]
    root = args.root.resolve()
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() == ".avi")


def _uncertain_minutes(tracks: list[list[dict]]) -> list[float]:
    """At most one 4s window, and only inside a minute with a box under 0.45."""
    for index, frame in enumerate(tracks):
        if any(box["conf"] < 0.45 for box in frame):
            return [index * COARSE_S]
    return []


def _fragmented(tracks: list[list[dict]]) -> bool:
    ids = {box["id"] for frame in tracks for box in frame}
    peak = max((len(frame) for frame in tracks), default=0)
    return peak > 0 and len(ids) > peak * 2


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pen 6 coarse batch")
    parser.add_argument("--root", type=Path, default=ROOT / "data" / "readable")
    parser.add_argument("--out", type=Path, default=ROOT / "outputs" / "batch")
    parser.add_argument("--clip", type=Path, default=None, help="One clip. Does not scan the tree.")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
