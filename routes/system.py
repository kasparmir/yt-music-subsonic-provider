"""routes/system.py — ping, getLicense, getMusicFolders, housekeeping stubs."""
from flask import Blueprint, jsonify
from utils.auth     import verify_auth
from utils.response import ok, err, ERR_WRONG_CREDS

system_bp = Blueprint("system", __name__)

# convenience: both /rest/ping and /rest/ping.view
def _route(*paths):
    def decorator(f):
        for p in paths:
            system_bp.add_url_rule(p, endpoint=f.__name__ + p, view_func=f, methods=["GET", "POST"])
        return f
    return decorator


@system_bp.route("/ping.view",  methods=["GET", "POST"])
@system_bp.route("/ping",       methods=["GET", "POST"])
def ping():
    return ok()


@system_bp.route("/getLicense.view", methods=["GET", "POST"])
@system_bp.route("/getLicense",      methods=["GET", "POST"])
def get_license():
    return ok({
        "license": {
            "valid":          True,
            "email":          "admin@ytmusic.local",
            "licenseExpires": "2099-12-31T00:00:00",
        }
    })


@system_bp.route("/getMusicFolders.view", methods=["GET", "POST"])
@system_bp.route("/getMusicFolders",      methods=["GET", "POST"])
def get_music_folders():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")
    return ok({
        "musicFolders": {
            "musicFolder": [{"id": "1", "name": "YouTube Music"}]
        }
    })


@system_bp.route("/getOpenSubsonicExtensions.view", methods=["GET", "POST"])
@system_bp.route("/getOpenSubsonicExtensions",      methods=["GET", "POST"])
def get_extensions():
    return ok({"openSubsonicExtensions": []})


# ── stubs that clients expect but we have no data for ──────────────────────

@system_bp.route("/getStarred2.view",       methods=["GET", "POST"])
@system_bp.route("/getStarred2",            methods=["GET", "POST"])
def get_starred2():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")
    return ok({"starred2": {"artist": [], "album": [], "song": []}})


@system_bp.route("/getNewestPodcasts.view", methods=["GET", "POST"])
@system_bp.route("/getNewestPodcasts",      methods=["GET", "POST"])
def get_newest_podcasts():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")
    return ok({"newestPodcasts": {"episode": []}})


@system_bp.route("/getAlbumList2.view", methods=["GET", "POST"])
@system_bp.route("/getAlbumList2",      methods=["GET", "POST"])
def get_album_list2():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")
    return ok({"albumList2": {"album": []}})


@system_bp.route("/getArtists.view", methods=["GET", "POST"])
@system_bp.route("/getArtists",      methods=["GET", "POST"])
def get_artists():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")
    return ok({"artists": {"ignoredArticles": "The El La Los Las Le Les", "index": []}})


@system_bp.route("/getPlaylists.view", methods=["GET", "POST"])
@system_bp.route("/getPlaylists",      methods=["GET", "POST"])
def get_playlists():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")
    return ok({"playlists": {"playlist": []}})


@system_bp.route("/getPodcasts.view", methods=["GET", "POST"])
@system_bp.route("/getPodcasts",      methods=["GET", "POST"])
def get_podcasts():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")
    return ok({"podcasts": {"channel": []}})


@system_bp.route("/getPlaylist.view", methods=["GET", "POST"])
@system_bp.route("/getPlaylist",      methods=["GET", "POST"])
def get_playlist():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")
    return ok({"playlist": {"id": "1", "name": "Empty", "songCount": 0, "entry": []}})


# ─────────────────────────────────────────────────────────────────────────────
# Diagnostics (unauthenticated — internal use only)
# ─────────────────────────────────────────────────────────────────────────────

@system_bp.route("/prefetchStatus", methods=["GET"])
def prefetch_status():
    """Return current prefetch service state (registry size, in-flight IDs)."""
    from services.prefetch_service import prefetch_service
    return jsonify(prefetch_service.status())
