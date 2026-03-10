"""routes/scrobble.py — scrobble, getNowPlaying, getScrobbles."""
import logging
from flask import Blueprint, request
from utils.auth        import verify_auth
from utils.response    import ok, err, ERR_WRONG_CREDS, ERR_MISSING_PARAM
import services.ytmusic_client as ytm
from services.scrobble_service import scrobble_service

log = logging.getLogger(__name__)
scrobble_bp = Blueprint("scrobble", __name__)

def _p(*keys):
    return next(
        (request.args.get(k) or request.form.get(k)
         for k in keys if request.args.get(k) or request.form.get(k)),
        "",
    )


@scrobble_bp.route("/scrobble.view", methods=["GET", "POST"])
@scrobble_bp.route("/scrobble",      methods=["GET", "POST"])
def scrobble():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")

    song_id    = _p("id")
    submission = _p("submission").lower() not in ("false", "0")

    if not song_id:
        return err(ERR_MISSING_PARAM, "Required parameter 'id' is missing")

    log.info("scrobble id=%s submission=%s", song_id, submission)

    info = ytm.get_song(song_id)
    if info and "videoDetails" in info:
        vd = info["videoDetails"]
        scrobble_service.add(
            video_id   = song_id,
            title      = vd.get("title",  "Unknown Title"),
            artist     = vd.get("author", "Unknown Artist"),
            album      = vd.get("album",  ""),
            submission = submission,
        )
    else:
        # Scrobble even if we can't resolve metadata
        scrobble_service.add(video_id=song_id, title=song_id,
                             artist="Unknown", submission=submission)

    return ok()


@scrobble_bp.route("/getNowPlaying.view", methods=["GET", "POST"])
@scrobble_bp.route("/getNowPlaying",      methods=["GET", "POST"])
def get_now_playing():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")

    np = scrobble_service.get_now_playing()
    entry = []
    if np:
        entry = [{
            "id":         np["video_id"],
            "title":      np["title"],
            "artist":     np["artist"],
            "album":      np.get("album", ""),
            "username":   "admin",
            "minutesAgo": 0,
            "playerId":   1,
        }]

    return ok({"nowPlaying": {"entry": entry}})


@scrobble_bp.route("/getScrobbles.view", methods=["GET", "POST"])
@scrobble_bp.route("/getScrobbles",      methods=["GET", "POST"])
def get_scrobbles():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")

    count = int(_p("count") or 50)
    since = _p("from")

    rows = scrobble_service.get_history(limit=count, since=since or None)
    items = [
        {
            "id":       r["video_id"],
            "title":    r["title"],
            "artist":   r["artist"],
            "album":    r.get("album", ""),
            "albumId":  r.get("album_id"),
            "time":     r["played_at"],
            "username": "admin",
        }
        for r in rows
    ]
    return ok({"scrobbles": {"scrobble": items}})
