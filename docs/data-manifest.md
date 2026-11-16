# Data manifest

What went into the batch. Counts were taken from the checkpoint files (`outputs/batch/checkpoints/`), `data/readable/`, and `outputs/batch/empty_clips.txt` on Sun Nov 15, 2026. They match the figures the team was given for the Drive folders. Older figures in `docs/data-inventory.md` describe the first 1,142 clips only and are superseded by this table.

## Clips

Total: **1,749** `.avi` clips, each about 5 minutes, 30 fps. Day 1 is 2026-11-07, Day 2 is 2026-11-08.

| Camera-day | Clips | Empty (no cow box) |
| --- | --- | --- |
| D1 Cam 01 | 289 | 112 |
| D1 Cam 02 | 292 | 135 |
| D1 Cam 03 | 287 | 0 |
| D2 Cam 01 | 293 | 131 |
| D2 Cam 02 | 293 | 184 |
| D2 Cam 03 | 295 | 42 |
| **Total** | **1,749** | **604** |

`data/readable/` holds 1,749 unique event names, and so do the checkpoints. All 1,749 clips were processed; nothing was dropped.

## Empty checkpoints

604 clips were processed and produced no cow detection. Their names are in `outputs/batch/empty_clips.txt`, one per line. They contribute no rows to `activity.csv`: a gap means "no detection", not "standing" and not "absent".

## Codec and OpenCV

- Codec: HEVC (Main). The AVI stream tag is `GHEC`, which OpenCV does not open.
- Fix: a stream copy (no re-encode) retagged `hvc1`, written to `data/readable/`. The original files in `data/raw/` were kept (1,749 present).
- `scripts/confirm_avi.py data/readable 1749`: **`opencv_ok=1749`, `failed=0`**, codec `hevc`, gate passed. Re-run on Nov 15, 2026; output in `outputs/confirm_avi_rerun.txt`, per-file records are in `outputs/ingest/probe-readable.jsonl` (not shipped in the zip, because it names local paths).
- Resolution where probed: Cam 01 and Cam 03 4000×3000, Cam 02 2592×1944. The batch decodes to 640×480.

## Camera mapping

| Camera | Filename tail | Role |
| --- | --- | --- |
| Cam 03 | `003` | Back |
| Cam 01 | `006` | Front 1 |
| Cam 02 | `017` | Front 2 |

Tracker ids are clip-local. No id is carried across clips or days.
