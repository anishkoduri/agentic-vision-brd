# Agentic Vision for Angus Behavior and BRD Early Warning

| | |
| --- | --- |
| **Competition** | AISFS × Merck Animal Health Hackathon 2026 |
| **Challenge** | Challenge 2 — Agentic Vision, BRD early warning from video |
| **Team** | Anish Koduri, Aaron Jacob, Amulya Bisaria |

> Two days of pen video (Pen 6, ten Angus, three cameras), read on one laptop. Minute labels where a cow was in frame. No health claim for any individual animal, because the same cow cannot yet be followed from clip to clip.

The batch has been run on all 1,749 clips. The ranker has been run on that output. It singled out nobody.

## Start here

| Deliverable | Where |
| --- | --- |
| Two-page technical brief | [`docs/technical-brief.md`](docs/technical-brief.md) |
| Anomaly report: herd day-over-day table, most anomalous tracklets, behavior by hour | [`docs/anomaly-report.md`](docs/anomaly-report.md) |
| Static visualization (open in a browser; no server, no network) | [`docs/visualization.html`](docs/visualization.html) |
| Explanations backed by clips (one card per anomalous tracklet) | [`docs/risk-cards.md`](docs/risk-cards.md) |
| Demo video, narrated (54 s) | [`challenge2-video/out/demo-voiced.mp4`](challenge2-video/out/demo-voiced.mp4) |
| Demo video, captions only | [`challenge2-video/out/demo.mp4`](challenge2-video/out/demo.mp4) |
| Data manifest | [`docs/data-manifest.md`](docs/data-manifest.md) |
| Result tables: [`activity.csv`](outputs/batch/activity.csv), [`brd_risk.csv`](outputs/batch/brd_risk.csv), [`time_budgets.csv`](outputs/batch/time_budgets.csv), [`time_budgets_by_camera.csv`](outputs/batch/time_budgets_by_camera.csv), [`empty_clips.txt`](outputs/batch/empty_clips.txt), reasoning traces ([`success`](outputs/batch/traces/success.md), [`failure`](outputs/batch/traces/failure.md), [`night`](outputs/batch/traces/night.md)), ID-check [`index.csv`](outputs/batch/id-checks/index.csv) | `outputs/batch/` |
| Full submission package, including the 283 ID-check stills (about 193 MB; the stills are only in the ZIP) | [`Challenge2-submission.zip`](https://github.com/anishkoduri/agentic-vision-brd/releases/download/v1.0.0/Challenge2-submission.zip) ([release v1.0.0](https://github.com/anishkoduri/agentic-vision-brd/releases/tag/v1.0.0)) |

## Verify the results

Run from the repo root in PowerShell, after the venv and install steps under "Run locally".

1. **Unit tests** (expect 33 pass, 1 skip):

   ```powershell
   .\.venv\Scripts\python.exe -m unittest tests.test_risk tests.test_behavior tests.test_probe tests.test_remux tests.test_evidence tests.test_hourly tests.test_traces tests.test_dedupe
   ```

2. **Row count** (expect 24,327, one per clip, track, and minute):

   ```powershell
   .\.venv\Scripts\python.exe -c "import csv; print(sum(1 for _ in csv.DictReader(open('outputs/batch/activity.csv', encoding='utf-8'))))"
   ```

3. **Render the brief** (expect `words=982`, 11pt pages=2, 12pt pages=2; uses headless Edge):

   ```powershell
   .\.venv\Scripts\python.exe scripts\render_brief.py
   ```

4. **Open `docs/visualization.html`** in a browser to see the behavior distribution, time budgets by camera, herd day-over-day, and feeding-by-hour charts. The most anomalous tracklets are in a table in `docs/anomaly-report.md`, not in this page.

5. The full 1,749-clip run is about 17 hours on a single laptop (estimated from timing one clip at 34.8 s), so the repo ships the completed outputs (`activity.csv`, `brd_risk.csv`, the time budgets, the traces, and the ID-check index). The steps above verify those outputs rather than re-running the batch.

## Demo video

[![Demo preview: a few seconds of the narrated walkthrough. Click to open the full video.](docs/demo-preview.gif)](challenge2-video/out/demo-voiced.mp4)

[`challenge2-video/out/demo-voiced.mp4`](challenge2-video/out/demo-voiced.mp4) is a 54-second narrated walkthrough of `docs/visualization.html`: the herd day-over-day comparison, feeding share by hour (the Day 2 midday drop), and the most anomalous tracklets from `docs/anomaly-report.md`. The narration is an ElevenLabs voice (George) laid over the captions; there is no music.

The same video with captions only and no audio is [`challenge2-video/out/demo.mp4`](challenge2-video/out/demo.mp4). Both were filmed from the local files. The edit can be rebuilt with `npm run all` in `challenge2-video/`, and the voiceover re-laid with `python scripts/voiceover.py <voiceover.mp3>`.

Voiceover generated with ElevenLabs (elevenlabs.io).

## Headline result

On Day 2 the herd's feeding share fell sharply at midday: at 13 h it went from 26.6% on Day 1 to 0.7%, and lying rose over the same hours (13 h: 10.8% to 57.0%). Reduced feed intake with more lying is a pattern a veterinarian would investigate first. It is a herd-level signal with a coverage caveat (front-camera track-minutes at 13 h fell from 830 to 28) and not a diagnosis. Details are in the brief and `docs/anomaly-report.md`.

## How this maps to the rubric

| Rubric item | What this submission has | Honest limit |
| --- | --- | --- |
| **Behavior accuracy** | One behavior label per track per minute: 24,327 rows across 1,749 clips (standing 13,659; lying 8,193; feeding 1,382; walking 1,093). | Only 4 of the spec's 10 behavior classes are detected. Labels are a geometric rule on the box, not ground truth, and no labeled accuracy was measured, so none is stated. |
| **Cow identification** | Clip-local tracker labels (`Cam 03-t1`); every row says which clip it came from. | No identity survives across clips, so no cow IDs are claimed and 0 of 9,750 tracks appear on both days. |
| **Agent loop (tools, checks itself)** | Tools: FFmpeg and OpenCV, YOLO11-small, ByteTrack. A box under 0.45 confidence triggers a 3 fps re-look (1,113 clips). Three traces follow one re-examined minute through Observe, Question, Verify, Revise (success, failure, night). | The vision-language model (Qwen2.5-VL-3B) was not run, so the check is tracker confidence plus the re-look. |
| **Biologically sensible behavioral features** | Feeding, lying, standing, walking; day and night time budgets; share by hour of day. Feed intake is read first because reduced intake is an early sign of BRD. | Feeding is labeled only on the front cameras, so a pooled feeding share is diluted by back-camera tracks. |
| **Explanations backed by video clips** | `docs/risk-cards.md` names the source clip, camera, day, and minute for each anomalous tracklet, with a veterinary reading. `top_reasons` in `brd_risk.csv` holds each tracklet's observed features against the herd. ID-check stills: 283 of 288 slots. | The event clips are not redistributed, so the evidence points at clips by name. |
| **Early warning** | A design for an hourly feeding-share check against the same hour the day before, with an alert and the clip as evidence (see the brief). | It is a design, not a live system. Nothing alerting was built or tested. |
| **Clinical signs** | The risk cards describe restlessness (walking while the herd rests) in veterinary terms. | No clinical sign is detected. A moving box is not a cough or a nasal discharge. |
| **Ranch-ready design** | All compute ran on one laptop with no cloud, no cluster, and no paid API, so a producer could run it. | Static outputs only; there is no deployed dashboard. |

## Honest limits

- **No per-cow ranking.** `outputs/batch/brd_risk.csv` leaves `score` and `rank` blank on every row. A per-cow ranking needs the same animal followed across clips and days, and that was not solved.
- **Only 4 of 10 behavior classes** are detected: standing, lying, feeding, walking.
- **Early warning is a design, not a live system.**
- **No accuracy was measured.** Labels use assumed thresholds (the feeding band, the 0.45 cutoff, night by the clock).
- Some, all, or none of the ten cows may have BRD. This analysis does not say which.

## What it does

- Samples each clip sparsely, and spends extra frames only where a detection is under 0.45 confidence.
- Writes a behavior row per tracker per minute (`outputs/batch/activity.csv`).
- Refuses a pen ranking when an id does not exist on both days (`outputs/batch/brd_risk.csv`: score and rank are blank; `top_reasons` holds each tracklet's observed features against the herd).
- Saves a still every 30 minutes per camera, a day/night time budget, three reasoning traces, and anomaly tracklet evidence ([`docs/risk-cards.md`](docs/risk-cards.md)).

## How it works

1. `scripts/confirm_avi.py` checks that OpenCV can read the remuxed HEVC files in `data/readable/`.
2. `scripts/run_batch.py` decodes on the GPU to 640×480, one frame every 10 seconds, and runs YOLO11-small plus ByteTrack. One 4-second window at 3 fps is added only if a box is under 0.45. BoT-SORT is retried only if ids fragment inside the clip.
3. Geometry labels the box: wide box lying, movement walking, low in a front frame feeding, otherwise standing (`src/behavior.py`).
4. `scripts/dedupe_activity.py` reduces `activity.csv` to one row per track per minute (second look wins). `scripts/write_deliverables.py` then runs `src/risk.py` on clip-qualified ids and rewrites the risk file, budgets, traces, and `docs/risk-cards.md`.
5. `scripts/build_overview.py` writes `docs/anomaly-report.md` (including the by-hour table, `src/hourly.py`) and `docs/visualization.html` from `activity.csv` and `time_budgets.csv`.

Tracker ids are per clip. `Cam 03-t1` in the next clip is a new track, not the same animal, so nothing here follows a cow across clips or days.

## Results from this batch

| Item | Value |
| --- | --- |
| Clips checkpointed | 1,749 of 1,749 |
| Clips with no cow box | 604 (listed in `outputs/batch/empty_clips.txt`, not filled) |
| Activity rows | 24,327 track-minutes (one row per track per minute) |
| Behaviors | standing 13,659; lying 8,193; feeding 1,382; walking 1,093 |
| Tracks on both days | 0 of 9,750 |
| Cows singled out | 0 |
| Extra 3 fps windows | 1,113 clips |
| ID stills | 283 of 288 slots; 5 slots have no clip and are listed in `outputs/batch/id-checks/index.csv` as "no covering clip — frame not available" |

## About `activity.csv`

- **24,327 rows.** One row is one detected track in one minute, and `activity.csv` has exactly one row per track per minute after dedup (`cow_id` is the clip-local tracker label such as `Cam 03-t1`; columns are `cow_id, day, minute, behavior, cameras, confidence, visible, evidence, alone, clip`). `cameras` is the spec's "camera(s) visible in" (`back_cam`, `front_cam_1`, `front_cam_2`); `minute` is the minute of the day (0–1439); `evidence`, `alone` and `clip` are extra columns.
- **Dedup.** The raw batch held 28,153 rows because the 3 fps re-examination window appended a second read of 3,826 (clip, `cow_id`, `minute`) keys that already had a coarse-pass row. `scripts/dedupe_activity.py` keeps one row per (clip, track, minute): the second-look row where there is one (the coarse row is dropped), otherwise the only row. That left 24,327 rows. The second look changed the behavior label in 1,220 of the 3,826 keys. `write_activity` in `src/assemble.py` now applies the same rule, so a rerun of the batch writes the deduped file. The pre-dedup file is not in the zip. Feeding share moved from 6.0% / 5.1% (Day 1 / Day 2, before dedup) to 6.1% / 5.1%; the Day 2 midday drop is essentially unchanged (13 h: 26.6% to 0.7%).
- **Not 28,800.** The spec's 28,800-row figure is 10 cows × 1,440 minutes × 2 days and assumes 10 stable cow IDs. This submission does not claim stable IDs, so it does not claim that shape.
- **Four behavior classes observed:** standing, lying, feeding, walking. All four are spelled as in the spec's ten classes; the other six (drinking, both ruminating classes, grooming, social interaction, other / not visible) are never assigned, because a box shape cannot show them. `visible` is `True` on every row because empty clips write no rows.
- **Empty clips are excluded.** The 604 clips with no detections contribute no rows and are listed in `outputs/batch/empty_clips.txt`. A gap means "no detection", never "standing" or "absent".
- **Observed, not estimated.** Every row has `evidence = observed`; nothing was imputed or filled in. The behavior label itself is a geometric rule on the box with assumed thresholds (feeding band, 0.45 cutoff, night by the clock), not ground truth, and no accuracy was measured.

## Time budgets (per track, not per cow)

- `outputs/batch/time_budgets.csv`: minutes per clip-qualified track (`Event…|Cam 03-t1`), by day and by `part` (`day` / `night`; night is 20:00–06:00 by the clock). A budget belongs to a track inside one clip. It is not a cow's day, because no animal is followed across clips.
- `HERD_AVERAGE` rows: mean minutes per track for each day, part and behavior, over the `n_tracks` tracks that have a row in that day and part (a track that never showed the behavior counts as 0).
- `outputs/batch/time_budgets_by_camera.csv`: track-minutes by day, camera and part, with `n_tracks` and `mean_minutes_per_track`. The `all_cameras (HERD_AVERAGE)` rows pool the three cameras and match the herd rows above. Feeding can only be read on the front cameras, so a pooled feeding average is diluted by back-camera tracks.

## Reasoning traces

`outputs/batch/traces/{success,failure,night}.md` (and `.json`) each follow one real re-examined minute through Observe, Question, Verify, Revise. The VLM (Qwen2.5-VL-3B) was not invoked, because its weights were not available on the machine; the verification is the tracker's box confidence plus the 3 fps re-examination window.

## Data manifest

[`docs/data-manifest.md`](docs/data-manifest.md) lists the clip counts per camera-day, the codec and remux, the OpenCV check, and the camera mapping.

## Camera mapping

| Camera | Filename tail | Role |
| --- | --- | --- |
| Cam 03 | `003` | Back |
| Cam 01 | `006` | Front 1 |
| Cam 02 | `017` | Front 2 |

## Run locally

The submission zip has no event video clips and no virtualenv. It does include the demo video project `challenge2-video/` (source, plus `out/demo.mp4` and `out/demo-voiced.mp4`; no `node_modules`, frames, or QA screenshots; run `npm install` there before rebuilding). Create one, then run from this directory (PowerShell, Python 3.14, NVIDIA GPU with CUDA 12.8 drivers). Install PyTorch first: `requirements.txt` pins `torch==2.11.0+cu128`, a build that exists only on the PyTorch index, so installing the requirements first fails.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch==2.11.0+cu128 torchvision==0.26.0+cu128 --index-url https://download.pytorch.org/whl/cu128
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest tests.test_risk tests.test_behavior tests.test_probe tests.test_remux tests.test_evidence tests.test_hourly tests.test_traces tests.test_dedupe
```

`confirm_avi.py`, `run_batch.py`, and `fill_id_checks.py` need the event clips remuxed into `data/readable/` first (a stream copy retagged `hvc1`, see `src/remux.py` and `scripts/remux_hvc1.py`). That folder is not in the zip. Without it, `confirm_avi.py` exits with "no .avi". The shipped `outputs/batch/` tables are the finished run, so those commands are a rerun, not a requirement to read the results. `write_deliverables.py` and `build_overview.py` need no video, but `write_deliverables.py` also reads `outputs/batch/checkpoints/` and `frames/`, which are not in the zip (the checkpoints name local clip paths); without them it would rewrite `empty_clips.txt` as empty, so rerun it only after a full batch. The `clip` column of `activity.csv` is the clip filename only.

```powershell
.\.venv\Scripts\python.exe scripts\confirm_avi.py data\readable 1749
.\.venv\Scripts\python.exe scripts\run_batch.py --root data\readable --out outputs\batch
.\.venv\Scripts\python.exe scripts\write_deliverables.py
.\.venv\Scripts\python.exe scripts\build_overview.py
.\.venv\Scripts\python.exe scripts\fill_id_checks.py
```

Notes:

- `confirm_avi.py <folder> <expected count>` exits non-zero if OpenCV cannot read every file or the count differs.
- `run_batch.py` refuses to start unless CUDA sees an RTX 4060. It skips a clip that already has a checkpoint (`--force` redoes it). The full batch writes `activity.csv` only at the end, and it also rewrites `brd_risk.csv` and `time_budgets.csv` with a naive version, so always run `write_deliverables.py` after it. `--clip <file>` processes one clip but still writes `activity.csv` under `--out`; give it a scratch `--out` (for example `--out outputs\smoke`), never `outputs\batch`. Do not point `--root` at `data/raw/`; those files are still the original GHEC AVIs.
- `write_deliverables.py` prints a summary line; expect `"singled_out": 0`.
- `fill_id_checks.py` exits 1 on this data because 5 of the 288 slots have no clip. That is the expected result, not a failure.

## External resources and AI tools

| Resource | Use and source |
| --- | --- |
| Event dataset | Merck–TAMU Agentic Vision dataset: Pen 6, 2 days × 3 cameras (1,749 clips). Obtained through the event Google Drive. It stays within the event and is not shared or published; no video is in this package or in git. |
| YOLO11-small pretrained weights | `yolo11s.pt` from Ultralytics (COCO class 19 = cow), used through Ultralytics 8.4.213. |
| PyTorch | 2.11.0+cu128, with torchvision 0.26.0+cu128, from the PyTorch cu128 wheel index. |
| ByteTrack / BoT-SORT | The implementations bundled in Ultralytics 8.4.213 (`bytetrack.yaml`, fallback `botsort.yaml`); no separate package or version. `lap` 0.5.14 is installed in this environment. |
| OpenCV 5.0.0.93, static-ffmpeg 3.0 | `requirements.txt`. FFmpeg is not required on PATH. |
| Qwen2.5-VL-3B | Not downloaded and not used. Uncertain minutes keep the tracker label. |
| Pen map | `docs/pen-map.png`, from the challenge packet. |

Video tooling (for `challenge2-video/` only; none of it is part of the analysis): Remotion 4.0.526 and Playwright 1.63.0 (Node) record and render the walkthrough from the local files. `faster-whisper` (a local speech-to-text model, base.en) was used once to check that the voiceover lines up with the captions; it is not in `requirements.txt` and its output is not in the package.

### AI use and human direction

This was a human-directed, AI-assisted build. Most of the code, analysis, and prose in this folder was written by AI coding assistants working from the human's instructions; the human did not hand-write it. The AI tools were:

- **Grok** (through Cursor): the technical writeup, and the pipeline and README drafts.
- **Claude** (Anthropic, through the Cursor coding agent; the session model is Claude Sonnet 5.5): the final documentation, the anomaly analysis (`docs/anomaly-report.md`, `docs/visualization.html`), the `brd_risk.csv` reasons, the risk cards, the deduplication fix, the video project in `challenge2-video/`, and the submission packaging.
- **ElevenLabs** (voice "George"): the narration audio. The human generated it from the narration script outside this folder and supplied the MP3; no audio was synthesized by the agent. The voiceover is credited to elevenlabs.io.

What the human did:

- Set the scope and the constraints that shape every result: local-only compute on one laptop, no cloud or paid APIs, no invented cow IDs, no per-cow ranking or risk score, no accuracy figures, and track numbers treated as clip-local.
- Obtained the dataset: ran the Google Drive download, supplied the clip parts that were missing from it, and decided which gaps to chase.
- Directed the fixes that changed the results: collapsing the duplicated second-look rows in `activity.csv` to one row per track per minute, removing local file paths from the package, and choosing what the brief says about Levels 2 and 3.
- Specified what to verify before packaging (row counts, archive tests, 2-page render at 11pt and 12pt, no local paths) and approved or redirected the work at each step.
- Chose the three charts and their order for the demo video, supplied its narration script, and supplied the voiceover recording.

All compute ran on one personal laptop (NVIDIA RTX 4060 Laptop GPU, 8 GB VRAM), with no cloud, cluster, or paid API, so the process can be repeated by anyone with the dataset and a CUDA GPU. Note that `run_batch.py` has a guard that refuses to start unless it sees an RTX 4060; edit that check to run on another GPU.

Checks run on the video files and the outputs (each was a real run, not an assumption):

- **Video ingest:** every `.avi` was probed with `ffprobe` and read with OpenCV (`confirm_avi.py`). The clips were HEVC in an AVI container that OpenCV could not open, so all of them were stream-copied to `hvc1` and re-verified with OpenCV before the originals were touched. The batch ran on the 1,749 remuxed clips.
- **Inventory:** clip counts per camera and day were compared against the Drive totals, and the missing parts were identified and unpacked.
- **Before the full batch:** a one-clip smoke test and a one-clip timing run, with the output files checked.
- **After the batch:** the activity, budget, and ID-check tables were verified against each other; the duplicate minute rows were found and removed; the package was scanned for local paths.
- **Packaging:** the brief was rendered in headless Edge at 11pt and 12pt to confirm it fits 2 pages, and the ZIP was extracted and checked after each rebuild.

No AI model ran inside the pipeline. The cow boxes come from local YOLO11-small, not from a hosted model, and no paid vision API was called. AI-written text and code were checked against the files and scripts in this folder, by running the tests and by checking the generated tables and rendered pages. No labeled accuracy was measured.

## Layout

```
src/            behavior, cameras, detect, risk, assemble, evidence, hourly
scripts/        confirm, batch, deliverables, overview, id stills
tests/          rank math, geometry, tracklet evidence, and by-hour shares on synthetic rows
data/readable/  hvc1 copies the batch reads (not committed)
outputs/batch/  activity, risk, budgets, traces, id-checks, checkpoints
docs/           brief, anomaly report, visualization, risk cards, decision record, pen map
yolo11s.pt      local detector weights
```

## Judging highlights

- **Originality.** Extra frames are spent only where the detector is unsure, so a full two-day pen fits an 8 GB laptop GPU. The work does not depend on a cluster or a paid endpoint.
- **Technical execution.** 1,749 clips were decoded, tracked, and checkpointed on the 4060. The ranker was then run on that table, not on a fixture.
- **Usefulness.** The useful output is the minute log, herd-level day-over-day comparison, and an explicit refusal to name a sick cow. A false id would have produced a confident, wrong ranking.
- **Completeness.** Commands above match the scripts. Limits are stated in `docs/technical-brief.md`.

## Not in this package

A stable id across clips, the Qwen weights, and the Level 3 live alert (cut to protect Level 1 and Level 2 and the deadline). `docs/visualization.html` is a static overview page, not a live dashboard. Raw video stays out of git.

## Honesty

Observed means a box and a geometric label in that clip. Assumed means the feeding band, the 0.45 cutoff, and night by the clock. Everything here is clip-level or herd-level evidence. This run cannot tell the ten cows apart across clips, so it does not rank or score individual animals. Some, all, or none of them may have BRD. The table does not say which.
