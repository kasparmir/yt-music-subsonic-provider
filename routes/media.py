"""
routes/media.py — /stream and /getCoverArt

stream     : resolves YouTube audio URL via yt-dlp and either proxies it
             byte-for-byte (with Range support) or transcodes via ffmpeg.
getCoverArt: fetches the best thumbnail from YTMusic and proxies it so
             clients never need to reach YouTube servers directly.
"""
import logging
import requests as req_lib
from flask import Blueprint, request, Response, current_app
from utils.auth            import verify_auth
from utils.response        import err, ERR_WRONG_CREDS, ERR_MISSING_PARAM, ERR_NOT_FOUND
from services.stream_service import build_stream_response
import services.ytmusic_client as ytm

log = logging.getLogger(__name__)
media_bp = Blueprint("media", __name__)

def _p(*keys):
    return next(
        (request.args.get(k) or request.form.get(k)
         for k in keys if request.args.get(k) or request.form.get(k)),
        "",
    )


# ─────────────────────────────────────────────────────────────────────────────
# /stream
# ─────────────────────────────────────────────────────────────────────────────

@media_bp.route("/stream.view", methods=["GET", "POST"])
@media_bp.route("/stream",      methods=["GET", "POST"])
def stream():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")

    video_id = _p("id")
    if not video_id:
        return err(ERR_MISSING_PARAM, "Required parameter 'id' is missing")

    log.info("stream video_id=%s", video_id)
    stream_cfg = current_app.config.get("STREAM", {})
    return build_stream_response(video_id, stream_cfg)


# ─────────────────────────────────────────────────────────────────────────────
# /getCoverArt — proxy so clients don't need to reach YouTube directly
# ─────────────────────────────────────────────────────────────────────────────

@media_bp.route("/getCoverArt.view", methods=["GET", "POST"])
@media_bp.route("/getCoverArt",      methods=["GET", "POST"])
def get_cover_art():
    if not verify_auth():
        return err(ERR_WRONG_CREDS, "Wrong username or password")

    cover_id = _p("id")
    size     = _p("size")   # optional requested pixel size (ignored for now)

    if not cover_id:
        return Response(status=404)

    # If the ID is already a full URL (shouldn't happen normally)
    if cover_id.startswith("http"):
        return _proxy_image(cover_id)

    # Try song → album → artist in that order
    thumb_url = (
        _thumb_from_song(cover_id)
        or _thumb_from_album(cover_id)
        or _thumb_from_artist(cover_id)
    )

    if thumb_url:
        return _proxy_image(thumb_url)

    return Response(status=404)


def _thumb_from_song(video_id: str):
    info = ytm.get_song(video_id)
    if info and "videoDetails" in info:
        thumbnails = info["videoDetails"].get("thumbnail", {}).get("thumbnails", [])
        return ytm.best_thumbnail(thumbnails) or None
    return None


def _thumb_from_album(browse_id: str):
    if not browse_id.startswith("MPRE"):
        return None
    info = ytm.get_album(browse_id)
    if info:
        return ytm.best_thumbnail(info.get("thumbnails", [])) or None
    return None


def _thumb_from_artist(browse_id: str):
    info = ytm.get_artist(browse_id)
    if info:
        return ytm.best_thumbnail(info.get("thumbnails", [])) or None
    return None


def _proxy_image(url: str) -> Response:
    """Download the image and stream it back to the client."""
    try:
        upstream = req_lib.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
            stream=True,
        )
        content_type = upstream.headers.get("Content-Type", "image/jpeg")
        data = upstream.content
        return Response(data, status=200, headers={"Content-Type": content_type})
    except Exception as exc:
        log.error("_proxy_image(%s): %s", url[:80], exc)
        return Response(status=502)
