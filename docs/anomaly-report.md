# Anomaly report — Pen 6, Day 1 vs Day 2

> **Scope: herd-level and tracklet-level evidence only.** Tracker IDs are assigned per clip and none survives across clips, so this report does **not** identify individual cows, does **not** follow any animal from Day 1 to Day 2, and does **not** rank cows 1–10. A tracklet is one track number inside one clip.

Source: `outputs/batch/activity.csv` (24,327 track-minutes) and `outputs/batch/time_budgets.csv` (same 24,327 track-minutes, cross-checked). A *track-minute* is one tracked box in one minute; behavior labels are geometric rules on bounding boxes (observed), not a diagnosis.

## 1. Herd day-over-day change

Coverage differs by day: Day 1 has 868 clips and 14,732 track-minutes, Day 2 has 881 clips and 9,595. Day 2 has more empty clips (357 vs 247), which contribute no rows. Raw counts therefore move with coverage and camera mix; the share-of-track-minutes column is the fairer comparison.

| Behavior | Day 1 min | Day 2 min | Change (min) | Change (%) | Day 1 share | Day 2 share | Share change (pp) |
|---|---:|---:|---:|---:|---:|---:|---:|
| standing | 8,712 | 4,947 | -3,765 | -43.2% | 59.1% | 51.6% | -7.6 |
| lying | 4,434 | 3,759 | -675 | -15.2% | 30.1% | 39.2% | +9.1 |
| feeding | 892 | 490 | -402 | -45.1% | 6.1% | 5.1% | -0.9 |
| walking | 694 | 399 | -295 | -42.5% | 4.7% | 4.2% | -0.6 |
| **total** | 14,732 | 9,595 | -5,137 | -34.9% | 100% | 100% | — |

Camera mix check (share of track-minutes within each camera) — a herd shift that appears in only one camera is more likely a view effect than a herd effect:

| Camera | Behavior | Day 1 share | Day 2 share | Share change (pp) |
|---|---|---:|---:|---:|
| front_cam_1 | standing | 55.8% | 44.5% | -11.3 |
| front_cam_1 | lying | 20.9% | 30.2% | +9.3 |
| front_cam_1 | feeding | 19.1% | 19.7% | +0.6 |
| front_cam_1 | walking | 4.2% | 5.6% | +1.4 |
| front_cam_2 | standing | 70.0% | 62.9% | -7.1 |
| front_cam_2 | lying | 13.5% | 15.4% | +1.9 |
| front_cam_2 | feeding | 0.5% | 0.6% | +0.0 |
| front_cam_2 | walking | 16.0% | 21.1% | +5.1 |
| back_cam | standing | 58.7% | 53.0% | -5.7 |
| back_cam | lying | 38.6% | 45.3% | +6.7 |
| back_cam | feeding | 0.0% | 0.0% | +0.0 |
| back_cam | walking | 2.7% | 1.7% | -1.0 |

## 2. Top 10 most anomalous tracklets

Method: 1,805 tracklets with at least 4 tracked minutes and mean box confidence ≥ 0.5. For each behavior, a tracklet's share of its own minutes is compared with the mean share across all tracklets from the **same camera on the same day** (cameras are compared separately because the feeding band only exists in the front views). Deviation is the z-score (share − herd mean) ÷ standard deviation. Each tracklet is scored on its most extreme behavior; at most one tracklet per clip is listed.

| # | Clip | Camera | Day | First minute of behavior | Track no. | Behavior | Tracklet share | Herd mean | Deviation (z) |
|--:|---|---|--:|---|--:|---|---:|---:|---:|
| 1 | `Event20261108033052003.Avi` | back_cam | 2 | 03:31 | 1 | walking | 50% of 4 min | 0.6% | +11.0 |
| 2 | `Event20261108142134003.Avi` | back_cam | 2 | 14:23 | 10 | walking | 50% of 4 min | 0.6% | +11.0 |
| 3 | `Event20261108043056003.Avi` | back_cam | 2 | 04:33 | 1 | walking | 50% of 4 min | 0.6% | +11.0 |
| 4 | `Event20261107094945003.Avi` | back_cam | 1 | 09:51 | 6 | walking | 50% of 4 min | 1.3% | +8.7 |
| 5 | `Event20261107135022017.Avi` | front_cam_2 | 1 | 13:50 | 2 | feeding | 75% of 4 min | 1.5% | +8.2 |
| 6 | `Event20261107090952006.Avi` | front_cam_1 | 1 | 09:11 | 20 | walking | 75% of 4 min | 2.5% | +8.0 |
| 7 | `Event20261107094445003.Avi` | back_cam | 1 | 09:47 | 6 | walking | 40% of 5 min | 1.3% | +6.9 |
| 8 | `Event20261107062931003.Avi` | back_cam | 1 | 06:32 | 5 | walking | 40% of 5 min | 1.3% | +6.9 |
| 9 | `Event20261108162543006.Avi` | front_cam_1 | 2 | 16:26 | 5 | walking | 50% of 4 min | 1.7% | +6.2 |
| 10 | `Event20261108101130006.Avi` | front_cam_1 | 2 | 10:13 | 10 | walking | 50% of 4 min | 1.7% | +6.2 |

## 3. Behavior by hour

From `activity.csv` only (hour = minute of day ÷ 60; observed rows only; empty clips have no rows, so an hour with few rows may also be an hour with many empty clips). Shares are of that hour's track-minutes on that day. Feeding can only be labeled on the front cameras, so all-camera feeding share also moves with how many front-camera rows exist.

| Hour | Day 1 track-min | Day 2 track-min | Feeding D1 | Feeding D2 | Feeding Δ (pp) | Lying D1 | Lying D2 | Lying Δ (pp) | Note |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| 00 | 167 | 306 | 0.0% | 0.0% | +0.0 | 53.9% | 60.1% | +6.2 |  |
| 01 | 339 | 340 | 1.2% | 0.9% | -0.3 | 22.4% | 45.0% | +22.6 |  |
| 02 | 314 | 268 | 0.0% | 0.4% | +0.4 | 61.8% | 43.7% | -18.1 |  |
| 03 | 249 | 288 | 0.0% | 2.8% | +2.8 | 69.1% | 63.2% | -5.9 |  |
| 04 | 431 | 272 | 0.2% | 0.4% | +0.1 | 67.5% | 60.7% | -6.9 |  |
| 05 | 308 | 118 | 0.0% | 3.4% | +3.4 | 61.7% | 56.8% | -4.9 |  |
| 06 | 787 | 329 | 0.9% | 0.6% | -0.3 | 33.8% | 43.5% | +9.7 |  |
| 07 | 1,143 | 548 | 5.3% | 0.4% | -5.0 | 16.8% | 45.1% | +28.3 |  |
| 08 | 995 | 768 | 0.7% | 6.5% | +5.8 | 26.3% | 28.9% | +2.6 |  |
| 09 | 905 | 761 | 3.6% | 7.5% | +3.8 | 33.0% | 30.1% | -2.9 |  |
| 10 | 776 | 712 | 2.3% | 6.3% | +4.0 | 27.6% | 36.4% | +8.8 |  |
| 11 | 623 | 519 | 0.0% | 0.0% | +0.0 | 62.9% | 48.4% | -14.6 |  |
| 12 | 1,107 | 644 | 17.9% | 0.2% | -17.7 | 23.2% | 44.1% | +20.9 |  |
| 13 | 1,065 | 570 | 26.6% | 0.7% | -25.9 | 10.8% | 57.0% | +46.2 |  |
| 14 | 1,139 | 649 | 10.9% | 6.0% | -4.9 | 14.7% | 31.0% | +16.3 |  |
| 15 | 951 | 522 | 3.0% | 3.4% | +0.4 | 22.6% | 35.4% | +12.8 |  |
| 16 | 847 | 837 | 7.2% | 16.4% | +9.2 | 13.0% | 23.1% | +10.1 |  |
| 17 | 1,063 | 807 | 4.7% | 14.4% | +9.7 | 23.4% | 20.2% | -3.2 |  |
| 18 | 303 | 114 | 0.0% | 0.0% | +0.0 | 49.2% | 71.9% | +22.8 |  |
| 19 | 366 | 128 | 2.5% | 0.0% | -2.5 | 51.9% | 70.3% | +18.4 |  |
| 20 | 175 | 17 | 0.0% | 0.0% | — | 66.3% | 29.4% | — | ⚠ n<100: noisy, no conclusion |
| 21 | 135 | 0 | 0.0% | — | — | 47.4% | — | — | ⚠ n<100: noisy, no conclusion |
| 22 | 211 | 10 | 1.4% | 0.0% | — | 46.4% | 40.0% | — | ⚠ n<100: noisy, no conclusion |
| 23 | 333 | 68 | 1.2% | 2.9% | — | 19.8% | 11.8% | — | ⚠ n<100: noisy, no conclusion |

**(1) Feeding share.** Largest Day 1 → Day 2 changes: 13 h: 26.6% → 0.7% (-25.9 pp); 12 h: 17.9% → 0.2% (-17.7 pp); 17 h: 4.7% → 14.4% (+9.7 pp).

Feeding share fell by more than 1 pp in 5 of 20 comparable hours (07 h, 12–14 h, 19 h) and rose by more than 1 pp in 7 (03 h, 05 h, 08–10 h, 16–17 h). The drop is **concentrated**: 12–13 h hold 78% of the summed percentage-point decreases, the other hours with a drop are small, and 7 hours move the other way, so the whole-day change of -0.9 pp is the net of a concentrated decrease and offsetting increases.

Coverage caveat at 13 h: feeding is only labeled on the front cameras, and front-camera track-minutes went from 830 (Day 1) to 28 (Day 2) while all-camera track-minutes were 1,065 and 570. Part of that drop reflects fewer cows in the front views, and these files cannot separate fewer cows feeding from fewer cows in view. The Day 2 front-camera sample at 13 h (28 track-minutes) is too small to say what share of those cows were feeding.

Coverage caveat at 12 h: feeding is only labeled on the front cameras, and front-camera track-minutes went from 673 (Day 1) to 114 (Day 2) while all-camera track-minutes were 1,107 and 644. Part of that drop reflects fewer cows in the front views, and these files cannot separate fewer cows feeding from fewer cows in view. Within front-camera rows alone, feeding went from 29.4% to 0.9% at 12 h, so the drop is not only a coverage effect.

**(2) Standing-to-lying shift.** Lying share rose in 13 of 20 comparable hours and fell in 7 (02–05 h, 09 h, 11 h, 17 h). In 11 of the 13 hours where lying rose, standing share fell. Largest rises: 13 h: 10.8% → 57.0% (+46.2 pp); 07 h: 16.8% → 45.1% (+28.3 pp); 18 h: 49.2% → 71.9% (+22.8 pp). Largest falls: 02 h: 61.8% → 43.7% (-18.1 pp); 11 h: 62.9% → 48.4% (-14.6 pp). The shift is **broad but uneven, not concentrated in one window**: most hours go the same way, but large opposite-sign hours exist and the biggest swings are in a few hours rather than a single block.

**(3) Small samples.** Day 2 has fewer than 100 track-minutes in: 20 h (n=17), 21 h (n=0), 22 h (n=10), 23 h (n=68). These hours are flagged in the table, their changes are not computed, and no conclusion is drawn from them. Where Day 1 and Day 2 have a few hundred track-minutes, shares can still swing both ways, because track-minutes from the same tracklet are correlated and the effective sample is smaller than the count.

**Reading the pattern.** These are the hours where the herd-level behavior changed most; a veterinarian would look at these windows first. They are not a BRD signal, they are not tied to any cow, and no hour-level change here says anything about disease. The by-hour pattern is mixed rather than clean (see callouts 1 and 2), so treat it as descriptive.

## 4. How to read this

- Large deviations on rare behaviors (walking, feeding in the front views) are largely a small-denominator effect: a tracklet that spends most of its minutes doing something rare scores high even though one such tracklet is ordinary.
- A deviation is a departure from the herd mean in the *geometric label*. It can reflect a box change (occlusion, a neighbor merging into the box, camera angle) as easily as a behavior change. Open the linked clip before reading anything into a row.
- Track numbers repeat across clips (`1`, `2`, … restart in every clip), so a number in this table is **not** the same animal as the same number elsewhere.
- Nothing here is a health finding. A score is not a diagnosis, and some, all, or none of the cattle may have BRD.

## 5. What we could not measure

Hour-level patterns are herd-level: they cannot be attributed to individual cows, because no animal is followed across clips.

Regenerate: `python scripts/build_overview.py`.
