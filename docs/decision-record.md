> **Status after the run (Nov 15, 2026):** this is the pre-run plan. Shipped results are in README.md, docs/technical-brief.md, and docs/final-report.md — RTX 4060 (not 4070), 24,327 rows (not 28,800), no per-cow rank, no dashboard, VLM not run, Level 3 is a design only.

# Decision record — Agentic Vision for Angus Behavior and BRD Prediction

Merck–TAMU Animal Science Hackathon 2026, Challenge 2.
Project root: this `pipeline` folder. Separate from BRDashboard. Do not touch that folder.
Status: grilling complete. Next skill: `hackathon-scope` (see `docs/scope.md`).

Posture: EXECUTION. The prompt decided the product. Grill-me asked only the gaps (hours, then the dataset location).

Clock at first prompt: Saturday Nov 14, 2026, 8:17 PM CST.
Hours-left number: **20** (internal package target, Sunday Nov 15, 2026, 4:00 PM CST).
Official deadline: Sunday Nov 15, 2026, 11:00 PM CST. That slack is not scheduled work.

Design direction: Restrained agricultural. Closest Hallmark catalog theme, name recorded when the theme deal runs. Dense operational dashboard. Observed and estimated stay visually distinct. “Not visible” stays honest. Fraunces is body-only, never the main visible text.

## Decisions

### 1 — Product and user
- INFERRED: none — the assignment is quoted in the BRD and the prompt.
- CHOSEN: A local system that watches Pen 6 around the clock, keeps one identity per cow across three cameras and two days, labels behavior every minute, and ranks which of 10 Angus cows may be getting sick before a person can see it. User: the herd manager. Actor on an alert: a pen rider. Judges: veterinarian, animal scientist, CV/AI specialists, beef technologist. Source: USER-STATED.
- REJECTED: A generic herd dashboard, a diagnostic device, a population study. Reason: the assignment is this pen, these two days, a risk rank, not a diagnosis.

### 2 — Hours left
- INFERRED: “Sunday afternoon” means the zip is ready by 4:00 PM CST Sunday, so Sunday evening stays free. Reasoning: the user said mid-afternoon is the end of active work and Sunday evening they are busy.
- CHOSEN: Full window to the official deadline, with work scheduled only through Sunday 4:00 PM CST (~20 hours from Sat 8:20 PM). Active: tonight for setup; Sunday morning through mid-afternoon for verification, the dashboard, and the brief. Overnight GPU is unattended. Source: USER-STATED window and active times; 4:00 PM clock is INFERRED.
- REJECTED: Using 11:00 PM as a work block. Reason: the user is busy Sunday evening. Also rejected: an 8-hour default. Reason: the user gave a real window.

### 3 — Named API
- INFERRED: none.
- CHOSEN: No hosted API. Local weights only (YOLO-small, quantized Qwen2.5-VL-3B). No paid service, no API key. Source: USER-STATED.
- REJECTED: Databricks, a cloud VLM API, any key prompt. Reason: the prompt forbids paid APIs and cloud GPU. HPRC only if access already exists; do not spend setup time. Default: the laptop.

### 4 — Dataset location
- INFERRED: none on the URL. The papers zip was identified by listing Downloads (11 MB, BRD PDFs).
- CHOSEN: Google Drive folder `https://drive.google.com/drive/folders/1-hwmEVNKO2kFf3VR7x8kkNrloAT1G5eO?usp=sharing`. The browser download is already running. Parts land in Downloads as `Problem 2_ BRD Agentic Vision-….zip` (~2 GB each). Watch Downloads, unzip each finished part into `pipeline/data/`, verify the inventory. Do not start a second download. The 11 MB `drive-download-20261114T210441Z-1-001.zip` is BRD papers, not video. Source: USER-STATED.
- REJECTED: A second download, `gdown`/rclone in parallel, treating the papers zip as video. Reason: the user forbade a second download, and the papers zip was opened and confirmed to be PDFs.

### 5 — Scoring priority
- INFERRED: none.
- CHOSEN: Polished Level 1, then Level 2 ranking, then Level 3 only if time remains. Level 2 is the first tiebreaker. Source: USER-STATED.
- REJECTED: Spreading effort across all three levels at once. Reason: a polished Level 1 beats a broken attempt at all three.

### 6 — Stack and platform
- INFERRED: none. The dashboard request is already web, so no native-to-web conversion was required.
- CHOSEN: Python + FFmpeg + OpenCV; Ultralytics YOLO-small; ByteTrack then BoT-SORT/ReID; quantized Qwen2.5-VL-3B for the agent loop only; NumPy/Pandas; statistical anomaly scoring; Next.js + FastAPI dashboard. Platform: responsive web dashboard plus a local Windows batch. Source: USER-STATED.
- REJECTED: Native iOS/Android, a Databricks notebook as the product, training a detector from scratch. Reason: the prompt names this stack, and pretrained weights are the off-the-shelf path.

### 7 — Compute
- INFERRED: none.
- CHOSEN: User’s Windows laptop. Observed device on 2026-11-15: NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB, driver 610.60. The batch refuses to start unless `torch.cuda` reports that 4060. Cursor writes code and scripts. The user starts the GPU batch. Stream frames. Checkpoint per clip. Never load YOLO and the 3B VLM together. Source: USER-STATED target device; GPU name observed with nvidia-smi.
- REJECTED: Cloud GPU, splitting compute across teammates’ machines. Reason: upload cost and weak teammate hardware.

### 8 — Sampling
- INFERRED: none.
- CHOSEN: Coarse pass 1 frame / 5 s (103,680 frames). 2–5 FPS only where identity, transitions, or ambiguity need it. VLM only for uncertain behaviors, clinical signs, and cross-camera checks. Rumination only on higher-FPS segments, and always lower confidence. Source: USER-STATED.
- REJECTED: VLM on every frame; a certain ruminating label at 1 frame / 5 s. Reason: 8 GB VRAM and jaw motion the coarse rate cannot see.

### 9 — Camera identity and zones
- INFERRED: the attached pen map matches the prompt’s warning (back cam top-left, two front cams by the bunk, chute on the left, bunk along the front). Which file is which camera is not knowable until video lands.
- CHOSEN: Do not assume the BRD’s “back, front, and top” labels. Verify the mapping from filenames and record it. If waterer and resting-area outlines are missing, derive zones from the video and mark them assumed. Source: USER-STATED.
- REJECTED: Hard-coding top/front/back from the BRD sentence. Reason: the pen map disagrees, and the prompt says verify.

### 10 — Identity and behavior
- INFERRED: none.
- CHOSEN: Per-camera tracks first, cross-camera match second (geometry, spatial handoff, appearance, time). Appearance is weak on identical black cows — say so. One behavior per cow per minute. “Other / not visible” is valid. The VLM never invents an ID and never overrides the tracker without video evidence in the trace. Source: USER-STATED.
- REJECTED: Appearance-only ReID as the primary key; hiding failed matches. Reason: black Angus cows will not separate reliably on coat color, and the prompt requires the failures reported.

### 11 — Agentic loop
- INFERRED: none.
- CHOSEN: A real loop on ambiguous cases only: Observe → Question → Verify (other camera, zoom, look back or forward) → revise → save the trace. Three traces: success, failure, night. An honest failure beats a fake success. Source: USER-STATED.
- REJECTED: A single-pass frame labeler presented as an agent. Reason: the BRD requires a model that plans, uses tools, and checks itself.

### 12 — Level 1 outputs
- INFERRED: none. The minute-row choice is the prompt’s own reconciliation of the BRD’s bout wording.
- CHOSEN: `activity.csv` 28,800 rows (cow_id, day, minute, behavior, cameras, confidence, visible). Bouts are grouped consecutive minutes; say so in the README. 288 ID-check frames plus an index. Per-cow time budgets, day vs night, plus the herd average. Three traces. Source: USER-STATED.
- REJECTED: Guessing a behavior when the cow is not visible. Reason: “other / not visible” is a legitimate value.

### 13 — Level 2 outputs
- INFERRED: none.
- CHOSEN: `brd_risk.csv` (cow_id, risk 0–1, rank 1–10, top reasons) from behavioral anomaly: less feeding vs the herd and vs her day-1 baseline, more lying, social isolation, broken daily rhythm. Top-3 risk cards with 2–3 clips each. Dashboard of timelines, rank, clips, alerts. Never assume a cow is sick. A score is not a diagnosis. Source: USER-STATED.
- REJECTED: A high score without a behavioral change; any accuracy number that was not computed. Reason: some or all cows may be healthy, and unmeasured metrics stay “not measured.”

### 14 — Level 3
- INFERRED: none.
- CHOSEN: Live alert on a fresh clip, VLM-checked clinical signs, clip saved. Build only after Level 1 and Level 2 are solid. Cut if it threatens the Sunday 4:00 PM package. Source: USER-STATED.
- REJECTED: Starting Level 3 tonight. Reason: P0 first.

### 15 — Honesty
- INFERRED: none.
- CHOSEN: Every output labels observed vs estimated vs assumed. No population claim, no claim past this pen and these two days, no diagnostic claim. Source: USER-STATED.
- REJECTED: Filling the brief with unmeasured accuracy. Reason: every number must trace to a computed output.

### 16 — Repo, theme, team, submission
- INFERRED: none.
- CHOSEN: All paths under this `pipeline` folder (`data/`, `src/`, `outputs/`, `dashboard/`, `docs/`, `README.md`). Raw video is never committed and never deleted. Theme is this project’s own restrained agricultural theme. Team of 3; the user does the work; no compute split. One repo or ZIP by the official deadline, packaged Sunday afternoon. README lists commands, model and version, quantization, outside data, and AI tools. `/demo` is not part of this build. Source: USER-STATED.
- REJECTED: A new folder outside `pipeline`; copying BRDashboard’s Furrow theme; filming a demo video automatically. Reason: the prompt forbids all three.

### 21 — Video container
- INFERRED: none on the container. The codec inside the avi is not measured until ffprobe runs on a finished event file.
- CHOSEN: Event video is `.avi`. Ingest runs ffprobe and then an OpenCV first-frame read. The detection batch does not start unless that read succeeds and the frame size matches ffprobe. Source: USER-STATED (container), this session.
- REJECTED: Starting YOLO on a file OpenCV cannot open. Reason: a codec OpenCV’s build cannot decode would waste the overnight pass.

### 22 — Camera mapping
- INFERRED: which front camera is 1 versus 2. Cam 01’s frame looks out from under the bunk roof toward the open end of the pen, with a gate on the image left. The pen map puts the chute on the left and Front cam 1 on that side.
- CHOSEN: Cam 01 (filename tail 006) is Front cam 1. Cam 02 (tail 017) is Front cam 2: the feed bunk fills the foreground. Cam 03 (tail 003) is the Back cam: the view is from the rear, and the bunk shelter is in the distance rather than in the foreground. Frames: `outputs/ingest/cam-frames/cam01.jpg`, `cam02.jpg`, `cam03.jpg`, compared with `docs/pen-map.png`. Source: observed frames.
- REJECTED: Treating the folder numbers as the pen-map names without a frame. Reason: decision 9.

## Download observation (Sat Nov 14, 2026, ~8:30 PM CST)

51 Chrome `.crdownload` files in Downloads, about 122 MB total. A 20-second sample showed 0 bytes of growth. No finished `Problem 2_ BRD Agentic Vision-….zip` yet. C: has about 510 GB free. Action: do not start a second download. Unzip only a `.zip` whose name matches the Problem 2 parts, after the size is stable. Leave `.crdownload` files alone.

## Risks

- The browser partials were not growing at 8:30 PM. If they stay paused, the overnight GPU pass has nothing to read. Owner: the user can resume Chrome; the builder does not launch a second download.
- Cross-camera identity on ten black cows can fail. Report the failure. Do not invent IDs.
- 8 GB VRAM. YOLO and the 3B VLM stay sequential.
- Night video is harder. The night trace is allowed to be an honest failure.
- Sunday active time ends mid-afternoon. A batch that is still running at noon squeezes the dashboard and the brief.

## Accepted unknowns

| Unknown | Owner | Resolution |
|---|---|---|
| Which filename is back / front cam 1 / front cam 2 | Builder | Resolved 2026-11-15 from one daytime frame each. See decision 22. |
| Waterer and resting-area polygons | Builder | Derive from video during behavior. Mark assumed. |
| Which cows, if any, show a BRD-like change | The ranking | Level 2. Never assumed in advance. |
| Whether HPRC is already usable | Builder | Only if the local pass cannot finish. Default: laptop. |
| Hallmark theme name | Design lead | Before the first UI slice, in `docs/design-tokens.md`. |
| Exact bedtime tonight | Builder | Kick the batch off when the first complete camera files exist and the script resumes. Do not wait on a clock time the user did not give. |

## Rejected alternatives

- Databricks or any second copy of the 50 GB download.
- Appearance-only identity, hidden match failures, invented sickness, diagnostic wording.
- VLM-on-every-frame, joint YOLO+VLM load, certain rumination at 1/5 s.
- Level 3 before P0, P2 charts before the required CSVs, a new project folder, Furrow, automatic `/demo`.

## Completion criteria

Grilling is done. The package is done when P0 is real and zipped before Sunday 4:00 PM CST: inventory, `activity.csv` (28,800 rows) or an explicit gap list for minutes the video does not cover, ID-check frames for completed time, time budgets, `brd_risk.csv`, top-3 cards with clips, a dashboard that reads those files, three agent traces, a two-page brief, and a README whose commands match the scripts. Missing video is reported, not filled in.
