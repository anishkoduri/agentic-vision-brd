# Technical brief — Challenge 2

Pen 6, ten Angus, two days, three cameras. The question was which animals changed how they used the pen. The answer this run can support is narrower: what each camera saw, minute by minute, and that no animal can yet be followed from one clip to the next.

## Approach

The differentiator is that all compute ran locally on a single laptop (NVIDIA GeForce RTX 4060 Laptop, 8 GB VRAM), with no cloud, no HPRC, no Databricks, and no paid services. Adaptive sampling, with the 3 fps re-examination used only where the box was below 0.45 confidence, kept the full 1,749-clip run feasible on that hardware. The stack is Python, PyTorch 2.11.0+cu128, Ultralytics 8.4.213, YOLO11-small (COCO cow class 19), and ByteTrack with BoT-SORT as a fallback.

The HEVC-in-AVI sources were remuxed (copied, not re-encoded) to `hvc1` in `data/readable/` so OpenCV could open all 1,749.

A coarse pass keeps one 640×480 frame every 10 seconds. Extra frames are spent only where the model is unsure: a box under 0.45 confidence opens one 4-second window at 3 frames per second. That window ran in 1,113 clips and was skipped in the rest. The quantized Qwen2.5-VL-3B weights are not on this disk, so an uncertain minute kept the tracker’s geometric label.

Labels use the box, not appearance. A wide box is lying. A centroid that moved is walking. A box low in a front-camera frame is feeding. Cam 03 is the back camera; Cam 01 and Cam 02 are the front cameras.

## Results

All 1,749 clips have a checkpoint. 604 (35%) returned no cow boxes. The detector saw no cow there, which fits an empty pen view but is not proof: 562 are from the two front cameras and 402 fall between 18:00 and 03:59, so low light may hide some animals. They are excluded from `activity.csv`, so a gap means “no detection,” never “standing” or “absent.”

`activity.csv` has 24,327 rows, one per track per minute (a second 3 fps look replaces the coarse read): standing 13,659, lying 8,193, feeding 1,382, walking 1,093. A row is one tracker inside one clip for one minute, not 10 cows times 1,440 minutes times 2 days. Day and night budgets (night is 20:00–06:00) are in `time_budgets_by_camera.csv` and `time_budgets.csv`; both are track-minutes, not ten identified cows. Of 288 requested ID-check stills, 283 exist; five slots have no covering clip, so none was invented.

The three traces (`outputs/batch/traces/`) each follow one re-examined minute through Observe, Question, Verify, Revise. Success: feeding, 0.19 to 0.81, front cam 1, day 2 at 08:51. Failure: standing 0.31 became walking 0.10, back cam, day 1 at 01:34. Night: lying 0.40 became standing 0.83, back cam, day 1 at 04:39. The check was tracker confidence plus the 3 fps window.

## Risk: what a veterinarian would look at first

Reduced feed intake is an early sign of BRD (spec §1), so we looked first at herd feeding. On Day 2 the feeding share fell sharply at midday: at 13 h from 26.6% on Day 1 to 0.7% (about 25 percentage points) and at 12 h from 17.9% to 0.2%, while lying rose over the same hours (13 h: 10.8% to 57.0%; 12 h: 23.2% to 44.1%). Less eating with more lying is a pattern a veterinarian would recognize as worth investigating first. It is a herd-level signal with a caveat: feeding is labeled only on the front cameras, and front-camera track-minutes at 13 h fell from 830 to 28, so part of the drop is fewer cows in view (`docs/anomaly-report.md`). Some, all, or none of the cows may have BRD, and this analysis does not diagnose any individual cow.

A per-cow ranking requires following the same animal across clips and days, and that cross-clip identity was not solved. So `brd_risk.csv` leaves score and rank blank on every row rather than fabricate them (0 of 9,750 tracks singled out), and the herd-level signal is reported instead. `top_reasons` in the CSV holds each tracklet’s observed features against the herd. A tracker number such as `Cam 03-t1` is issued again in the next clip, so `docs/risk-cards.md` explains clip-level tracklets in veterinary terms, not animals. An earlier file that grouped them as one cow is archived in `outputs/batch/audit/` and is not evidence.

## Limitations and honesty

Observed: boxes, geometric labels, confidences, clip times, and the ranker’s refusal. Assumed: the feeding band (a region of the frame, not a bunk sensor), the 0.45 cutoff, the 10-second grid, and night defined by the clock.

The identity limit. ByteTrack numbers tracks inside one clip and restarts them in the next, so no ID survives across clips. The animals are black and untagged and we built no appearance matching, so a track in one clip cannot be called the animal in another. That blocks the Level 2 goal. Our evidence is herd-level and tracklet-level (`docs/visualization.html`).

Not observed: which of the ten cows is which. Not claimed: that any cow has BRD, or that any cow does not. The Level 3 live alert was cut because it would have threatened Level 1 and Level 2 polish and the deadline. No labeled accuracy was measured, so none is stated.

## With more data

Identity across clips would come first, since it unlocks a per-cow, day-over-day comparison. **Early-warning design.** A live system would watch new video on the same single laptop, rerun the detector and the geometric labels, recompute the feeding and lying share for each hour, and compare each hour with the same hour the day before. When the feeding share drops sharply, it would send a pen-rider alert with the clip as evidence. This is a design, not a running live system: nothing here was built or tested, and the alert threshold would be set with a veterinarian. It is built to run on local ranch hardware (a single laptop, no cloud), so a producer could run it.
