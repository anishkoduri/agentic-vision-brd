"""Overlay a recorded voiceover on out/demo.mp4 without re-synthesising anything.

The recording is cut only at its own pauses, and each phrase is placed at the caption cue it belongs to
(cue times come from the same timeline the video was rendered from). The video stream is copied.
A local speech-to-text pass (faster-whisper, CPU) maps phrases to cues and then checks the result.

    python scripts/voiceover.py "<voiceover.mp3>"
"""
from __future__ import annotations

import difflib
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
RATE = 44100
FIRST_START = 0.2   # the first line is longer than its beat, so it starts just before its caption
MIN_PAUSE = 0.2     # floor for a pause when a phrase is running behind its cue
PAD = 0.06          # silence kept on each side of a cut
FADE = 0.008


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, capture_output=True)


def decode(path: Path, rate: int = RATE) -> np.ndarray:
    raw = run("ffmpeg", "-v", "error", "-i", str(path), "-vn", "-f", "s16le", "-ac", "1", "-ar", str(rate), "-").stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def speech_segments(path: Path, total: float) -> list[tuple[float, float]]:
    log = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=noise=-35dB:d=0.18", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)]
    segments, cursor = [], 0.0
    for start, end in zip(starts, ends + [total] * (len(starts) - len(ends))):
        if start - cursor > 0.05:
            segments.append((cursor, start))
        cursor = end
    if total - cursor > 0.05:
        segments.append((cursor, total))
    return segments


def norm(word: str) -> str:
    return re.sub(r"[^a-z0-9]", "", word.lower())


def transcribe(model, path: Path) -> list[tuple[str, float, float]]:
    # Whisper wants 16 kHz samples; decoding here avoids its own file reader.
    segments, _ = model.transcribe(decode(path, 16000), language="en", word_timestamps=True, vad_filter=False)
    return [(w.word.strip(), w.start, w.end) for s in segments for w in s.words]


def cue_of_words(cues: list[dict], heard: list[tuple[str, float, float]]) -> list[int | None]:
    """For every heard word, the index of the caption cue it belongs to (None when it has no match)."""
    script = [(norm(w), i) for i, cue in enumerate(cues) for w in cue["text"].split() if norm(w)]
    matcher = difflib.SequenceMatcher(a=[norm(w) for w, _, _ in heard], b=[w for w, _ in script], autojunk=False)
    owner: list[int | None] = [None] * len(heard)
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            owner[block.a + k] = script[block.b + k][1]
    return owner


def main() -> int:
    source = Path(sys.argv[1])
    timeline = json.loads((HERE / "capture" / "learn" / "timeline.json").read_text(encoding="utf-8-sig"))
    shots = json.loads((HERE / "shots.json").read_text(encoding="utf-8"))["shots"]
    close = next(s for s in timeline["scenes"] if s["id"] == "close")
    # The close line has no caption (it is the sentence on the card), so its cue is the card itself.
    cues = timeline["captions"] + [{"text": next(s["say"] for s in shots if s["id"] == "close"),
                                    "from": close["start"] + 0.2, "to": close["start"] + close["dur"]}]
    total = float(timeline["total"])

    from faster_whisper import WhisperModel
    model = WhisperModel("base.en", device="cpu", compute_type="int8")

    audio = decode(source)
    spans = speech_segments(source, len(audio) / RATE)
    heard = transcribe(model, source)
    owner = cue_of_words(cues, heard)

    # Phrases: one per stretch of speech between pauses, with the cue its first matched word belongs to.
    phrases = []
    for a, b in spans:
        idx = [i for i, (_, ws, we) in enumerate(heard) if a - 0.1 <= (ws + we) / 2 <= b + 0.1]
        phrases.append({"a": a, "b": b, "cue": next((owner[i] for i in idx if owner[i] is not None), None),
                        "text": " ".join(heard[i][0] for i in idx),
                        "words": [(owner[i], heard[i][1] - a) for i in idx if owner[i] is not None]})
    scene_of = lambda cue: next(i for i, sc in enumerate(timeline["scenes"]) if cues[cue]["from"] < sc["start"] + sc["dur"])

    def lay_out(scale: dict[int, float]) -> None:
        prev_end, prev_b, seen, scene = None, None, set(), 0
        for ph in phrases:
            scene = scene_of(ph["cue"]) if ph["cue"] is not None else scene
            pause = (ph["a"] - prev_b) * scale.get(scene, 1.0) if prev_b is not None else 0.0
            if prev_end is None:
                start = FIRST_START
            elif ph["cue"] is not None and ph["cue"] not in seen:
                start = max(cues[ph["cue"]]["from"], prev_end + min(pause, MIN_PAUSE))
            else:
                start = prev_end + pause
            seen.add(ph["cue"])
            ph.update(at=start, end=start + ph["b"] - ph["a"], scene=scene)
            prev_end, prev_b = ph["end"], ph["b"]

    # Where a beat's narration would run past its last caption, shorten that beat's own pauses (never the speech).
    scale: dict[int, float] = {}
    for _ in range(6):
        lay_out(scale)
        late = {ph["scene"] for ph in phrases
                if ph["end"] > max(c["to"] for c in cues if scene_of(cues.index(c)) == ph["scene"])}
        late = {sc for sc in late if scale.get(sc, 1.0) > 0.55}
        if not late:
            break
        for sc in late:
            scale[sc] = round(scale.get(sc, 1.0) - 0.1, 2)

    track = np.zeros(int(round(total * RATE)), dtype=np.float32)
    for ph in phrases:
        lo, hi = max(0, int((ph["a"] - PAD) * RATE)), min(len(audio), int((ph["b"] + PAD) * RATE))
        clip = audio[lo:hi].copy()
        ramp = int(FADE * RATE)
        clip[:ramp] *= np.linspace(0, 1, ramp)
        clip[-ramp:] *= np.linspace(1, 0, ramp)
        at = int((ph["at"] - PAD) * RATE)
        if at + len(clip) > len(track):
            raise SystemExit(f"phrase {ph['text']!r} would run past the end of the video")
        track[at:at + len(clip)] += clip

    out = HERE / "out"
    wav = out / "voiceover-aligned.wav"
    with wave.open(str(wav), "wb") as fh:
        fh.setnchannels(1); fh.setsampwidth(2); fh.setframerate(RATE)
        fh.writeframes((np.clip(track, -1, 1) * 32767).astype(np.int16).tobytes())
    voiced = out / "demo-voiced.mp4"
    run("ffmpeg", "-y", "-v", "error", "-i", str(out / "demo.mp4"), "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(voiced))

    print(f"pause scale per beat (1.0 = untouched): {scale or 'all 1.0'}")
    print("PLACEMENT (source seconds -> video seconds)")
    for ph in phrases:
        print(f"  {ph['a']:6.2f}-{ph['b']:6.2f} -> {ph['at']:6.2f}-{ph['end']:6.2f}  cue {ph['cue']}  {ph['text']}")

    # Check the finished file, not the plan. Speech onsets are measured from its audio; the words are
    # confirmed by transcribing it. Mid-phrase cue times are estimates from the word timings.
    measured = [(x, y) for x, y in speech_segments(voiced, total)]
    final = transcribe(model, voiced)
    said = [norm(w) for w, _, _ in final if norm(w)]
    orig = [norm(w) for w, _, _ in heard if norm(w)]
    print(f"\nwords in finished file match the recording, in order: {said == orig} ({len(said)} words)")
    print("SYNC CHECK (first word of each caption, in demo-voiced.mp4)")
    worst = 0.0
    for i, cue in enumerate(cues):
        hit = next(((ph, off) for ph in phrases for owner_i, off in ph["words"] if owner_i == i), None)
        if hit is None:
            print(f"  cue {i:2d} NO MATCHED WORD  {cue['text']}")
            continue
        ph, off = hit
        exact = ph["cue"] == i and off == ph["words"][0][1]
        t = ph["at"] if exact else ph["at"] + off
        onset = min(measured, key=lambda m: abs(m[0] - ph["at"]))[0]
        last = max(p2["at"] + o for p2 in phrases for oi, o in p2["words"] if oi == i)
        worst = max(worst, abs(t - cue["from"]))
        print(f"  cue {i:2d} caption {cue['from']:5.2f}-{cue['to']:5.2f}  spoken from {t:5.2f}{' ' if exact else '~'} "
              f"({t - cue['from']:+.2f}s)  last word starts {last:5.2f}  phrase onset measured {onset:5.2f}  {cue['text']}")
    drift = max(abs(min(measured, key=lambda m: abs(m[0] - ph["at"]))[0] - ph["at"]) for ph in phrases)
    print(f"\nworst caption offset: {worst:.2f}s   measured onset vs planned, worst: {drift:.2f}s   peak: {float(np.abs(track).max()):.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
