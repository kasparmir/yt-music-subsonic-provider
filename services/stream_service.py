"""
services/stream_service.py — resolve & serve audio from YouTube Music.

Two streaming modes (controlled by config STREAM.proxy):
  proxy=False  → return the raw CDN URL to the caller, who does a 302 redirect
  proxy=True   → pipe the audio through this Flask process (supports Range, avoids CORS)

When STREAM.ffmpeg_transcode=True the audio is re-encoded to mp3 via ffmpeg
before being piped to the client.  ffmpeg must be on PATH.
"""
import logging
import subprocess
import threading
import time
from typing import Optional, Tuple, Generator

import requests
import yt_dlp
from flask import Response, stream_with_context, request

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# URL resolver + cache
# ─────────────────────────────────────────────────────────────────────────────

class _StreamCache:
    """Thread-safe TTL cache for resolved stream URLs."""

    def __init__(self):
        self._store: dict[str, Tuple[str, float]] = {}
        self._lock  = threading.Lock()

    def get(self, key: str, ttl: int) -> Optional[str]:
        with self._lock:
            entry = self._store.get(key)
            if entry and (time.time() - entry[1]) < ttl:
                return entry[0]
        return None

    def set(self, key: str, url: str):
        with self._lock:
            self._store[key] = (url, time.time())

    def invalidate(self, key: str):
        with self._lock:
            self._store.pop(key, None)


_cache = _StreamCache()

_YDL_OPTS = {
    "format":           "bestaudio/best",
    "quiet":            True,
    "no_warnings":      True,
    "extract_flat":     False,
    "nocheckcertificate": True,
    "socket_timeout":   15,
}


def resolve_url(video_id: str, cache_ttl: int = 3600) -> Optional[str]:
    """
    Return the best-audio CDN URL for *video_id*.
    Result is cached for *cache_ttl* seconds.
    """
    cached = _cache.get(video_id, cache_ttl)
    if cached:
        log.debug("resolve_url cache HIT for %s", video_id)
        return cached

    yt_url = f"https://music.youtube.com/watch?v={video_id}"
    log.info("resolve_url: extracting stream for %s", video_id)

    try:
        with yt_dlp.YoutubeDL(_YDL_OPTS) as ydl:
            info = ydl.extract_info(yt_url, download=False)

        url = _pick_best_audio(info)
        if url:
            _cache.set(video_id, url)
            log.info("resolve_url: OK for %s (len=%d)", video_id, len(url))
        else:
            log.warning("resolve_url: no suitable audio format for %s", video_id)
        return url

    except Exception as exc:
        log.error("resolve_url(%s): %s", video_id, exc)
        return None


def _pick_best_audio(info: dict) -> Optional[str]:
    """Select the best audio-only format from a yt-dlp info dict."""
    formats = info.get("formats", [])
    # audio-only streams
    audio = [
        f for f in formats
        if f.get("acodec") != "none" and f.get("vcodec") in ("none", None, "")
    ]
    if audio:
        # prefer m4a, then highest bitrate
        audio.sort(
            key=lambda f: (f.get("abr") or 0, 1 if f.get("ext") == "m4a" else 0),
            reverse=True,
        )
        url = audio[0].get("url")
        if url:
            log.debug("_pick_best_audio: %s %s %s abr=%s",
                      audio[0].get("format_id"), audio[0].get("ext"),
                      audio[0].get("acodec"), audio[0].get("abr"))
            return url

    # fallback to top-level url
    return info.get("url")


# ─────────────────────────────────────────────────────────────────────────────
# Flask response builders
# ─────────────────────────────────────────────────────────────────────────────

def build_stream_response(video_id: str, stream_cfg: dict) -> Response:
    """
    Return a Flask Response that streams audio for *video_id*.

    stream_cfg keys:
      cache_ttl        int   seconds
      proxy            bool  pipe through this server vs 302 redirect
      ffmpeg_transcode bool  re-encode via ffmpeg
      ffmpeg_bitrate   str   e.g. "192k"
      prefetch_ahead   int   how many upcoming tracks to warm (default 2)
      prefetch_workers int   thread-pool size for background resolution (default 3)
    """
    cache_ttl       = int(stream_cfg.get("cache_ttl",       3600))
    proxy           = bool(stream_cfg.get("proxy",           True))
    transcode       = bool(stream_cfg.get("ffmpeg_transcode", False))
    bitrate         = str(stream_cfg.get("ffmpeg_bitrate",   "192k"))
    prefetch_ahead  = int(stream_cfg.get("prefetch_ahead",   2))
    prefetch_workers= int(stream_cfg.get("prefetch_workers", 3))

    url = resolve_url(video_id, cache_ttl)
    if not url:
        return Response("Stream not found", status=404)

    # ── trigger background pre-resolution of upcoming tracks ─────────────────
    # Import here (not at top level) to avoid circular dependency.
    from services.prefetch_service import prefetch_service
    prefetch_service.configure(workers=prefetch_workers)
    prefetch_service.on_stream_started(
        video_id,
        cache_ttl=cache_ttl,
        prefetch_ahead=prefetch_ahead,
    )

    if not proxy:
        # Simple redirect — fastest, but client must be able to reach YouTube CDN
        return Response(status=302, headers={"Location": url})

    if transcode:
        return _ffmpeg_transcode_response(url, bitrate)

    return _proxy_response(url)


def _proxy_response(upstream_url: str) -> Response:
    """
    Pipe the upstream audio byte-for-byte, respecting Range requests.
    """
    headers = {
        "User-Agent":       "Mozilla/5.0",
        "Accept":           "*/*",
        "Accept-Encoding":  "identity",
    }
    range_header = request.headers.get("Range")
    if range_header:
        headers["Range"] = range_header

    try:
        upstream = requests.get(upstream_url, headers=headers, stream=True, timeout=15)
    except requests.RequestException as exc:
        log.error("_proxy_response: upstream request failed: %s", exc)
        return Response("Upstream error", status=502)

    content_type = upstream.headers.get("Content-Type", "audio/mpeg")
    resp_headers = {
        "Content-Type":  content_type,
        "Accept-Ranges": "bytes",
    }
    if "Content-Length" in upstream.headers:
        resp_headers["Content-Length"] = upstream.headers["Content-Length"]
    if "Content-Range" in upstream.headers:
        resp_headers["Content-Range"] = upstream.headers["Content-Range"]

    status_code = upstream.status_code  # usually 200 or 206

    @stream_with_context
    def generate() -> Generator[bytes, None, None]:
        try:
            for chunk in upstream.iter_content(chunk_size=32_768):
                if chunk:
                    yield chunk
        finally:
            upstream.close()

    return Response(generate(), status=status_code, headers=resp_headers)


def _ffmpeg_transcode_response(upstream_url: str, bitrate: str) -> Response:
    """
    Pipe *upstream_url* through ffmpeg → mp3 and stream to the client.
    Requires ffmpeg on PATH.
    """
    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        "-i",      upstream_url,
        "-vn",                        # drop video
        "-acodec", "libmp3lame",
        "-ab",     bitrate,
        "-f",      "mp3",
        "pipe:1",                     # write to stdout
    ]
    log.info("ffmpeg transcode: %s", " ".join(cmd))

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        log.error("ffmpeg not found — falling back to direct proxy")
        return _proxy_response(upstream_url)

    @stream_with_context
    def generate() -> Generator[bytes, None, None]:
        try:
            while True:
                chunk = proc.stdout.read(32_768)
                if not chunk:
                    break
                yield chunk
        finally:
            proc.stdout.close()
            proc.wait()

    return Response(
        generate(),
        status=200,
        headers={
            "Content-Type":  "audio/mpeg",
            "Accept-Ranges": "none",
        },
    )
