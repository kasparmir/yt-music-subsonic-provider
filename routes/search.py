"""routes/search.py — search3 endpoint."""
import logging
from flask import Blueprint, request
from utils.auth       import verify_auth
from utils.response   import ok, err, ERR_WRONG_CREDS, ERR_GENERIC
import services.ytmusic_client as ytm
import services.mapper         as mapper
from services.prefetch_service import prefetch_service

log = logging.getLogger(__name__)
search_bp = Blueprint("search", __name__)

_PARAM = lambda *keys: next((request.args.get(k) or request.form.get(k) for k in keys if request.args.get(k) or request.form.get(k)), "")


@search_bp.route("/search3.view", methods=["GET", "POST"])
@search_bp.route("/search3",      methods=["GET", "POST"])
def search3():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")

    query = _PARAM("query")
    if not query:
        return ok({"searchResult3": {"song": [], "artist": [], "album": []}})

    song_count   = int(_PARAM("songCount")   or 20)
    artist_count = int(_PARAM("artistCount") or 10)
    album_count  = int(_PARAM("albumCount")  or 10)

    log.info("search3 query=%r songs=%d artists=%d albums=%d",
             query, song_count, artist_count, album_count)

    try:
        raw_songs   = ytm.search(query, filter_type="songs",   limit=song_count)
        raw_artists = ytm.search(query, filter_type="artists", limit=artist_count)
        raw_albums  = ytm.search(query, filter_type="albums",  limit=album_count)

        songs   = [s for raw in raw_songs   if (s := mapper.song_from_search(raw))]
        artists = [a for raw in raw_artists if (a := mapper.artist_from_search(raw))]
        albums  = [a for raw in raw_albums  if (a := mapper.album_from_search(raw))]

        log.info("search3 → %d songs, %d artists, %d albums",
                 len(songs), len(artists), len(albums))

        # Register song order for prefetch (most likely play order)
        prefetch_service.register_queue([s["id"] for s in songs])

        return ok({
            "searchResult3": {
                "song":   songs,
                "artist": artists,
                "album":  albums,
            }
        })

    except Exception as exc:
        log.exception("search3 error")
        return err(ERR_GENERIC, str(exc))
