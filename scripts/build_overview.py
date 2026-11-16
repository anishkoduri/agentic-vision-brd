"""Build docs/anomaly-report.md and docs/visualization.html from the batch CSVs.

Read-only on outputs/batch; writes only under docs/. Herd- and tracklet-level
evidence only: track IDs are per-clip, so nothing here identifies an animal.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.evidence import (  # noqa: E402
    BEHAVIORS, CAMERAS, MIN_MEAN_CONF, MIN_TRACKLET_MINUTES, assessable, clip_link,
    first_minute, group_tracklets, herd_stats, top_anomalies,
)

from src.hourly import HOURS, MIN_N, hourly, section_lines, share  # noqa: E402

BATCH = ROOT / "outputs" / "batch"
DOCS = ROOT / "docs"


def day_of(clip_stem: str) -> int:
    return 1 if clip_stem.startswith("Event20261107") else 2


def load() -> dict:
    rows = list(csv.DictReader((BATCH / "activity.csv").open(encoding="utf-8")))
    budgets = [r for r in csv.DictReader((BATCH / "time_budgets.csv").open(encoding="utf-8"))
               if r["cow_id"] != "HERD_AVERAGE"]  # herd rows are means, not track-minutes
    stems = [p.stem for p in (BATCH / "checkpoints").glob("*.json")]
    clips_per_day = Counter(day_of(s) for s in stems)
    empties = (BATCH / "empty_clips.txt").read_text(encoding="utf-8").split()
    empty_per_day = Counter(day_of(Path(e).stem) for e in empties)
    return {"rows": rows, "budgets": budgets, "clips_per_day": clips_per_day,
            "empty_per_day": empty_per_day}


def herd_tables(rows: list[dict]) -> dict:
    by_day = {d: Counter() for d in (1, 2)}
    by_cam_day: dict[tuple[str, int], Counter] = defaultdict(Counter)
    for r in rows:
        d = int(r["day"])
        by_day[d][r["behavior"]] += 1
        by_cam_day[(r["cameras"], d)][r["behavior"]] += 1
    return {"by_day": by_day, "by_cam_day": by_cam_day}


def camera_budgets(budgets: list[dict]) -> dict[str, Counter]:
    tail = {"Cam 01": "front_cam_1", "Cam 02": "front_cam_2", "Cam 03": "back_cam"}
    out: dict[str, Counter] = {c: Counter() for c in CAMERAS}
    for r in budgets:
        cam = tail[r["cow_id"].split("|")[1][:6]]
        out[cam][r["behavior"]] += int(r["minutes"])
    return out


def pct(n: int, total: int) -> float:
    return 100 * n / total if total else 0.0


def write_report(data: dict, herd: dict, top: list[dict], n_tracklets: int) -> dict:
    by_day, cpd = herd["by_day"], data["clips_per_day"]
    tot = {d: sum(by_day[d].values()) for d in (1, 2)}
    lines = [
        "# Anomaly report — Pen 6, Day 1 vs Day 2",
        "",
        "> **Scope: herd-level and tracklet-level evidence only.** Tracker IDs are assigned "
        "per clip and none survives across clips, so this report does **not** identify "
        "individual cows, does **not** follow any animal from Day 1 to Day 2, and does "
        "**not** rank cows 1–10. A tracklet is one track number inside one clip.",
        "",
        "Source: `outputs/batch/activity.csv` "
        f"({sum(tot.values()):,} track-minutes) and `outputs/batch/time_budgets.csv` "
        f"(same {sum(int(r['minutes']) for r in data['budgets']):,} track-minutes, cross-checked). "
        "A *track-minute* is one tracked box in one minute; behavior labels are geometric "
        "rules on bounding boxes (observed), not a diagnosis.",
        "",
        "## 1. Herd day-over-day change",
        "",
        f"Coverage differs by day: Day 1 has {cpd[1]} clips and {tot[1]:,} track-minutes, "
        f"Day 2 has {cpd[2]} clips and {tot[2]:,}. Day 2 has more empty clips "
        f"({data['empty_per_day'][2]} vs {data['empty_per_day'][1]}), which contribute no rows. "
        "Raw counts therefore move with coverage and camera mix; the share-of-track-minutes "
        "column is the fairer comparison.",
        "",
        "| Behavior | Day 1 min | Day 2 min | Change (min) | Change (%) | Day 1 share | Day 2 share | Share change (pp) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    deltas = {}
    for b in BEHAVIORS:
        a, c = by_day[1][b], by_day[2][b]
        s1, s2 = pct(a, tot[1]), pct(c, tot[2])
        deltas[b] = (a, c, s1, s2)
        lines.append(
            f"| {b} | {a:,} | {c:,} | {c - a:+,} | {pct(c - a, a):+.1f}% | "
            f"{s1:.1f}% | {s2:.1f}% | {s2 - s1:+.1f} |"
        )
    lines += [
        f"| **total** | {tot[1]:,} | {tot[2]:,} | {tot[2] - tot[1]:+,} | "
        f"{pct(tot[2] - tot[1], tot[1]):+.1f}% | 100% | 100% | — |",
        "",
        "Camera mix check (share of track-minutes within each camera) — a herd shift "
        "that appears in only one camera is more likely a view effect than a herd effect:",
        "",
        "| Camera | Behavior | Day 1 share | Day 2 share | Share change (pp) |",
        "|---|---|---:|---:|---:|",
    ]
    for cam in CAMERAS:
        c1, c2 = herd["by_cam_day"][(cam, 1)], herd["by_cam_day"][(cam, 2)]
        t1, t2 = sum(c1.values()), sum(c2.values())
        for b in BEHAVIORS:
            s1, s2 = pct(c1[b], t1), pct(c2[b], t2)
            lines.append(f"| {cam} | {b} | {s1:.1f}% | {s2:.1f}% | {s2 - s1:+.1f} |")
    lines += [
        "",
        "## 2. Top 10 most anomalous tracklets",
        "",
        f"Method: {n_tracklets:,} tracklets with at least {MIN_TRACKLET_MINUTES} tracked "
        f"minutes and mean box confidence ≥ {MIN_MEAN_CONF}. For each behavior, a tracklet's "
        "share of its own minutes is compared with the mean share across all tracklets "
        "from the **same camera on the same day** (cameras are compared separately because "
        "the feeding band only exists in the front views). Deviation is the z-score "
        "(share − herd mean) ÷ standard deviation. Each tracklet is scored on its most "
        "extreme behavior; at most one tracklet per clip is listed.",
        "",
        "| # | Clip | Camera | Day | First minute of behavior | Track no. | Behavior | Tracklet share | Herd mean | Deviation (z) |",
        "|--:|---|---|--:|---|--:|---|---:|---:|---:|",
    ]
    for i, t in enumerate(top, 1):
        lines.append(
            f"| {i} | {clip_link(t['clip'], ROOT)} | {t['camera']} | {t['day']} | "
            f"{first_minute(t)} | {t['track']} | {t['behavior']} | "
            f"{100 * t['share']:.0f}% of {t['n']} min | {100 * t['herd_mean']:.1f}% | {t['z']:+.1f} |"
        )
    lines += [
        "",
        *section_lines(hourly(data["rows"])),
        "## 4. How to read this",
        "",
        "- Large deviations on rare behaviors (walking, feeding in the front views) are "
        "largely a small-denominator effect: a tracklet that spends most of its minutes "
        "doing something rare scores high even though one such tracklet is ordinary.",
        "- A deviation is a departure from the herd mean in the *geometric label*. It can "
        "reflect a box change (occlusion, a neighbor merging into the box, camera angle) "
        "as easily as a behavior change. Open the linked clip before reading anything into a row.",
        "- Track numbers repeat across clips (`1`, `2`, … restart in every clip), so a "
        "number in this table is **not** the same animal as the same number elsewhere.",
        "- Nothing here is a health finding. A score is not a diagnosis, and some, all, or "
        "none of the cattle may have BRD.",
        "",
        "## 5. What we could not measure",
        "",
        "Hour-level patterns are herd-level: they cannot be attributed to individual cows, because "
        "no animal is followed across clips.",
        "",
        "Regenerate: `python scripts/build_overview.py`.",
        "",
    ]
    (DOCS / "anomaly-report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"deltas": deltas, "tot": tot}


# ---------------------------------------------------------------- HTML / SVG
COLORS = {"standing": "#566770", "lying": "#8a6a3b", "feeding": "#4f7a37", "walking": "#b04a28"}
INK, MUTED = "#2b2a24", "#5c5a50"


def svg_distribution(counts: Counter) -> str:
    total, top = sum(counts.values()), max(counts.values())
    rows = []
    for i, b in enumerate(BEHAVIORS):
        y, w = 14 + i * 44, 360 * counts[b] / top
        rows.append(
            f'<text x="86" y="{y + 19}" text-anchor="end" fill="{INK}" font-size="15">{b}</text>'
            f'<rect x="96" y="{y}" width="{w:.1f}" height="28" rx="3" fill="{COLORS[b]}"/>'
            f'<text x="{96 + w + 8:.1f}" y="{y + 19}" fill="{INK}" font-size="14">'
            f"{counts[b]:,} ({pct(counts[b], total):.1f}%)</text>"
        )
    return (
        '<svg viewBox="0 0 640 190" role="img" aria-labelledby="t1 d1">'
        '<title id="t1">Behavior distribution</title>'
        f'<desc id="d1">Track-minutes by behavior: '
        + ", ".join(f"{b} {counts[b]:,}" for b in BEHAVIORS)
        + ".</desc>" + "".join(rows) + "</svg>"
    )


def svg_cameras(cam: dict[str, Counter]) -> str:
    rows = []
    for i, c in enumerate(CAMERAS):
        total, y, x = sum(cam[c].values()), 14 + i * 56, 120.0
        rows.append(f'<text x="112" y="{y + 22}" text-anchor="end" fill="{INK}" font-size="15">{c}</text>')
        for b in BEHAVIORS:
            w = 480 * cam[c][b] / total
            rows.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="32" fill="{COLORS[b]}"/>')
            if w > 44:
                rows.append(
                    f'<text x="{x + w / 2:.1f}" y="{y + 21}" text-anchor="middle" fill="#fff" '
                    f'font-size="13" font-weight="600">{pct(cam[c][b], total):.0f}%</text>'
                )
            x += w
        rows.append(f'<text x="{x + 8:.1f}" y="{y + 21}" fill="{MUTED}" font-size="12">{total:,} min</text>')
    legend = "".join(
        f'<rect x="{120 + i * 110}" y="190" width="14" height="14" rx="2" fill="{COLORS[b]}"/>'
        f'<text x="{140 + i * 110}" y="202" fill="{INK}" font-size="13">{b}</text>'
        for i, b in enumerate(BEHAVIORS)
    )
    return (
        '<svg viewBox="0 0 720 216" role="img" aria-labelledby="t2 d2">'
        '<title id="t2">Time budget by camera</title>'
        '<desc id="d2">Share of each camera\'s track-minutes by behavior.</desc>'
        + "".join(rows) + legend + "</svg>"
    )


def svg_day_over_day(deltas: dict) -> str:
    top = max(max(v[2], v[3]) for v in deltas.values())
    base, h = 230, 190
    out = [f'<line x1="50" y1="{base}" x2="620" y2="{base}" stroke="{MUTED}"/>']
    for tick in range(0, int(top) + 20, 20):
        y = base - h * tick / top
        if y < 20:
            break
        out.append(
            f'<line x1="50" y1="{y:.1f}" x2="620" y2="{y:.1f}" stroke="#d8d2c0"/>'
            f'<text x="44" y="{y + 4:.1f}" text-anchor="end" fill="{MUTED}" font-size="12">{tick}%</text>'
        )
    for i, b in enumerate(BEHAVIORS):
        gx = 80 + i * 140
        for j, (share, op) in enumerate(((deltas[b][2], 0.45), (deltas[b][3], 1.0))):
            bh, x = h * share / top, gx + j * 48
            out.append(
                f'<rect x="{x}" y="{base - bh:.1f}" width="42" height="{bh:.1f}" rx="3" '
                f'fill="{COLORS[b]}" opacity="{op}"/>'
                f'<text x="{x + 21}" y="{base - bh - 6:.1f}" text-anchor="middle" fill="{INK}" '
                f'font-size="13">{share:.1f}%</text>'
                f'<text x="{x + 21}" y="{base + 16}" text-anchor="middle" fill="{MUTED}" '
                f'font-size="12">Day {j + 1}</text>'
            )
        out.append(f'<text x="{gx + 45}" y="{base + 36}" text-anchor="middle" fill="{INK}" font-size="15">{b}</text>')
    return (
        '<svg viewBox="0 0 640 280" role="img" aria-labelledby="t3 d3">'
        '<title id="t3">Herd day-over-day comparison</title>'
        '<desc id="d3">Share of each day\'s track-minutes by behavior, Day 1 (light) vs Day 2 (solid).</desc>'
        + "".join(out) + "</svg>"
    )


def svg_feeding_by_hour(hd: dict) -> str:
    """Grouped bars, feeding share by hour. Day 2 hours under MIN_N are shaded, not drawn."""
    left, width, base, ph = 50, 570, 200, 160
    slot = width / 24
    vals = [share(hd[d][h], "feeding") or 0 for d in (1, 2) for h in HOURS if hd[d][h]["n"] >= MIN_N]
    top = max(10, -(-max(vals) // 10) * 10)
    out = []
    for tick in range(0, int(top) + 1, 10):
        y = base - ph * tick / top
        out.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="620" y2="{y:.1f}" stroke="#d8d2c0"/>'
            f'<text x="{left - 6}" y="{y + 4:.1f}" text-anchor="end" fill="{MUTED}" font-size="12">{tick}%</text>'
        )
    for h in HOURS:
        gx = left + h * slot
        if hd[2][h]["n"] < MIN_N:
            out.append(f'<rect x="{gx:.1f}" y="20" width="{slot:.1f}" height="{base - 20}" fill="#e8e1cf" opacity=".7">'
                       f'<title>{h:02d} h: Day 2 has {hd[2][h]["n"]} track-minutes (under {MIN_N}); not drawn</title></rect>')
            continue
        for j, d in enumerate((1, 2)):
            v = share(hd[d][h], "feeding") or 0
            bh, x = ph * v / top, gx + 2 + j * (slot / 2 - 1)
            out.append(
                f'<rect x="{x:.1f}" y="{base - bh:.1f}" width="{slot / 2 - 3:.1f}" height="{max(bh, 0.5):.1f}" '
                f'fill="{COLORS["feeding"]}" opacity="{0.4 if d == 1 else 1}">'
                f'<title>{h:02d} h, Day {d}: feeding {v:.1f}% of {hd[d][h]["n"]} track-minutes</title></rect>'
            )
        if h % 3 == 0:
            out.append(f'<text x="{gx + slot / 2:.1f}" y="{base + 16}" text-anchor="middle" fill="{MUTED}" font-size="12">{h:02d}</text>')
    out.append(f'<line x1="{left}" y1="{base}" x2="620" y2="{base}" stroke="{MUTED}"/>')
    out.append(
        f'<text x="{left}" y="{base + 40}" fill="{INK}" font-size="13">hour of day</text>'
        f'<rect x="300" y="{base + 28}" width="14" height="14" rx="2" fill="{COLORS["feeding"]}" opacity=".4"/>'
        f'<text x="320" y="{base + 40}" fill="{INK}" font-size="13">Day 1</text>'
        f'<rect x="380" y="{base + 28}" width="14" height="14" rx="2" fill="{COLORS["feeding"]}"/>'
        f'<text x="400" y="{base + 40}" fill="{INK}" font-size="13">Day 2</text>'
        f'<rect x="460" y="{base + 28}" width="14" height="14" rx="2" fill="#e8e1cf"/>'
        f'<text x="480" y="{base + 40}" fill="{INK}" font-size="13">Day 2 n&lt;{MIN_N}</text>'
    )
    return (
        '<svg viewBox="0 0 640 250" role="img" aria-labelledby="t4 d4">'
        '<title id="t4">Feeding share by hour</title>'
        '<desc id="d4">Share of track-minutes labeled feeding, per hour of day, Day 1 (light) vs Day 2 (solid). '
        'Hours where Day 2 has under 100 track-minutes are shaded and not drawn.</desc>'
        + "".join(out) + "</svg>"
    )


GRAIN = (
    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E"
    "%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='2'/%3E"
    "%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)' opacity='.09'/%3E%3C/svg%3E\")"
)

CSS = f"""
:root{{--ink:{INK};--muted:{MUTED};--paper:#f4f0e6;--card:#fbf8f0;--line:#d8d2c0}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper) {GRAIN};color:var(--ink);
font-family:Fraunces,Georgia,'Times New Roman',serif;line-height:1.5}}
main{{max-width:880px;margin:0 auto;padding:32px 20px 56px}}
h1{{font-size:2rem;margin:0 0 4px;letter-spacing:-.01em}}
.sub{{color:var(--muted);margin:0 0 24px}}
.card{{background:var(--card) {GRAIN};border:1px solid var(--line);border-radius:10px;
padding:20px 22px;margin:0 0 20px;box-shadow:0 1px 0 #fff inset,0 6px 16px -10px rgba(60,50,30,.35)}}
h2{{font-size:1.15rem;margin:0 0 4px}}
.note{{color:var(--muted);font-size:.9rem;margin:0 0 12px}}
svg{{width:100%;height:auto;display:block}}
table{{border-collapse:collapse;width:100%;font-size:.88rem;margin-top:12px}}
th,td{{text-align:right;padding:5px 8px;border-bottom:1px solid var(--line)}}
th:first-child,td:first-child{{text-align:left}}
.warn{{border-left:4px solid {COLORS['walking']};}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important}}}}
"""


def write_html(data: dict, herd: dict, summary: dict) -> None:
    overall = Counter()
    for c in herd["by_day"].values():
        overall.update(c)
    cam = camera_budgets(data["budgets"])
    deltas, tot = summary["deltas"], summary["tot"]
    dod_rows = "".join(
        f"<tr><td>{b}</td><td>{a:,}</td><td>{c:,}</td><td>{c - a:+,}</td>"
        f"<td>{s1:.1f}%</td><td>{s2:.1f}%</td><td>{s2 - s1:+.1f}</td></tr>"
        for b, (a, c, s1, s2) in deltas.items()
    )
    cam_rows = "".join(
        f"<tr><td>{c}</td>" + "".join(f"<td>{cam[c][b]:,}</td>" for b in BEHAVIORS)
        + f"<td>{sum(cam[c].values()):,}</td></tr>"
        for c in CAMERAS
    )
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pen 6 — Behavioral Overview</title><style>{CSS}</style></head>
<body><main>
<h1>Pen 6 — Behavioral Overview</h1>
<p class="sub">{sum(overall.values()):,} track-minutes from {sum(data['clips_per_day'].values()):,} clips
(Day 1: {data['clips_per_day'][1]} clips, Day 2: {data['clips_per_day'][2]}). Unit: one tracked box in one minute.</p>

<section class="card warn"><h2>What this page is — and is not</h2>
<p class="note" style="margin:0">Herd-level evidence only. Tracker IDs are per clip and never carry across
clips, so no animal is followed between days, no individual is identified, and nothing here ranks cows or
diagnoses disease. Labels are geometric rules on bounding boxes.</p></section>

<section class="card"><h2>Behavior distribution</h2>
<p class="note">Track-minutes by behavior, both days combined.</p>{svg_distribution(overall)}</section>

<section class="card"><h2>Time budgets by camera</h2>
<p class="note">Share of each camera's track-minutes (from time_budgets.csv). The back camera sees the
whole pen; front cameras see the bunk, so feeding is only observable there.</p>{svg_cameras(cam)}
<table><tr><th>Camera</th>{''.join(f'<th>{b}</th>' for b in BEHAVIORS)}<th>total</th></tr>{cam_rows}</table></section>

<section class="card"><h2>Herd day-over-day comparison</h2>
<p class="note">Share of each day's track-minutes (Day 1 light, Day 2 solid). Shares are used because
coverage differs: Day 1 {tot[1]:,} vs Day 2 {tot[2]:,} track-minutes.</p>{svg_day_over_day(deltas)}
<table><tr><th>Behavior</th><th>Day 1 min</th><th>Day 2 min</th><th>Change</th><th>Day 1 share</th>
<th>Day 2 share</th><th>Change (pp)</th></tr>{dod_rows}</table></section>

<section class="card"><h2>Feeding share by hour</h2>
<p class="note">Share of each hour's track-minutes labeled feeding. Descriptive only: feeding is labeled on the
front cameras only, so Day 2's low midday bars partly reflect few front-camera rows then (see the
anomaly report). Not a disease signal and not tied to any cow.</p>{svg_feeding_by_hour(hourly(data["rows"]))}</section>
</main></body></html>
"""
    (DOCS / "visualization.html").write_text(page, encoding="utf-8")


def main() -> None:
    data = load()
    herd = herd_tables(data["rows"])
    tl = group_tracklets(data["rows"])
    stats = herd_stats(tl)
    top = top_anomalies(tl, stats, 10)
    summary = write_report(data, herd, top, sum(assessable(t) for t in tl))
    write_html(data, herd, summary)
    print(json.dumps({
        "rows": len(data["rows"]), "clips_per_day": dict(data["clips_per_day"]),
        "deltas": summary["deltas"], "tracklets": len(tl),
        "top": [(Path(t["clip"]).name, t["camera"], t["day"], t["track"], t["behavior"],
                 round(t["share"], 2), round(t["herd_mean"], 3), round(t["z"], 1)) for t in top],
    }, indent=1))


if __name__ == "__main__":
    main()
