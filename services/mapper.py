"""
services/mapper.py — translate raw ytmusicapi objects into Subsonic-shaped dicts.

All public functions return plain Python dicts; they are JSON-serialisable and
contain only string / int / bool / None values (no datetime objects etc.).

Subsonic ID conventions used here
──────────────────────────────────
  video IDs   → used as-is (11-char YouTube video IDs)
  album IDs   → ytmusicapi browseId (starts with MPRE…)
  artist IDs  → ytmusicapi browseId (starts with UC… or similar)

These are opaque to the client and are echoed back in subsequent requests.
"""
from datetime import datetime
from typing import Optional

_NOW = lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")  # noqa: E731

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _artist_name(obj: dict, fallback: str = "Unknown Artist") -> str:
    artists = obj.get("artists") or []
    return artists[0].get("name", fallback) if artists else fallback


def _artist_id(obj: dict) -> Optional[str]:
    artists = obj.get("artists") or []
    return artists[0].get("id") if artists else None


def _album_name(obj: dict) -> str:
    album = obj.get("album")
    if isinstance(album, dict):
        return album.get("name", "Unknown Album")
    return "Unknown Album"


def _album_id(obj: dict) -> Optional[str]:
    album = obj.get("album")
    if isinstance(album, dict):
        return album.get("id") or None
    return None


def _duration(obj: dict) -> int:
    return int(obj.get("duration_seconds") or 0)


def _year(obj: dict) -> Optional[int]:
    y = obj.get("year")
    try:
        return int(y) if y else None
    except (TypeError, ValueError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Public mappers
# ─────────────────────────────────────────────────────────────────────────────

def song_from_search(raw: dict) -> Optional[dict]:
    """Map a search-result song dict to a Subsonic <child> / song object."""
    video_id = raw.get("videoId", "")
    if not video_id:
        return None

    artist  = _artist_name(raw)
    a_id    = _artist_id(raw)
    album   = _album_name(raw)
    alb_id  = _album_id(raw)
    dur     = _duration(raw)
    title   = raw.get("title", "Unknown Title")

    return {
        "id":          video_id,
        "parent":      alb_id or "1",
        "isDir":       False,
        "title":       title,
        "album":       album,
        "artist":      artist,
        "track":       1,
        "year":        _year(raw) or 2024,
        "genre":       "Unknown",
        "coverArt":    video_id,
        "size":        5_000_000,
        "contentType": "audio/mpeg",
        "suffix":      "mp3",
        "duration":    dur,
        "bitRate":     192,
        "path":        f"{artist}/{album}/{title}.mp3",
        "isVideo":     False,
        "playCount":   0,
        "created":     _NOW(),
        "albumId":     alb_id,
        "artistId":    a_id,
        "type":        "music",
    }


def song_from_track(track: dict, album_info: dict, index: int = 1) -> Optional[dict]:
    """Map an album-track dict (from get_album) to a Subsonic song object."""
    video_id = track.get("videoId", "")
    if not video_id:
        return None

    album_id   = album_info.get("_browse_id", "")        # injected by route
    album_name = album_info.get("title", "Unknown Album")
    album_year = _year(album_info) or 2024

    # track artist > album artist
    artist   = _artist_name(track) or _artist_name(album_info)
    a_id     = _artist_id(track)   or _artist_id(album_info)
    title    = track.get("title", "Unknown Title")
    dur      = _duration(track)

    return {
        "id":          video_id,
        "parent":      album_id or "1",
        "isDir":       False,
        "title":       title,
        "album":       album_name,
        "artist":      artist,
        "track":       index,
        "year":        album_year,
        "genre":       "Unknown",
        "coverArt":    video_id,
        "size":        5_000_000,
        "contentType": "audio/mpeg",
        "suffix":      "mp3",
        "duration":    dur,
        "bitRate":     192,
        "path":        f"{artist}/{album_name}/{title}.mp3",
        "isVideo":     False,
        "playCount":   0,
        "created":     _NOW(),
        "albumId":     album_id or None,
        "artistId":    a_id,
        "type":        "music",
    }


def artist_from_search(raw: dict) -> Optional[dict]:
    browse_id = raw.get("browseId", "")
    if not browse_id:
        return None
    return {
        "id":         browse_id,
        "name":       raw.get("artist", "Unknown Artist"),
        "coverArt":   browse_id,
        "albumCount": 0,
        "starred":    None,
    }


def artist_detail(browse_id: str, info: dict) -> dict:
    """Map get_artist() result to a full Subsonic artist object with album list."""
    raw_albums = info.get("albums", {})
    if isinstance(raw_albums, dict):
        raw_albums = raw_albums.get("results", [])

    album_list = []
    for alb in raw_albums:
        alb_id = alb.get("browseId", "")
        if not alb_id:
            continue
        album_list.append({
            "id":        alb_id,
            "name":      alb.get("title", "Unknown Album"),
            "artist":    info.get("name", ""),
            "artistId":  browse_id,
            "coverArt":  alb_id,
            "songCount": 10,
            "duration":  0,
            "playCount": 0,
            "created":   _NOW(),
            "year":      _year(alb),
            "genre":     "Unknown",
        })

    return {
        "id":         browse_id,
        "name":       info.get("name", "Unknown Artist"),
        "coverArt":   browse_id,
        "albumCount": len(album_list),
        "starred":    None,
        "album":      album_list,
    }


def album_from_search(raw: dict) -> Optional[dict]:
    browse_id = raw.get("browseId", "")
    if not browse_id:
        return None
    artist = _artist_name(raw, fallback=raw.get("artists", [{}])[0].get("name", "Unknown Artist") if raw.get("artists") else "Unknown Artist")
    return {
        "id":        browse_id,
        "parent":    "1",
        "album":     raw.get("title", "Unknown Album"),
        "title":     raw.get("title", "Unknown Album"),
        "name":      raw.get("title", "Unknown Album"),
        "isDir":     True,
        "coverArt":  browse_id,
        "songCount": 10,
        "created":   _NOW(),
        "duration":  0,
        "playCount": 0,
        "artist":    artist,
        "artistId":  _artist_id(raw),
        "year":      _year(raw) or 2024,
    }


def album_detail(browse_id: str, info: dict) -> dict:
    """Map get_album() result to a full Subsonic album object with track list."""
    # inject browse_id so song_from_track can reference it
    info["_browse_id"] = browse_id

    artist   = _artist_name(info)
    a_id     = _artist_id(info)
    tracks   = info.get("tracks", [])

    songs = []
    for idx, track in enumerate(tracks, start=1):
        s = song_from_track(track, info, idx)
        if s:
            songs.append(s)

    total_dur = sum(s["duration"] for s in songs)

    return {
        "id":        browse_id,
        "name":      info.get("title", "Unknown Album"),
        "artist":    artist,
        "artistId":  a_id,
        "coverArt":  browse_id,
        "songCount": len(songs),
        "duration":  total_dur,
        "playCount": 0,
        "created":   _NOW(),
        "starred":   None,
        "year":      _year(info) or 2024,
        "genre":     "Unknown",
        "song":      songs,
    }


def artist_info(info: dict, browse_id: str) -> dict:
    from services.ytmusic_client import best_thumbnail
    cover = best_thumbnail(info.get("thumbnails", []))

    similar = []
    related = info.get("related", {})
    if isinstance(related, dict):
        for sim in related.get("results", [])[:5]:
            sim_id = sim.get("browseId", "")
            if sim_id:
                similar.append({
                    "id":         sim_id,
                    "name":       sim.get("title", "Unknown"),
                    "albumCount": 0,
                    "coverArt":   sim_id,
                })

    def _resize(url: str, w: int) -> str:
        return url.replace("=w600-h600", f"=w{w}-h{w}") if url else ""

    return {
        "biography":      info.get("description", ""),
        "musicBrainzId":  "",
        "lastFmUrl":      "",
        "smallImageUrl":  _resize(cover, 200),
        "mediumImageUrl": _resize(cover, 400),
        "largeImageUrl":  cover,
        "similarArtist":  similar,
    }


def album_info(info: dict) -> dict:
    from services.ytmusic_client import best_thumbnail
    cover = best_thumbnail(info.get("thumbnails", []))

    def _resize(url: str, w: int) -> str:
        return url.replace("=w600-h600", f"=w{w}-h{w}") if url else ""

    return {
        "notes":           info.get("description", ""),
        "musicBrainzId":   "",
        "lastFmUrl":       "",
        "smallImageUrl":   _resize(cover, 200),
        "mediumImageUrl":  _resize(cover, 400),
        "largeImageUrl":   cover,
    }
