> **Status after the run (Nov 15, 2026):** this is the pre-run plan. Shipped results are in README.md, docs/technical-brief.md, and docs/final-report.md — RTX 4060 (not 4070), 24,327 rows (not 28,800), no per-cow rank, no dashboard, VLM not run, Level 3 is a design only.

# Expansion — planner pass

Phases 0–3. Lenses: [demo impact](9655e7d2-4bac-4993-af39-9c0d60cd3c13), [depth](0c520028-857e-4199-abbc-bce4174f4f95), [bold bets](42b4e6c6-d958-48ce-a5c8-73b9e82dee5f), [memorable moments](61fee19c-be9d-4c6c-8a82-8450bcbea133). Lists also in `.hackathon/lens-a.md`, `lens-b.md`, `lens-c.md`. Lens D was taken from its finished return.

Story: A herd manager sees who changed, the minute it started, and when missing video or a bad ID is too weak to single her out. A score is not a diagnosis.

Hours-left: 20. These ride beside P0. They do not replace `activity.csv`, the identity report, the three traces, or the brief.

Scores are value / originality / feasibility / differentiation / demo / effort-ease, each 1–3. Effort-ease is high when the work is small.

## Approved

| # | Feature | Why | Effort | Depends | UI | Tool/API | Scores | Verdict |
|---|---------|-----|--------|---------|----|----------|--------|---------|
| 1 | Evidence clips open on the cited minute, day 1 beside day 2, with a poster still and a blank tile where a camera did not see her | The judge sees the change in one glance | M | risk cards | Y — card | ffmpeg | 3/2/3/2/3/2 | Approve |
| 2 | Rank is computed on visible minutes only; the all-minutes score sits beside it; isolation counts only when she is visible and alone | A lost cow cannot look sick | S | activity.csv | Y — rank | numpy, pandas | 3/2/3/3/3/3 | Approve |
| 3 | Subtract the herd’s shared hourly feeding and lying profile, then flag a meal she skipped while visible elsewhere (≥7 cows at the bunk) | A pen-wide slow day does not create ten alerts, and a skipped meal is a rider cue | M | activity.csv | Y — card | numpy | 3/3/3/3/3/2 | Approve |
| 4 | Minutes with two tracklets claiming one cow in incompatible zones stay out of the rank; if a card’s clips are not one ID, the reason is withheld. Consistency CSV includes leave-one-camera-out agreement | A swapped ID cannot become a feeding collapse | M | tracklets | Y — card | numpy | 3/3/2/3/2/2 | Approve |
| 5 | Mark the first sustained minute she diverged from her own day-1 clock | The clip is “when,” not only “less than yesterday” | M | activity.csv | Y — timeline | numpy | 3/3/3/3/3/2 | Approve. Bold bet. Fallback: no marker; the card uses day totals |
| 6 | Show how many feeding minutes would swap her with the next cow | Close ranks read as fragile, not as a clinical cut | S | brd_risk.csv | Y — rank | numpy | 2/2/3/2/2/3 | Approve |
| 7 | Flag “insufficient evidence to single her out” when she is mostly unseen, one hour dominates, or the whole pen’s scores are compressed | The table can refuse a pull | S | rank | Y — rank | none | 3/3/3/2/3/3 | Tweak: this wording, not a medical “do not pull” order |
| 8 | Header strip of camera-hours on disk versus gaps | Missing video is obvious before anyone reads a rank | S | inventory | Y — header | none | 2/1/3/1/2/3 | Approve |
| 9 | A rank-1 route that opens her card, both days, and the traces already staged | The first paint is the stare moment | S | dashboard | Y — route | none | 2/1/3/1/3/3 | Approve |
| 10 | Up to nine VLM checks (3 cows × 3 reasons): keep, refuse, or cannot tell, with the frame on the card | A cited reason can lose its bullet after the model looks | M | clips, agent | Y — card | Qwen2.5-VL-3B | 3/3/2/3/3/2 | Approve. VLM does not score risk and does not invent an ID |
| 11 | Each activity row carries its camera-hour checkpoint id; a dark hour raises the YOLO confidence and marks surviving labels estimated | A label can be traced, and night noise is not lying time | S | checkpoints | N | OpenCV, numpy | 2/1/3/2/1/3 | Tweak: one luminance constant and a column, not a second detect pass |

Hungarian assignment per handoff window is not an expansion. It is how the P0 identity step will match tracklets. Appearance stays a logged tie-break. Fallback if the cost matrix is flat: leave both IDs provisional.

Feeding bouts are not an expansion. The prompt already scores feeding visits. The rank module will run-length-encode them.

## Order

1. Feature 11, with the coarse pass.
2. Features 2, 3, 5, 6, 7, in one rank module, after minute rows exist.
3. Feature 4, after tracklets exist.
4. Feature 1, after the rank cites minutes.
5. Feature 10, Sunday, after YOLO is unloaded.
6. Features 8 and 9, with the dashboard.

## Risks

| # | Breaks if | Fallback |
|---|-----------|----------|
| 1 | The cited minute has no frame | Card says the frame is missing. No stand-in from another minute |
| 2 | A cow is almost never visible | Her visible-only score is blank and feature 7 fires |
| 3 | Fewer than 7 cows are ever seen feeding together | Meal-dropout term is omitted and the card says so |
| 4 | Quarantine removes most of her minutes | No rank reason from those minutes. Report the count |
| 5 | Gaps break the day-1 clock | No change-point marker. Day totals remain |
| 6 | Scores are tied | Tag “tied,” not a fake minute delta |
| 7 | Thresholds are arbitrary | They are written in the brief as assumptions |
| 8 | Inventory is empty | Empty strip, not a full bar |
| 9 | Rank CSV is empty | Route shows the empty state |
| 10 | VLM OOMs or the overnight pass is still running | Reasons stay “not checked.” Tracker labels stand |
| 11 | Luminance threshold is wrong for this barn | Constant lives in one config value. Labels stay estimated, not certain |

## Rejected

- Full three-counterfactual “courtroom” UI. Too large. Features 2, 4, and 6 are the smaller version.
- `ruptures` for the change-point. A few lines of CUSUM do it. No new dependency.
- “At the bunk, head not down” as a rank term. One frame every 5 seconds cannot support head pose.
- Bunk arrival-order as its own score. Meal dropout is the rider cue that fits the time.
- Click-a-timeline-block to seek. The clip already opens on the cited minute.
- Animated pen-map handoff. The consistency CSV and the ID-check frames carry identity.
- A separate rank-1-versus-median chart. The herd residual is that comparison.
- Serving every sample frame from the checkpoint. The checkpoint id on the row is the audit trail.
- Jackknife by dropping each cow. Adjacent-swap minutes are the stability test.
- A toggle that hides one of the two ranks. Both scores stay on screen.
- Appearance overriding geometry. Contradicts the decision record.
- Any wording that says she is sick, or an order to treat her.

## Assumptions

- A change-point is the first 30-minute run where her feeding or lying residual stays beyond 1.5 robust z versus her day-1 same hour. Owner: rank module. Reversible.
- A herd meal is a minute when at least 7 of 10 cows are labeled feeding. Owner: rank module. Reversible.
- Night gate default: mean luminance under 40/255 on that hour’s samples, YOLO confidence floor 0.45 instead of 0.25. Tuned on the first real hour. Owner: detect loop.
- The sorted rank uses the visible-only score. The all-minutes score is a column, not the sort key.
- Feature 7 fires when visible fraction is under 0.4, or one clock hour holds more than half of her anomaly mass, or the pen’s visible-only scores all lie inside 0.15 of each other.

## Briefs

UI features 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 use `ui-ux-pro-max` and `less-flat-ui` together. Direction: restrained agricultural, Hallmark theme recorded in `docs/design-tokens.md` before any UI. Dense dashboard stays flat. Fraunces is not the main text.

### 1 — Evidence clip pack
Outcome: each top-3 reason links a day-1 clip and a day-2 clip that start at the cited minute, plus a jpg poster, plus a blank tile labeled not visible when that camera has no detection. Files: `src/clips.py`, `outputs/clips/`, card fields in `outputs/cards/`. Tool: ffmpeg. Budget: a 20-second clip extracts in under 5 s from a local file. Edges: missing file, minute past the end of the file, camera not in the row. Evidence: a fixture video produces two clips and one poster whose start time matches the cited minute.

### 2 — Visible-only rank and isolation
Outcome: `brd_risk.csv` gains `risk_visible`, `risk_all`, `visible_fraction`. Sort by `risk_visible`. Isolation z uses only minutes that are visible and have no neighbor. Files: `src/risk.py`. Tool: numpy, pandas. Budget: under 5 s on 28,800 rows. Edges: all minutes invisible, no neighbors ever, division by an empty herd. Evidence: a fixture where cow A is unseen for a day does not outrank cow B who actually fed less while visible.

### 3 — Herd residual and meal dropout
Outcome: z-scores are on the cow’s hourly residual after subtracting the herd profile. A skipped meal while she is visible elsewhere is a named reason with minute ranges. Files: `src/risk.py`. Tool: numpy. Budget: same 5 s scan. Edges: fewer than 7 cows ever feed together (term omitted), day 2 missing (no residual against day 1), all cows not visible in that hour. Evidence: a fixture where every cow feeds 30% less on day 2 does not fill the top ranks unless one cow drops further.

### 4 — Identity quarantine
Outcome: conflicting minutes are excluded from the anomaly vector and counted. Card reasons whose clips do not share one `cow_id` are withheld. `consistency.csv` has a leave-one-camera-out agreement column. Files: `src/identity.py`, `outputs/identity/consistency.csv`. Tool: numpy. P0 matching itself uses `scipy.optimize.linear_sum_assignment` once per handoff window. Budget: LOCO is three extra passes over tracklets, not over video. Edges: all minutes quarantined, a camera missing entirely, flat costs. Evidence: a fixture with two tracklets in incompatible zones drops those minutes from the rank and says so.

### 5 — Change-point
Outcome: rank card carries `change_minute` or blank. Files: `src/risk.py`. Tool: numpy CUSUM. Budget: one pass over her 2,880 minutes. Edges: no day 1, gap longer than 30 minutes, no window past threshold. Evidence: a fixture that drops feeding at minute 600 on day 2 marks a minute inside that window, or leaves the marker blank and keeps the day total.

### 6 — Stability tag
Outcome: column `minutes_to_swap` and tag `stable` or `fragile` or `tied`. Fragile means fewer than 15 feeding minutes would swap adjacent ranks. Files: `src/risk.py`. Tool: numpy. Edges: ties, a cow with no feeding term, a one-cow pen. Evidence: two close fixture scores produce a small minute delta; a wide gap produces `stable`.

### 7 — Insufficient evidence
Outcome: column `single_out` is yes or no, plus a reason string that never says sick or healthy as a fact. Files: `src/risk.py`. Tool: none. Edges: visible fraction exactly 0.4, one hour at exactly half the mass, scores just inside the 0.15 band. Evidence: a fixture cow with visible fraction 0.2 gets `single_out=no`.

### 8 — Coverage strip
Outcome: the dashboard header shows present, gap, and not-processed camera-hours from the inventory. Files: `dashboard/` header, `outputs/ingest/manifest.jsonl`. Tool: none. Edges: empty manifest, partial day, a camera with zero files. Evidence: a manifest with one missing hour renders a gap, not a full bar.

### 9 — Rank-1 route
Outcome: `/rank/1` opens the top card staged. Files: dashboard route. Tool: none. Edges: empty CSV, missing clips, rank tie. Evidence: a fixture CSV loads cow rank 1 without extra clicks.

### 10 — Reason audit
Outcome: each top reason is `kept`, `refused`, or `cannot tell`, with a trace path. Cap nine calls. YOLO is not loaded. Files: `src/agent.py`, `outputs/traces/`. Tool: quantized Qwen2.5-VL-3B. Budget: nine calls, one model at a time. Edges: OOM, unreadable night frame, missing clip. Evidence: a refused fixture reason is demoted and the frame path is in the trace. If the weights are not on disk yet, the column stays `not checked`.

### 11 — Provenance
Outcome: `activity.csv` has `checkpoint_id` and `light` (`day` or `night`). Night hours use confidence floor 0.45. Files: `src/detect.py`, `src/aggregate.py`, `src/config.py`. Tool: OpenCV, numpy. Budget: luminance is the mean of the hour’s already-sampled frames, no extra decode. Edges: unreadable frame, threshold too high (labels become not visible, not a guessed behavior), resumed checkpoint. Evidence: a dark fixture hour writes `light=night` and does not emit a high-confidence lying label from a low-score box.

Phase 4 is built by `orchestrate`, not by a second expansion implementer pass. Phase 5 and Phase 6 stay with orchestrate.
