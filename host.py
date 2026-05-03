#!/usr/bin/env python3
"""Native messaging host for X image saver.

Reads JSON over stdin (4-byte length prefix), downloads image,
writes EXIF UserComment with source tweet URL, imports to Photos.app.
"""
import sys
import json
import struct
import urllib.request
import subprocess
import tempfile
import os
import re
from pathlib import Path


def read_message():
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) == 0:
        sys.exit(0)
    length = struct.unpack("@I", raw_length)[0]
    return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))


def send_message(obj):
    encoded = json.dumps(obj).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("@I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def upgrade_x_url(url: str) -> list[str]:
    """Return candidate URLs ordered best-to-worst quality."""
    if "pbs.twimg.com" in url:
        base = re.sub(r"[?&]name=\w+", "", url)
        base = re.sub(r"[?&]format=\w+", "", base)
        base = base.rstrip("?&")
        sep = "&" if "?" in base else "?"
        return [
            f"{base}{sep}format=png&name=orig",
            f"{base}{sep}format=jpg&name=orig",
            url,
        ]
    if "xhscdn.com" in url or "xiaohongshu.com" in url:
        return upgrade_xhs_url(url)
    return [url]


def upgrade_xhs_url(url: str) -> list[str]:
    """Strip XHS CDN transform suffix to remove watermark + get full quality.

    Patterns observed:
      https://sns-webpic-qc.xhscdn.com/<date>/<hash>/<trace>!nd_dft_wlteh_webp_3
      https://sns-img-bd.xhscdn.com/<trace>?...
      https://ci.xiaohongshu.com/<trace>
    The "!..." suffix is the imageMogr/CDN transform tag — anything after `!`
    triggers watermark/format/scale. Stripping it returns the original upload.
    """
    candidates = []
    # Strip query string
    clean = url.split("?")[0]
    # Strip "!suffix" transform tag — this is what carries watermark
    no_bang = clean.split("!")[0]
    candidates.append(no_bang)

    # Try the dedicated original-image host with the same trace ID
    m = re.search(r"/([0-9a-f]{20,})(?:[/!?]|$)", no_bang)
    trace = m.group(1) if m else None
    if trace:
        candidates.append(f"https://ci.xiaohongshu.com/{trace}")
        candidates.append(f"https://sns-img-bd.xhscdn.com/{trace}")
        candidates.append(f"https://sns-img-hw.xhscdn.com/{trace}")

    # Original URL last, just in case
    if url not in candidates:
        candidates.append(url)
    return candidates


def guess_ext(url: str) -> str:
    m = re.search(r"format=(\w+)", url)
    if m:
        return f".{m.group(1)}"
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        if ext in url.lower():
            return ".jpg" if ext == ".jpeg" else ext
    return ".jpg"


def sniff_format(data: bytes) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"\x00\x00\x00 " or data[4:8] == b"ftyp":
        return "mp4"
    return "bin"


def referer_for(url: str) -> str:
    if "xhscdn.com" in url or "xiaohongshu.com" in url:
        return "https://www.xiaohongshu.com/"
    if "twimg.com" in url:
        return "https://x.com/"
    return ""


def fetch(url: str) -> tuple[bytes, str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "image/png,image/jpeg,image/webp,image/*,*/*;q=0.8",
    }
    ref = referer_for(url)
    if ref:
        headers["Referer"] = ref
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(), r.headers.get("Content-Type", "")


def download(candidates: list[str]) -> tuple[Path, str, str]:
    """Try candidates, prefer PNG byte-result. Return (path, used_url, real_fmt)."""
    last_err = None
    fallback = None  # (data, url, fmt) — first success even if not PNG
    for url in candidates:
        try:
            data, ctype = fetch(url)
            fmt = sniff_format(data)
            if fmt == "png":
                path = _persist(data, fmt)
                return path, url, fmt
            if fallback is None:
                fallback = (data, url, fmt)
        except Exception as e:
            last_err = e
            continue
    if fallback:
        data, url, fmt = fallback
        return _persist(data, fmt), url, fmt
    raise last_err if last_err else RuntimeError("no candidates")


def _persist(data: bytes, fmt: str) -> Path:
    ext = ".jpg" if fmt == "jpg" else f".{fmt}"
    fd, path = tempfile.mkstemp(suffix=ext, prefix="xphoto_")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(data)
    return Path(path)


def write_exif(path: Path, tweet_url: str):
    """Write tweet URL into EXIF UserComment via exiftool if available, else skip."""
    if not tweet_url:
        return
    exiftool = subprocess.run(["which", "exiftool"], capture_output=True, text=True)
    if exiftool.returncode != 0:
        return
    subprocess.run(
        [
            "exiftool",
            "-overwrite_original",
            f"-UserComment={tweet_url}",
            f"-XPComment={tweet_url}",
            f"-ImageDescription=Source: {tweet_url}",
            str(path),
        ],
        capture_output=True,
    )


def import_to_photos(path: Path) -> bool:
    script = f'''
    tell application "Photos"
        activate
        delay 0.3
        import POSIX file "{path}" skip check duplicates false
    end tell
    '''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return r.returncode == 0


def main():
    msg = read_message()
    src_url = msg.get("srcUrl", "")
    tweet_url = msg.get("pageUrl", "")

    if not src_url:
        send_message({"ok": False, "error": "no srcUrl"})
        return

    try:
        candidates = upgrade_x_url(src_url)
        path, used, fmt = download(candidates)
        write_exif(path, tweet_url)
        ok = import_to_photos(path)
        size = path.stat().st_size
        try:
            os.unlink(path)
        except OSError:
            pass
        send_message({"ok": ok, "url": used, "format": fmt, "bytes": size, "tweet": tweet_url})
    except Exception as e:
        send_message({"ok": False, "error": str(e)})


if __name__ == "__main__":
    main()
