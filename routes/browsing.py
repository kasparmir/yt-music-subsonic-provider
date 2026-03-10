"""
routes/browsing.py — getArtist, getAlbum, getSong, getTopSongs,
                     getArtistInfo2, getAlbumInfo2
"""
import logging
from flask import Blueprint, request
from utils.auth       import verify_auth
from utils.response   import ok, err, ERR_WRONG_CREDS, ERR_NOT_FOUND, ERR_MISSING_PARAM
import services.ytmusic_client as ytm
import services.mapper         as mapper
from services.prefetch_service import prefetch_service

log = logging.getLogger(__name__)
browsing_bp = Blueprint("browsing", __name__)

def _p(*keys):
    return next(
        (request.args.get(k) or request.form.get(k)
         for k in keys
         if  request.args.get(k) or request.form.get(k)),
        "",
    )

_EMPTY_ARTIST_INFO = {
    "biography":      "",
    "musicBrainzId":  "",
    "lastFmUrl":      "",
    "smallImageUrl":  "",
    "mediumImageUrl": "",
    "largeImageUrl":  "",
    "similarArtist":  [],
}

_EMPTY_ALBUM_INFO = {
    "notes":           "",
    "musicBrainzId":   "",
    "lastFmUrl":       "",
    "smallImageUrl":   "",
    "mediumImageUrl":  "",
    "largeImageUrl":   "",
}


# ─────────────────────────────────────────────────────────────────────────────
# getArtist
# ─────────────────────────────────────────────────────────────────────────────

@browsing_bp.route("/getArtist.view", methods=["GET", "POST"])
@browsing_bp.route("/getArtist",      methods=["GET", "POST"])
def get_artist():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")

    artist_id = _p("id")
    if not artist_id or artist_id.startswith("http"):
        return err(ERR_MISSING_PARAM, "Missing or invalid artist ID")

    log.info("getArtist id=%s", artist_id)
    info = ytm.get_artist(artist_id)
    if not info:
        return err(ERR_NOT_FOUND, "Artist not found")

    return ok({"artist": mapper.artist_detail(artist_id, info)})


# ─────────────────────────────────────────────────────────────────────────────
# getArtistInfo2
# ─────────────────────────────────────────────────────────────────────────────

@browsing_bp.route("/getArtistInfo2.view", methods=["GET", "POST"])
@browsing_bp.route("/getArtistInfo2",      methods=["GET", "POST"])
def get_artist_info2():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")

    artist_id = _p("id")
    log.info("getArtistInfo2 id=%s", artist_id)

    if not artist_id or artist_id.startswith("http"):
        return ok({"artistInfo2": _EMPTY_ARTIST_INFO})

    info = ytm.get_artist(artist_id)
    if not info:
        return ok({"artistInfo2": _EMPTY_ARTIST_INFO})

    return ok({"artistInfo2": mapper.artist_info(info, artist_id)})


# ─────────────────────────────────────────────────────────────────────────────
# getAlbum
# ─────────────────────────────────────────────────────────────────────────────

@browsing_bp.route("/getAlbum.view", methods=["GET", "POST"])
@browsing_bp.route("/getAlbum",      methods=["GET", "POST"])
def get_album():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")

    album_id = _p("id")
    log.info("getAlbum id=%s", album_id)

    # Non-real album IDs we can't look up
    if not album_id or album_id == "1" \
       or album_id.startswith("http") \
       or not album_id.startswith("MPRE"):
        return ok({
            "album": {
                "id": album_id or "1", "name": "Unknown Album",
                "artist": "Unknown Artist", "artistId": None,
                "coverArt": album_id if album_id and album_id != "1" else None,
                "songCount": 0, "duration": 0, "playCount": 0,
                "created": "", "starred": None,
                "year": 2024, "genre": "Unknown", "song": [],
            }
        })

    info = ytm.get_album(album_id)
    if not info:
        return err(ERR_NOT_FOUND, "Album not found")

    # Register track order so the prefetch service can warm upcoming tracks
    track_ids = [t.get("videoId", "") for t in info.get("tracks", [])]
    prefetch_service.register_queue(track_ids)
    log.debug("getAlbum: registered queue of %d tracks for prefetch", len(track_ids))

    return ok({"album": mapper.album_detail(album_id, info)})


# ─────────────────────────────────────────────────────────────────────────────
# getAlbumInfo2
# ─────────────────────────────────────────────────────────────────────────────

@browsing_bp.route("/getAlbumInfo2.view", methods=["GET", "POST"])
@browsing_bp.route("/getAlbumInfo2",      methods=["GET", "POST"])
def get_album_info2():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")

    album_id = _p("id")
    log.info("getAlbumInfo2 id=%s", album_id)

    if not album_id or album_id == "1" \
       or album_id.startswith("http") \
       or not album_id.startswith("MPRE"):
        return ok({"albumInfo": _EMPTY_ALBUM_INFO})

    info = ytm.get_album(album_id)
    if not info:
        return ok({"albumInfo": _EMPTY_ALBUM_INFO})

    return ok({"albumInfo": mapper.album_info(info)})


# ─────────────────────────────────────────────────────────────────────────────
# getSong
# ─────────────────────────────────────────────────────────────────────────────

@browsing_bp.route("/getSong.view", methods=["GET", "POST"])
@browsing_bp.route("/getSong",      methods=["GET", "POST"])
def get_song():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")

    song_id = _p("id")
    log.info("getSong id=%s", song_id)

    if not song_id or song_id.startswith("http"):
        return err(ERR_MISSING_PARAM, "Missing or invalid song ID")

    info = ytm.get_song(song_id)
    if not info or "videoDetails" not in info:
        return err(ERR_NOT_FOUND, "Song not found")

    vd        = info["videoDetails"]
    title     = vd.get("title", "Unknown Title")
    artist    = vd.get("author", "Unknown Artist")
    duration  = int(vd.get("lengthSeconds", 0))

    # Try to get album name from microformat
    album_name = "Unknown Album"
    mf = info.get("microformat", {}).get("microformatDataRenderer", {})
    if mf.get("albumName"):
        album_name = mf["albumName"]
    elif vd.get("album"):
        album_name = vd["album"]

    return ok({
        "song": {
            "id":          song_id,
            "parent":      "1",
            "isDir":       False,
            "title":       title,
            "album":       album_name,
            "artist":      artist,
            "track":       1,
            "year":        2024,
            "genre":       "Unknown",
            "coverArt":    song_id,
            "size":        5_000_000,
            "contentType": "audio/mpeg",
            "suffix":      "mp3",
            "duration":    duration,
            "bitRate":     192,
            "path":        f"{artist}/{album_name}/{title}.mp3",
            "isVideo":     False,
            "playCount":   0,
            "created":     "",
            "albumId":     None,
            "type":        "music",
        }
    })


# ─────────────────────────────────────────────────────────────────────────────
# getTopSongs
# ─────────────────────────────────────────────────────────────────────────────

@browsing_bp.route("/getTopSongs.view", methods=["GET", "POST"])
@browsing_bp.route("/getTopSongs",      methods=["GET", "POST"])
def get_top_songs():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")

    artist_name = _p("artist")
    count       = int(_p("count") or 50)
    log.info("getTopSongs artist=%r count=%d", artist_name, count)

    if not artist_name:
        return ok({"topSongs": {"song": []}})

    raw   = ytm.search(artist_name, filter_type="songs", limit=count)
    songs = [s for r in raw if (s := mapper.song_from_search(r))]

    # Warm upcoming tracks in the background
    prefetch_service.register_queue([s["id"] for s in songs])

    return ok({"topSongs": {"song": songs[:count]}})
