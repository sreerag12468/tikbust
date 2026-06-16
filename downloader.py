"""
downloader.py — fetches a watermark-free TikTok video.
Strategy: try the tikwm.com public API first (fast, no watermark),
fall back to yt-dlp if the API fails.
"""

import re
import os
import tempfile

import requests


# ── helpers ──────────────────────────────────────────────────────────────────

def _safe_filename(name: str, fallback: str = "tiktok_video") -> str:
    name = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")
    return (name[:60] or fallback) + ".mp4"


# ── strategy 1: tikwm public API ─────────────────────────────────────────────

def _fetch_via_api(url: str) -> tuple[str, bytes]:
    """Returns (filename, video_bytes) or raises."""
    api = "https://www.tikwm.com/api/"
    resp = requests.post(api, data={"url": url, "hd": 1}, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise ValueError(f"API error: {data.get('msg', 'unknown')}")

    item = data["data"]
    # prefer HD link
    video_url = item.get("hdplay") or item.get("play")
    if not video_url:
        raise ValueError("No playable URL in API response")

    title = item.get("title", "tiktok_video")
    filename = _safe_filename(title)

    video_resp = requests.get(video_url, timeout=60, stream=True)
    video_resp.raise_for_status()
    content = video_resp.content
    if len(content) < 10_000:
        raise ValueError("Downloaded file too small — likely blocked")

    return filename, content


# ── strategy 2: yt-dlp fallback ──────────────────────────────────────────────

def _fetch_via_ytdlp(url: str) -> tuple[str, bytes]:
    """Returns (filename, video_bytes) or raises."""
    try:
        import yt_dlp
    except ImportError:
        raise RuntimeError("yt-dlp is not installed")

    with tempfile.TemporaryDirectory() as tmp:
        out_tmpl = os.path.join(tmp, "%(title).60s_%(id)s.%(ext)s")
        ydl_opts = {
            "outtmpl": out_tmpl,
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Referer": "https://www.tiktok.com/",
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = _safe_filename(info.get("title", "tiktok_video"))
            # find the written file
            raw_path = ydl.prepare_filename(info)
            mp4_path = os.path.splitext(raw_path)[0] + ".mp4"
            chosen = mp4_path if os.path.exists(mp4_path) else raw_path

        with open(chosen, "rb") as f:
            content = f.read()

    return filename, content


# ── public API ────────────────────────────────────────────────────────────────

def fetch_hd_video(url: str) -> tuple[str, bytes]:
    """
    Download a TikTok video.
    Returns (filename, video_bytes).
    Tries the tikwm API first; falls back to yt-dlp on any failure.
    """
    try:
        return _fetch_via_api(url)
    except Exception as api_err:
        print(f"[downloader] API failed ({api_err}), trying yt-dlp …")
        return _fetch_via_ytdlp(url)
