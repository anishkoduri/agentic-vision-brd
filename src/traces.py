"""Reasoning traces: Observe, Question, Verify, Revise, from real re-examined minutes.

The batch (scripts/run_batch.py) ran one loop: a coarse pass at 1 frame / 10 s, a trigger when a
box fell under 0.45 confidence, one 4 s window at 3 fps over that spot, then a second set of minute
rows. Those second rows are appended to the clip checkpoint after the coarse rows, so a repeated
(cow_id, minute) key is a coarse read followed by a re-examination read. No VLM ran.
"""

from __future__ import annotations

import json
from pathlib import Path

TRIGGER = 0.45
VLM_STATEMENT = (
    "The VLM (Qwen2.5-VL-3B) was NOT invoked: its weights were not available on this machine. "
    "Verification used the tracker's box confidence plus the 3 fps temporal re-examination instead."
)
NOT_USED = "zoom/crop, cross-camera retrieval, a look-back or look-forward outside the 4 s window"

# Manual look at the saved frames, made after the batch; the pipeline did not do this.
REVIEWER_NOTES = {
    "Event20261107013412003": (
        "Reviewer note (made after the run, not part of the pipeline): a "
        "frame at the clip start (`frames/Event20261107013412003/f0001.jpg`) and the last frame of the window "
        "(`frames/Event20261107013412003-dense-0/d0012.jpg`) show the same dark shapes in the same places in "
        "a night view, so the 'walking' label looks like a tracker artifact."
    ),
    "Event20261108085125006": (
        "Reviewer note (made after the run, not part of the pipeline): `frames/Event20261108085125006-dense-0/"
        "d0006.jpg` shows animals at the bunk rail in the lower part of the frame, which fits the feeding label."
    ),
}


def night(minute: int) -> bool:
    return minute // 60 >= 20 or minute // 60 < 6


def reexamined_pairs(checkpoints: Path, frames: Path | None = None) -> list[dict]:
    """Pairs of (coarse row, re-examination row) that share a clip-local track and minute."""
    pairs: list[dict] = []
    for path in sorted(checkpoints.glob("*.json")):
        seen: dict[tuple, dict] = {}
        for row in json.loads(path.read_text(encoding="utf-8")):
            key = (row["cow_id"], row["minute"])
            if key in seen:
                pairs.append({"stem": path.stem, "coarse": seen[key], "dense": row, "window": _window(frames, path.stem)})
            else:
                seen[key] = row
    return pairs


def _window(frames: Path | None, stem: str) -> dict:
    if frames is None:
        return {"start_s": None, "frames": None}
    dirs = sorted(frames.glob(f"{stem}-dense-*"))
    if not dirs:
        return {"start_s": None, "frames": None}
    return {"start_s": int(dirs[0].name.rsplit("-", 1)[1]), "frames": len(list(dirs[0].glob("*.jpg")))}


def pick_traces(pairs: list[dict]) -> dict[str, dict]:
    """success: label confirmed, biggest confidence gain, daytime. failure: label flipped, lowest
    confidence after the second look. night: 20:00-06:00, weak first read, flipped, most confident after."""
    def flipped(p): return p["coarse"]["behavior"] != p["dense"]["behavior"]
    def gain(p): return p["dense"]["confidence"] - p["coarse"]["confidence"]
    day = [p for p in pairs if not night(p["dense"]["minute"]) and not flipped(p)]
    dark = [p for p in pairs if night(p["dense"]["minute"]) and p["coarse"]["confidence"] < TRIGGER]
    picks = {
        "success": max(day, key=lambda p: (gain(p), p["stem"]), default=None),
        "failure": min((p for p in pairs if flipped(p)), key=lambda p: (p["dense"]["confidence"], p["stem"]), default=None),
        "night": max(dark, key=lambda p: (flipped(p), p["dense"]["confidence"], p["stem"]), default=None),
    }
    return {kind: pair for kind, pair in picks.items() if pair}


def trace_body(kind: str, pair: dict) -> dict:
    a, b = pair["coarse"], pair["dense"]
    clock = f"{b['minute'] // 60:02d}:{b['minute'] % 60:02d}"
    window = pair["window"]
    same = a["behavior"] == b["behavior"]
    start = "at 0 s, the start of the clip" if window["start_s"] == 0 else f"{window['start_s']} s into the clip"
    return {
        "kind": kind,
        "a_clip": {
            "file": f"{pair['stem']}.Avi", "camera": a["cameras"], "day": a["day"],
            "minute_of_day": a["minute"], "clock": clock, "track": f"{a['cow_id']} (clip-local, not a cow ID)",
        },
        "b_observe": {
            "label": a["behavior"], "confidence": a["confidence"],
            "source": "coarse pass: one 640x480 frame every 10 s, YOLO11-small + ByteTrack, geometric label",
        },
        "c_question": (
            f"This minute's confidence ({a['confidence']:.3f}) is under the {TRIGGER} trigger. Is '{a['behavior']}' "
            "the right label for this minute, or was the box too weak to say?"
        ),
        "d_verify": {
            "tool": "higher-FPS re-examination window (3 fps, 4 s, tracker re-run on those frames)",
            "window_start": start, "window_frames": window["frames"], "trigger": f"a box under {TRIGGER} in the coarse pass",
            "tools_not_used": NOT_USED,
        },
        "e_revise": {"label": b["behavior"], "confidence": b["confidence"], "label_changed": not same},
        "f_learned": _learned(kind, a, b, same),
        "reviewer_note": REVIEWER_NOTES.get(pair["stem"]),
        "vlm": VLM_STATEMENT,
        "caveat": (
            "The tracker is reset before each pass (`track_frames` in src/detect.py), so the window's track numbers are issued again; the second read is "
            "matched to the first by track number and minute, not by a verified identity. "
            "Both rows stay in activity.csv. Nothing here is a diagnosis."
        ),
    }


def _learned(kind: str, a: dict, b: dict, same: bool) -> str:
    gain = b["confidence"] - a["confidence"]
    if same:
        return (f"The second look kept the label and moved confidence from {a['confidence']:.3f} to "
                f"{b['confidence']:.3f} ({gain:+.3f}), so the weak first read was a detection-quality problem, not a wrong label.")
    if b["confidence"] < TRIGGER:
        return (f"The label changed ({a['behavior']} to {b['behavior']}) but confidence fell to {b['confidence']:.3f}, still "
                f"under {TRIGGER}. The re-examination did not resolve the ambiguity, so the revised label is unreliable.")
    return (f"The label changed ({a['behavior']} to {b['behavior']}) and confidence rose to {b['confidence']:.3f}. "
            "The second read is better supported, but it is a new tracker pass matched by track number only"
            + (", and at night the view is infrared with low contrast." if kind == "night" else "."))


def render_markdown(body: dict) -> str:
    c, o, v, r = body["a_clip"], body["b_observe"], body["d_verify"], body["e_revise"]
    lines = [
        f"# Trace: {body['kind']}",
        "",
        "Loop: Observe, Question, Verify, Revise.",
        "",
        f"**(a) Clip.** `{c['file']}`, camera `{c['camera']}`, Day {c['day']}, minute {c['minute_of_day']} ({c['clock']}), track {c['track']}.",
        "",
        f"**(b) Observe.** Label `{o['label']}`, confidence {o['confidence']:.3f}. Source: {o['source']}.",
        "",
        f"**(c) Question.** {body['c_question']}",
        "",
        f"**(d) Verify.** Tool: {v['tool']}, starting {v['window_start']} ({v['window_frames']} frames), "
        f"triggered by {v['trigger']}. Not used: {v['tools_not_used']}.",
        "",
        f"**(e) Revise.** Label `{r['label']}`, confidence {r['confidence']:.3f}"
        + (" (label changed)." if r["label_changed"] else " (label unchanged)."),
        "",
        f"**(f) Learned.** {body['f_learned']}",
    ]
    if body["reviewer_note"]:
        lines += ["", body["reviewer_note"]]
    lines += ["", f"**VLM.** {body['vlm']}", "", f"**Caveat.** {body['caveat']}", ""]
    return "\n".join(lines)


def write_traces(checkpoints: Path, frames: Path, dest: Path) -> dict[str, dict]:
    dest.mkdir(parents=True, exist_ok=True)
    written: dict[str, dict] = {}
    for kind, pair in pick_traces(reexamined_pairs(checkpoints, frames)).items():
        body = trace_body(kind, pair)
        (dest / f"{kind}.json").write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
        (dest / f"{kind}.md").write_text(render_markdown(body), encoding="utf-8")
        written[kind] = body
    return written
