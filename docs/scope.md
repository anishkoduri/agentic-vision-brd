# Scope — Pen 6 agentic vision

Source: `docs/decision-record.md`. Hours-left: **20** (package by Sunday Nov 15, 2026, 4:00 PM CST). Official slack until 11:00 PM CST is not scheduled work.

Platform: responsive web dashboard (Next.js + FastAPI) plus a local Python batch on the Windows laptop (RTX 4070, 8 GB). The prompt asked for this web dashboard. No native-app conversion.

Design direction: Restrained agricultural. Closest Hallmark catalog theme, name recorded when the theme deal runs. Dense operational dashboard. Observed and estimated stay visually distinct. “Not visible” stays honest. Fraunces is body-only, never the main visible text.

Next step: `feature-expansion` Phases 0–3, then `orchestrate` builds. `orch-build-mvp` does not run in this same run.

## Wow test

A judge opens cow rank 1 and sees a change a pen rider would recognize: she visited the bunk less than the herd and less than she did on day 1, the minute timeline shows when, and two clips play from the cameras that actually saw her. Beside it, an agent trace shows the model looked at the other camera and at an earlier minute before it kept the label. One of the three traces is an honest failure. That is the stare moment. A score with no clip is not.

## Project assessment

- Strengths: The rubric, the stack, the outputs, and the cut order are already decided. Level 2 is a relative rank on ten cows, which two days of video can support. Pretrained YOLO and a small VLM fit the laptop.
- Weaknesses: Ten black cows will not separate on appearance. The browser partials were not growing at 8:30 PM. Night frames are hard. 8 GB cannot hold YOLO and the 3B VLM together.
- Opportunities: An honest failure trace plus vet-language reasons tied to real clips is what the panel (a veterinarian and an animal scientist) can trust. Most teams will either fake certainty or skip the agent loop.
- Constraints: 20 hours to a zipped package. Active only tonight and Sunday morning through mid-afternoon. One laptop. No second download. No paid API. Event video stays in `data/` and out of git.
- Recommended direction: Ship a true Level 1 minute record and a Level 2 rank a veterinarian can audit from clips. Level 3 waits until that package exists.

## Winnable category

Level 2 tiebreak: a relative behavioral rank with video-backed reasons, on top of a complete Level 1. The second tiebreak is the two-page brief. We are not competing on “most models” or on a live alert that puts the CSVs at risk.

## Must-have (P0, plus the traces the prompt refuses to cut)

1. Watch the existing browser download. Unzip each finished `Problem 2_ BRD Agentic Vision-….zip` into `data/raw/`. Write an inventory (file, camera guess, duration, fps, resolution). Do not download again.
2. Coarse detect + per-camera track + minute rows for every camera-hour that actually arrives. Checkpoint per camera-hour. Resume.
3. `activity.csv` with one row per cow per minute that the inventory covers. Columns: cow_id, day, minute, behavior, cameras, confidence, visible, evidence flag (`observed` / `estimated` / `assumed`). Minutes with no video stay `other / not visible`, never a guessed behavior. Target shape is 28,800 rows when both days and all cameras are present; a shortfall is a listed gap, not a padded row.
4. Cross-camera identity report: per cow, how often the handoff agreed, and where it failed. Appearance is a weak feature and the report says so.
5. ID-check frames every 30 minutes on each camera that was processed, plus an index. Missing slots are listed.
6. Per-cow time budgets, day vs night, plus the herd average.
7. `brd_risk.csv`: relative score 0–1, rank 1–10, top reasons in herd-manager language. No cow is pre-labeled sick.
8. Top-3 one-page risk cards, each with 2–3 real clips.
9. Dashboard that reads those files: timeline per cow, rank, evidence clips, observed vs estimated vs not visible.
10. Three agent traces (success, failure, night) on ambiguous cases only.
11. Two-page brief and a README whose commands reproduce the CSVs from raw video. Model name, version, and quantization recorded. AI tools disclosed.
12. Submission zip with code, outputs, brief, README. Raw video listed as “obtain from the Drive folder,” not committed.

## Cut list

- Level 3 live alert. Reason: P1, only after the Sunday package exists. Cut first if Sunday slips.
- Extra charts beyond the timeline, rank, and clips. Reason: P2.
- Databricks, HPRC setup, a second download, teammate GPU. Reason: recorded decisions.
- Training a detector or a ReID net from scratch. Reason: pretrained YOLO-small and BoT-SORT. Off-the-shelf is the prompt.
- Certain ruminating labels at 1 frame / 5 s. Reason: jaw motion is not in those frames.
- Population claims, diagnostic wording, unmeasured accuracy numbers. Reason: honesty rules.
- `/demo` video and a narration key. Reason: the user did not ask.
- Auth, a hosted database, cloud deploy. Reason: nobody asked; the judge reads a repo and a local dashboard.
- Inventing minute rows for video that has not arrived. Reason: that is a fake Level 1. Cut substance: padded activity rows — honesty rule. The code still runs on a tiny synthetic fixture so Sunday is not blocked on code, and that fixture is never submitted as event data.

## Demo storyboard (finalist talk, 4 minutes)

The scored artifact is the repo and the brief. This is the path through them if the team presents Tuesday, and the path a judge takes on Sunday’s zip.

1. 0:00–0:30 — Pen 6, ten Angus cows, three cameras, two days. Staff still find BRD by looking. Early signs are a change in feeding, lying, and isolation, not a diagnosis from a model.
2. 0:30–1:30 — Open the dashboard on `brd_risk.csv`. Ten ranks. Pick rank 1. The timeline shows day vs night and day 1 vs day 2. The label on each block says observed, estimated, or not visible.
3. 1:30–2:30 — Wow: play the two bunk clips and the comparison to her own day-1 baseline and to the herd. Show the agent trace that fetched the other camera before keeping the behavior. Then show the failure trace.
4. 2:30–3:30 — ID-check frame and the consistency report, including a cow the cameras lost. Time-budget chart against the herd average.
5. 3:30–4:00 — What two days and ten cows cannot support. What we would do with ear tags, a waterer polygon from the farm, and a third day. Level 3 only if it is actually in the zip.

## Time budget

20 hours, split on the user’s real schedule rather than a pretend rehearsal block. The overnight third is compute.

| Block | When | Job |
|---|---|---|
| First third (~7h) | Tonight, active | Watcher + inventory, pipeline code, tests on a synthetic clip and on the first real file that lands, dashboard skeleton that reads CSVs, kick off the resumable coarse pass |
| Middle third (~7h) | Overnight, unattended | Coarse detect + track, checkpointed per camera-hour. A crash loses at most one hour |
| Last third (~6h) | Sunday morning–4:00 PM, active | Spot-check IDs, fix the worst identity errors, risk rank, cards, traces, dashboard against real CSVs, brief, zip |

Slack 4:00–11:00 PM CST is unused on purpose.

## Vertical slices

1. First finished zip → inventory row (hour 0 of tonight).
2. One camera-hour → detections, tracks, minute rows, one ID-check contact sheet.
3. Those rows → one cow’s time budget and a provisional rank input.
4. Dashboard reads the real CSV, including an empty and a not-visible state.
5. Only then the full overnight sweep.

## Technical substance

### Ingest
- Architecture: Chrome writes Downloads → watcher sees a stable `.zip` → extract under `data/raw/<part>/` → `outputs/ingest/manifest.jsonl`.
- Algorithm: filename parse plus `ffprobe` (duration, fps, width, height). Identity of the camera is a recorded mapping, not a guess from the BRD’s “top” wording.
- Performance budget: do not unpack a file until its size is unchanged for 15 s; one zip at a time; leave `.crdownload` untouched.
- Edge cases: still-growing zip (skip); papers zip (ignore by name); bad zip (log, do not delete the source); duplicate part (ledger says already extracted).

### Detect, track, minute activity
- Architecture: FFmpeg frame sample → YOLO-small → ByteTrack per camera → minute aggregator → `activity.csv`. Checkpoints under `outputs/checkpoints/<camera>/<hour>`.
- Algorithm: ByteTrack on the coarse 1/5 s boxes. BoT-SORT/ReID only when a track breaks inside one camera. Minute label is the mode of in-minute samples, with confidence as agreement, and `visible=false` when no box survived.
- Performance budget: YOLO-small only, batch sized to stay under 8 GB, checkpoint every camera-hour, resume from the last checkpoint, no image dump of the 103,680 frames.
- Edge cases: missing hour (gap row, not a guess); zero detections (not visible); duplicate checkpoint (skip completed hour); process kill (resume, do not restart the camera).

### Cross-camera identity
- Architecture: per-camera tracklets → homography-free zone handoff using the pen map → appearance embedding as a tie-break only → `outputs/identity/consistency.csv`.
- Algorithm: a cow that exits one camera’s overlapping zone must enter the geometrically expected zone of another within a short time window. Match score is zone + time, with appearance as a weak prior. Unmatched tracklets stay provisional IDs and are counted as failures.
- Performance budget: identity is CPU-side on stored tracklets, not a second full detect pass. Report a consistency fraction per cow.
- Edge cases: two cows in the same zone (do not merge; mark ambiguous); night track with no appearance (zone+time only, lower confidence); cow never seen on a camera (say so); appearance conflict with geometry (geometry wins, conflict logged).

### Behavior
- Architecture: minute samples + zone polygons → one of the ten classes.
- Algorithm: feeding = bunk zone and head-down posture proxy; drinking = waterer zone once the zone exists; lying vs standing from bbox aspect; walking from displacement; ruminating only if the segment was sampled at 2–5 FPS, else the class is refused. Social = two cows in proximity. Else other / not visible.
- Performance budget: one label per cow-minute; rumination attempts limited to the higher-FPS subset, not the 103,680-frame pass.
- Edge cases: zone not yet derived (behavior `estimated` or `other`, never a fake drink); occlusion (not visible); class tie (lower-confidence class, flag estimated); bunk zone with a standing cow facing away (not feeding).

### BRD rank
- Architecture: `activity.csv` → per-cow day/night budgets → anomaly vector → `brd_risk.csv` and three cards.
- Algorithm: robust z-score of feeding minutes and feeding bouts versus the herd and versus that cow’s day 1; lying-minute excess; isolation minutes (no neighbor); circadian deviation (hour-of-day profile vs her day 1). Rank is the mean of the available z-scores, scaled to 0–1 within this pen. A missing day does not get a baseline term.
- Performance budget: the rank is a table scan of 28,800 rows, under 5 s on the laptop CPU. Every top-3 reason cites the minute ranges and the clip paths.
- Edge cases: all cows similar (scores compress near each other; say the pen shows no standout); one cow mostly not visible (down-weight, do not call her sick); day 2 missing (no day-over-day term); a single extreme hour (report it, do not let one hour set the rank alone — use the day total).

### Agent loop
- Architecture: queue of low-confidence minutes → Qwen2.5-VL-3B after YOLO is unloaded → tools: detect, track, crop, other-camera frame, t−Δ and t+Δ → trace JSON.
- Algorithm: the model must name the tool call and the frame it used. A revised label is kept only if the trace contains that frame path. Otherwise the tracker label stands.
- Performance budget: at most a few dozen VLM calls, not 103,680. One model resident at a time. Three traces written to `outputs/traces/`.
- Edge cases: VLM refuses or OOMs (keep tracker label, write the failure trace); night frame unreadable (failure trace is the deliverable); tool returns no other camera (say the cow was not visible there; do not invent a view).

### Dashboard
- Architecture: FastAPI serves the CSVs and clip files; Next.js renders rank, timeline, and a clip player. No second source of truth.
- Algorithm: read the CSVs. Do not recompute risk in the browser.
- Performance budget: first rank paint under 2 s on local data; clip starts from a local file path the API allows (no directory traversal).
- Edge cases: empty CSV (empty state, not a fake rank); not-visible minutes (distinct from estimated); missing clip file (card says the file is missing); malformed row (skip the row, show a count of skipped rows).

## Unknowns carried forward

| Unknown | Owner | Resolution |
|---|---|---|
| Filename → camera mapping | Builder | Ingest |
| Waterer and resting polygons | Builder | Behavior step, marked assumed |
| Which cows look sick | The rank | Level 2, from the data |
| HPRC | Builder | Only if the laptop cannot finish. Default laptop |
| Hallmark theme name | Design lead | Before any UI slice |
| When tonight’s batch starts | Builder | When the first complete files exist and the script is resumable |

## Pre-empted failures

- Download stall: watcher logs byte totals; no second client.
- Overnight crash: per-hour checkpoints.
- VLM OOM: YOLO process exits before the VLM process starts.
- Wifi drop after the files are local: the batch does not need the network.
- Judge opens the dashboard with no server: README has the one command, and the CSVs are readable without it.

## What MVP means here

A zipped repo a judge can clone, point at the video, and rerun, plus the CSVs, frames, traces, cards, and a two-page brief. The dashboard is the visualization tool the BRD requires. It is not a product for a thousand pens.
