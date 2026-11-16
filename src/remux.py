"""Copy-remux a GHEC AVI to an hvc1-tagged AVI. Never re-encodes and never deletes the source."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def ffmpeg_bin() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    import static_ffmpeg

    static_ffmpeg.add_paths()
    found = shutil.which("ffmpeg")
    if not found:
        raise RuntimeError("ffmpeg is not on PATH and static-ffmpeg did not provide it")
    return found


def remux_argv(ffmpeg: str, source: Path, dest: Path) -> list[str]:
    """Stream copy. `-c:v hevc` is the input decoder hint; `-c copy` does not re-encode."""
    return [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-c:v",
        "hevc",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-c",
        "copy",
        "-tag:v",
        "hvc1",
        str(dest),
    ]


def remux_file(source: Path, dest: Path) -> None:
    """Write dest. Leaves source untouched. A failed attempt does not keep a partial file."""
    source = Path(source)
    dest = Path(dest)
    if not source.is_file():
        raise FileNotFoundError(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # The temp name has to end in .avi. ffmpeg picks the muxer from the extension.
    partial = dest.with_name(dest.stem + ".part.avi")
    try:
        subprocess.run(
            remux_argv(ffmpeg_bin(), source, partial),
            check=True,
            capture_output=True,
            timeout=300,
        )
        partial.replace(dest)
    except subprocess.CalledProcessError as exc:
        partial.unlink(missing_ok=True)
        err = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        raise RuntimeError(err[-400:] or f"ffmpeg exited {exc.returncode}") from exc
    except subprocess.TimeoutExpired as exc:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg timed out on {source.name}") from exc
    except OSError:
        partial.unlink(missing_ok=True)
        raise
