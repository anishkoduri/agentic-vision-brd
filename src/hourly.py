"""Behavior by hour of day, Day 1 vs Day 2, from activity rows only.

Herd-level numbers: a row is one tracked box in one minute, so nothing here
follows an animal. Hours with no rows (including empty clips) simply have n = 0.
"""

from __future__ import annotations

from collections import Counter

MIN_N = 100  # Day 2 hours below this many track-minutes are flagged noisy
HOURS = range(24)
DAYS = (1, 2)


def hourly(rows: list[dict]) -> dict[int, dict[int, dict]]:
    """{day: {hour: {"n", "front", "front_feeding", "counts"}}}; `front` counts non-back-camera rows."""
    out = {d: {h: {"n": 0, "front": 0, "front_feeding": 0, "counts": Counter()} for h in HOURS} for d in DAYS}
    for r in rows:
        cell = out[int(r["day"])][int(r["minute"]) // 60]
        cell["n"] += 1
        cell["counts"][r["behavior"]] += 1
        if r["cameras"] != "back_cam":
            cell["front"] += 1
            cell["front_feeding"] += r["behavior"] == "feeding"
    return out


def share(cell: dict, behavior: str) -> float | None:
    return 100 * cell["counts"][behavior] / cell["n"] if cell["n"] else None


def comparable(data: dict, hour: int) -> bool:
    return all(data[d][hour]["n"] >= MIN_N for d in DAYS)


def delta(data: dict, hour: int, behavior: str) -> float | None:
    a, b = share(data[1][hour], behavior), share(data[2][hour], behavior)
    return None if a is None or b is None else b - a


def _fmt(x: float | None) -> str:
    return "—" if x is None else f"{x:.1f}%"


def _spans(hours: list[int]) -> str:
    """[12, 13, 14, 16] -> '12–14 h, 16 h'."""
    if not hours:
        return "none"
    runs, start, prev = [], hours[0], hours[0]
    for h in hours[1:] + [None]:
        if h is not None and h == prev + 1:
            prev = h
            continue
        runs.append(f"{start:02d} h" if start == prev else f"{start:02d}–{prev:02d} h")
        start = prev = h
    return ", ".join(runs)


def _change(data: dict, hour: int, behavior: str) -> str:
    a, b = share(data[1][hour], behavior), share(data[2][hour], behavior)
    return f"{hour:02d} h: {a:.1f}% → {b:.1f}% ({b - a:+.1f} pp)"


def table_lines(data: dict) -> list[str]:
    lines = [
        "| Hour | Day 1 track-min | Day 2 track-min | Feeding D1 | Feeding D2 | Feeding Δ (pp) "
        "| Lying D1 | Lying D2 | Lying Δ (pp) | Note |",
        "|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|",
    ]
    for h in HOURS:
        ok = comparable(data, h)
        dfeed, dlie = delta(data, h, "feeding"), delta(data, h, "lying")
        note = "" if ok else f"⚠ n<{MIN_N}: noisy, no conclusion"
        lines.append(
            f"| {h:02d} | {data[1][h]['n']:,} | {data[2][h]['n']:,} "
            f"| {_fmt(share(data[1][h], 'feeding'))} | {_fmt(share(data[2][h], 'feeding'))} "
            f"| {f'{dfeed:+.1f}' if ok and dfeed is not None else '—'} "
            f"| {_fmt(share(data[1][h], 'lying'))} | {_fmt(share(data[2][h], 'lying'))} "
            f"| {f'{dlie:+.1f}' if ok and dlie is not None else '—'} | {note} |"
        )
    return lines


def _day_share(data: dict, day: int, behavior: str) -> float:
    n = sum(data[day][h]["n"] for h in HOURS)
    return 100 * sum(data[day][h]["counts"][behavior] for h in HOURS) / n


def feeding_callout(data: dict, comp: list[int]) -> list[str]:
    changes = {h: delta(data, h, "feeding") for h in comp}
    top = sorted(comp, key=lambda h: -abs(changes[h]))[:3]
    drops = [h for h in comp if changes[h] < -1]
    rises = [h for h in comp if changes[h] > 1]
    worst = sorted(drops, key=lambda h: changes[h])[:2]
    total_drop = sum(-changes[h] for h in drops)
    top_share = 100 * sum(-changes[h] for h in worst) / total_drop if total_drop else 0
    concentrated = top_share >= 60
    net = _day_share(data, 2, "feeding") - _day_share(data, 1, "feeding")
    out = [
        "**(1) Feeding share.** Largest Day 1 → Day 2 changes: "
        + "; ".join(_change(data, h, "feeding") for h in top) + ".",
        "",
        f"Feeding share fell by more than 1 pp in {len(drops)} of {len(comp)} comparable hours "
        f"({_spans(drops)}) and rose by more than 1 pp in {len(rises)} ({_spans(rises)}). "
        + (
            f"The drop is **concentrated**: {_spans(sorted(worst))} hold {top_share:.0f}% of the summed "
            f"percentage-point decreases, the other hours with a drop are small, and {len(rises)} hours move "
            f"the other way, so the whole-day change of {net:+.1f} pp is the net of a concentrated decrease "
            "and offsetting increases."
            if concentrated else
            f"The drop is **spread** over several hours: the two largest ({_spans(sorted(worst))}) hold only "
            f"{top_share:.0f}% of the summed decreases."
        ),
        "",
    ]
    for h in worst:
        a, b = data[1][h], data[2][h]
        fa, fb = (100 * c["front_feeding"] / c["front"] if c["front"] else None for c in (a, b))
        within = (
            f" Within front-camera rows alone, feeding went from {fa:.1f}% to {fb:.1f}% at {h:02d} h, so "
            "the drop is not only a coverage effect."
            if fa is not None and b["front"] >= MIN_N else
            f" The Day 2 front-camera sample at {h:02d} h ({b['front']} track-minutes) is too small to say "
            "what share of those cows were feeding."
        )
        out.append(
            f"Coverage caveat at {h:02d} h: feeding is only labeled on the front cameras, and front-camera "
            f"track-minutes went from {a['front']:,} (Day 1) to {b['front']:,} (Day 2) while all-camera "
            f"track-minutes were {a['n']:,} and {b['n']:,}. Part of that drop reflects fewer cows in the "
            "front views, and these files cannot separate fewer cows feeding from fewer cows in view."
            + within
        )
        out.append("")
    return out


def lying_callout(data: dict, comp: list[int]) -> list[str]:
    changes = {h: delta(data, h, "lying") for h in comp}
    up = [h for h in comp if changes[h] > 0]
    down = [h for h in comp if changes[h] < 0]
    mirrored = sum(1 for h in up if (delta(data, h, "standing") or 0) < 0)
    big_up = sorted(comp, key=lambda h: -changes[h])[:3]
    big_down = sorted(comp, key=lambda h: changes[h])[:2]
    broad = len(up) / len(comp) >= 0.85
    return [
        f"**(2) Standing-to-lying shift.** Lying share rose in {len(up)} of {len(comp)} comparable hours "
        f"and fell in {len(down)} ({_spans(down)}). In {mirrored} of the {len(up)} hours where lying rose, "
        "standing share fell. Largest rises: " + "; ".join(_change(data, h, "lying") for h in big_up)
        + ". Largest falls: " + "; ".join(_change(data, h, "lying") for h in big_down) + ". "
        + (
            "The shift is spread across the day."
            if broad else
            "The shift is **broad but uneven, not concentrated in one window**: most hours go the same "
            "way, but large opposite-sign hours exist and the biggest swings are in a few hours rather "
            "than a single block."
        ),
        "",
    ]


def noise_callout(data: dict) -> list[str]:
    flagged = [h for h in HOURS if data[2][h]["n"] < MIN_N]
    detail = ", ".join(f"{h:02d} h (n={data[2][h]['n']})" for h in flagged)
    return [
        f"**(3) Small samples.** Day 2 has fewer than {MIN_N} track-minutes in: {detail}. These hours are "
        "flagged in the table, their changes are not computed, and no conclusion is drawn from them. "
        "Where Day 1 and Day 2 have a few hundred track-minutes, shares can still swing both ways, because "
        "track-minutes from the same tracklet are correlated and the effective sample is smaller than the count.",
        "",
    ]


def section_lines(data: dict) -> list[str]:
    comp = [h for h in HOURS if comparable(data, h)]
    return [
        "## 3. Behavior by hour",
        "",
        "From `activity.csv` only (hour = minute of day ÷ 60; observed rows only; empty clips have no rows, so "
        "an hour with few rows may also be an hour with many empty clips). Shares are of that hour's "
        "track-minutes on that day. Feeding can only be labeled on the front cameras, so all-camera feeding "
        "share also moves with how many front-camera rows exist.",
        "",
        *table_lines(data),
        "",
        *feeding_callout(data, comp),
        *lying_callout(data, comp),
        *noise_callout(data),
        "**Reading the pattern.** These are the hours where the herd-level behavior changed most; a "
        "veterinarian would look at these windows first. They are not a BRD signal, they are not tied to any "
        "cow, and no hour-level change here says anything about disease. The by-hour pattern is mixed rather "
        "than clean (see callouts 1 and 2), so treat it as descriptive.",
        "",
    ]
