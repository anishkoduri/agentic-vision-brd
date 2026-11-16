"""Capture-only page for the demo video: renders the existing 'Top 10 most anomalous tracklets'
table from docs/anomaly-report.md. No number is typed here; every cell is read from the report."""
import html, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
report = (ROOT / "docs" / "anomaly-report.md").read_text(encoding="utf-8")
section = report.split("## 2. Top 10 most anomalous tracklets", 1)[1].split("\n## ", 1)[0]
rows = [[c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        for line in section.splitlines() if line.startswith("|") and not line.startswith("|--")]
head, body = rows[0], rows[1:]
assert len(body) == 10, len(body)
viz = (ROOT / "docs" / "visualization.html").read_text(encoding="utf-8")
css = re.search(r"<style>(.*?)</style>", viz, re.S).group(1)
tr = lambda cells, tag: "<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>"
page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Pen 6 — Anomaly tracklets</title><style>{css}
main{{max-width:1180px}} table{{font-size:1rem}} th,td{{text-align:left;padding:9px 10px}}</style></head><body><main>
<h1>Pen 6 — Top anomaly tracklets</h1>
<p class="sub">From docs/anomaly-report.md, section 2. Each row is one tracker number inside one clip.</p>
<section class="card warn"><h2>Clip-level evidence only</h2>
<p class="note" style="margin:0">A track number is clip-local, not a cow ID. Tracklets are not linked across clips or days,
no individual cow is identified or ordered, and a deviation is not a diagnosis.</p></section>
<section class="card"><h2>Tracklets that deviate most from the herd mean for their camera and day</h2>
<table id="tracklets">{tr(head, "th")}{"".join(tr(r, "td") for r in body)}</table></section>
</main></body></html>"""
(ROOT / "challenge2-video" / "app" / "tracklets.html").write_text(page, encoding="utf-8")
print("rows", len(body))
