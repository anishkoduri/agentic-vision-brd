# Final report

The overnight batch finished. Deliverables were built from `outputs/batch/` without starting another batch.

## Done

- 1,749 checkpoints, one per clip in `data/readable/`. 0 clips missing. 604 checkpoints are `[]` (no cow box). Names are in `outputs/batch/empty_clips.txt`.
- `activity.csv`: 24,327 rows, one per track per minute after dedup (second look kept over the coarse read). Standing 13,659, lying 8,193, feeding 1,382, walking 1,093. All `evidence=observed`.
- `src/risk.py` `rank_minutes` ran on clip-qualified ids. 9,750 tracks, 0 singled out, reason `no day-over-day term`. Columns in `brd_risk.csv`: cow_id, score, rank, top_reasons. Score and rank are blank.
- The batch’s first risk file merged tracker numbers across clips. It is copied to `outputs/batch/audit/brd_risk.csv` and is not the ranking.
- Time budgets: `time_budgets.csv` (per clip-track, plus `HERD_AVERAGE` rows) and `time_budgets_by_camera.csv` (track-minutes by camera, day, clock day/night, plus pooled herd-average rows).
- ID stills: 283 of 288. Index `outputs/batch/id-checks/index.csv`. Five slots have no covering clip and are marked "no covering clip — frame not available" in the index.
- Traces: `outputs/batch/traces/success.md`, `failure.md`, `night.md` (with `.json` copies). Three different re-examined minutes; the VLM was not invoked.
- Cards: `docs/risk-cards.md`. Three cameras, three clips each, showing a repeated track number is not one cow.
- Brief: `docs/technical-brief.md`. README commands match the scripts.
- Tests: `tests.test_risk` and `tests.test_behavior`, 12 tests, OK. Includes a one-day track that must not receive a rank.

## Assumptions

- Night is the clock (20:00–06:00), not a light measurement.
- Feeding is the lower band of a front-camera frame. That rule is assumed.
- A clip covers the next 5 minutes when choosing an ID still. A slot outside that window is missing.
- Tracker ids reset every clip. Qualifying `cow_id` by the clip stem is the identity the ranker was given.

## Missing

- Stable identity of the ten cows across clips, cameras, and days. Hungarian handoff was not built.
- Qwen2.5-VL-3B weights. Uncertain labels stayed with the tracker.
- Dashboard, submission zip, and a measured accuracy.
- Five ID stills, because those minutes are not in the video.
- 604 clips with no box. Those minutes are not in `activity.csv`.

## Where it lives

| Piece | Path |
| --- | --- |
| Activity | `outputs/batch/activity.csv` |
| Risk | `outputs/batch/brd_risk.csv` |
| Withdrawn merge | `outputs/batch/audit/brd_risk.csv` |
| Budgets | `outputs/batch/time_budgets.csv`, `time_budgets_by_camera.csv` |
| Traces | `outputs/batch/traces/` |
| ID stills | `outputs/batch/id-checks/` |
| Cards | `docs/risk-cards.md` |
| Brief | `docs/technical-brief.md` |
| README | `README.md` |

A score is not a diagnosis. Some, all, or none of the cows may have BRD. This package does not say which.
