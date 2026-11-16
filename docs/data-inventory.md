# Data inventory

Counted from the 51 finished zip parts in Downloads on Sat Nov 14, 2026, about 9:45 PM CST. Codec tag read from the AVI `strh` header of every video. OpenCV was tried on the files already unpacked.

## What arrived

- 51 zip parts named `Problem 2_ BRD Agentic Vision-20261115T020840Z-1-NNN.zip`.
- Zip bytes: 108,959,739,877 (101.48 GB).
- Inside: 1,142 `.avi` files, 101.47 GB, plus `pen map.png`, the challenge PDF, and the challenge docx.
- Part numbers run from 001 to 059. These eight numbers are not in Downloads: 046, 048, 052, 054, 055, 056, 057, 058. Chrome’s partial count was 51 for the whole download, so those eight never started.

## Size against the brief

The brief said about 50 GB. The finished download is 101.48 GB. At 9:01 PM the same 51 partials totaled 71.4 GB and were still growing, so 71 GB was a midpoint, not a second copy. The videos are already HEVC, so the zip parts are almost the same size as the files inside them (101.48 GB zipped, 101.47 GB uncompressed).

## Cameras and files

The folders are the camera labels. They are not yet tied to Back cam, Front cam 1, or Front cam 2 on the pen map. The filename tail matches the folder.

| Folder | File tail | Clips | Size | First stamp | Last stamp | Resolution where probed |
|---|---|---|---|---|---|---|
| Day 1 / Cam 01 | 006 | 4 | 0.26 GB | 2026-11-07 03:39:30 | 2026-11-07 23:55:50 | on disk, all four in part 059 |
| Day 1 / Cam 02 | 017 | 250 | 18.18 GB | 2026-11-07 03:29:42 | 2026-11-07 23:56:01 | 2592×1944 |
| Day 1 / Cam 03 | 003 | 122 | 16.01 GB | 2026-11-07 05:14:26 | 2026-11-07 23:55:39 | 4000×3000 |
| Day 2 / Cam 01 | 006 | 250 | 21.04 GB | 2026-11-08 03:36:04 | 2026-11-08 23:56:10 | 4000×3000 |
| Day 2 / Cam 02 | 017 | 255 | 15.64 GB | 2026-11-08 02:36:12 | 2026-11-08 23:56:28 | 2592×1944 |
| Day 2 / Cam 03 | 003 | 261 | 30.35 GB | 2026-11-08 00:10:40 | 2026-11-08 23:56:11 | 4000×3000 |

Day 1 is 2026-11-07. Day 2 is 2026-11-08. Day 1 Cam 01 has four clips and all four are in part 059. Day 2 of that same camera has 250 clips.

## Drive totals, recounted 10:17 PM CST

`data/raw` and `data/readable` match the 51 zip central directories: 1,142 clips, same six camera-day counts. Nothing was lost in the unzip. Drive figures below are the ones supplied for this check. Day 2’s “about 292” is compared with 292. No Drive total was given for Day 1 Cam 02.

| Folder | On disk | Drive | Short |
|---|---|---|---|
| Day 1 / Cam 01 | 4 | 289 | 285 |
| Day 1 / Cam 02 | 250 | not given | — |
| Day 1 / Cam 03 | 122 | 287 | 165 |
| Day 2 / Cam 01 | 250 | 292 | 42 |
| Day 2 / Cam 02 | 255 | 292 | 37 |
| Day 2 / Cam 03 | 261 | 292 | 31 |

Named shortfall: 560 clips. The eight missing parts (046, 048, 052, 054, 055, 056, 057, 058) are about 2.14 GB each, 17.1 GB together, and they sit in the part-number band whose neighbors hold 13–19 Day 1 Cam 03 clips. That is on the order of 110 clips and 17 GB. Day 1 Cam 01’s 285-clip hole is already larger than that, at the size of the four clips that did arrive. The eight parts do not account for the gap.

## Codec and the batch gate

Every one of the 1,142 files is AVI, fourcc `GHEC` (`0x43454847`), 30 fps. ffprobe without a hint reports `codec_name=unknown`. Forcing the HEVC decoder identifies `hevc (Main)`, `yuvj420p`, and it decoded a frame. OpenCV’s `VideoCapture` does not open the raw files (`codec_id=0`). After a copy remux with tag `hvc1`, OpenCV read a 4000×3000 frame from one Day 2 Cam 01 clip.

The raw files still fail OpenCV. A stream copy retagged `hvc1` is in `data/readable/`. Originals in `data/raw/` were kept.

On 2026-11-15 the 26 `Challenge 2 - Missing clips` parts (001–026) added 607 clips. None failed to unpack. Unique event names on disk: 1,749. `confirm_avi.py data/readable 1749` reported `opencv_ok=1749`, `failed=0`, codec `hevc`, exit 0. The batch reads `data/readable/` only.
