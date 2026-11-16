# QA notes — demo video

Checked from the contact sheets and stills in `out/qa/` (not committed).

## Per-beat A/V table

| Beat | Line | What the frame shows | Supports it |
| --- | --- | --- | --- |
| hook (card) | Ten Angus cows. Two days. Three cameras. 1,749 clips. | Abstract card wall, one card picked out | Neutral: no claim on screen |
| pipeline | We built a vision pipeline that watches the pen around the clock… | Top of `docs/visualization.html`, then the herd day-over-day chart | Yes, for "what each cow is doing". The page shows behavior labels, not disease signs |
| found | Here's what it found. | Herd day-over-day comparison (lying 30.1% to 39.2%, feeding 6.1% to 5.1%) | Yes |
| drop | On day two, feeding fell sharply at midday… | Feeding share by hour, cursor on the 13 h bars | Yes for feeding. Lying is not on this chart; it is on the herd chart before and after |
| pattern | Less eating, more lying… | Herd table (lying +9.1 pp, feeding −0.9 pp) with the feeding chart below | Yes for the two shares. "A veterinarian would investigate" is the script's reading, not on screen |
| honest | We could not identify individual cows across clips… | Top anomaly tracklets table and the "clip-local, not a cow ID" note | Yes |
| arch (card) | All of it ran on a single laptop, no cloud. | Pipeline boxes with the stack labels | Yes |
| close (card) | The full evidence is in the technical brief and the repository. | Title and that sentence | Yes |

## Known mismatches left in

- The feeding chart's own note says "Not a disease signal and not tied to any cow" and that the low Day 2 midday bars partly reflect few front-camera rows. That note is on screen while the caption describes the drop.
- The tracklets page (`app/tracklets.html`) is a capture page generated from `docs/anomaly-report.md` section 2 by `scripts/make_tracklets_page.py`. `docs/visualization.html` has no tracklet view.

## Not done

- No narration (no voice provider on this machine) and no music bed. Captions carry the script.
- No mix check, because there is no audio.
- The skill's motion-graphics layer (one-world camera, kinetic type, opener concept) was not built. The cards are the template's, recoloured from the page tokens.
- The script has 8 beats, not the skill's 12–16, because the user supplied the script and asked for a short video.
