"""Print docs/technical-brief.md to PDF in headless Edge at 11pt and 12pt and count pages.

The brief has headings, paragraphs, inline code and no tables or lists, so a tiny converter is enough.
Letter paper, 0.75 in margins. Exit code 1 if either size is over 2 pages.
"""

from __future__ import annotations

import html
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "technical-brief.md"
EDGE = Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
MAX_PAGES = 2
SIZES = (11, 12)
CSS = """@page {{ size: Letter; margin: 0.75in; }}
body {{ font-family: "Segoe UI", Arial, sans-serif; font-size: {pt}pt; line-height: 1.3; margin: 0; }}
h1 {{ font-size: 1.6em; margin: 0 0 .4em; }} h2 {{ font-size: 1.25em; margin: .9em 0 .3em; }}
p {{ margin: 0 0 .6em; }} code {{ font-family: Consolas, monospace; font-size: .9em; }}"""


def to_html(markdown: str, pt: int) -> str:
    body = []
    for block in re.split(r"\n\s*\n", markdown.strip()):
        text = html.escape(block.strip(), quote=False)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
        heading = re.match(r"(#{1,2}) (.*)", text)
        body.append(f"<h{len(heading.group(1))}>{heading.group(2)}</h{len(heading.group(1))}>" if heading else f"<p>{text}</p>")
    return f"<!doctype html><meta charset=utf-8><style>{CSS.format(pt=pt)}</style>" + "\n".join(body)


def pages(pdf: Path) -> int:
    return len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", pdf.read_bytes()))


def render(markdown: str, pt: int, work: Path) -> int:
    page = work / f"brief-{pt}.html"
    pdf = work / f"brief-{pt}.pdf"
    page.write_text(to_html(markdown, pt), encoding="utf-8")
    subprocess.run(
        [str(EDGE), "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", page.as_uri()],
        check=True, capture_output=True, timeout=120,
    )
    return pages(pdf)


def main() -> int:
    markdown = BRIEF.read_text(encoding="utf-8")
    print(f"words={len(markdown.split())}")
    over = False
    with tempfile.TemporaryDirectory() as tmp:
        for pt in SIZES:
            count = render(markdown, pt, Path(tmp))
            print(f"{pt}pt pages={count}")
            over |= count > MAX_PAGES
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
