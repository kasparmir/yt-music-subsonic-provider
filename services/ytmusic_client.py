"""
services/ytmusic_client.py — thin, unauthenticated wrapper around ytmusicapi.

All methods return raw ytmusicapi dicts or None/[] on error; they do NOT raise.
"""
import logging
from typing import Optional
from ytmusicapi import YTMusic

log = logging.getLogger(__name__)

# Single shared YTMusic instance (unauthenticated — no Google account needed)
_ytm = YTMusic()


# ─────────────────────────────────────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────────────────────────────────────

def search(query: str, filter_type: str = "songs", limit: int = 20) -> list:
    """
    filter_type: 'songs' | 'albums' | 'artists' | 'playlists' | 'videos'
    """
    try:
        return _ytm.search(query, filter=filter_type, limit=limit) or []
    except Exception as exc:
        log.error("search(%r, %r): %s", query, filter_type, exc)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Lookups
# ─────────────────────────────────────────────────────────────────────────────

def get_song(video_id: str) -> Optional[dict]:
    try:
        return _ytm.get_song(video_id)
    except Exception as exc:
        log.error("get_song(%r): %s", video_id, exc)
        return None


def get_artist(browse_id: str) -> Optional[dict]:
    try:
        return _ytm.get_artist(browse_id)
    except Exception as exc:
        log.error("get_artist(%r): %s", browse_id, exc)
        return None


def get_album(browse_id: str) -> Optional[dict]:
    try:
        info = _ytm.get_album(browse_id)
        if not isinstance(info, dict):
            return None
        # normalise missing keys
        info.setdefault("title",      "Unknown Album")
        info.setdefault("tracks",     [])
        info.setdefault("thumbnails", [])
        info.setdefault("artists",    [])
        return info
    except Exception as exc:
        log.error("get_album(%r): %s", browse_id, exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Thumbnail helpers
# ─────────────────────────────────────────────────────────────────────────────

def best_thumbnail(thumbnails: list, target_size: int = 600) -> str:
    """Return the URL of the thumbnail closest to *target_size* pixels wide."""
    if not thumbnails:
        return ""
    # pick the largest available
    best = max(thumbnails, key=lambda t: t.get("width", 0))
    url: str = best.get("url", "")
    # upgrade small Google thumbnail sizes to 600×600
    for old in ("=w60-h60", "=w120-h120", "=w226-h226"):
        url = url.replace(old, f"=w{target_size}-h{target_size}")
    return url
