"""utils/response.py — helpers for building Open Subsonic JSON responses."""
from flask import jsonify

_VERSION = "1.16.1"
_SERVER_TYPE = "ytmusic-subsonic"
_SERVER_VERSION = "2.0.0"


def ok(payload: dict = None):
    """Successful response, optionally with a payload dict."""
    body = {
        "status": "ok",
        "version": _VERSION,
        "type": _SERVER_TYPE,
        "serverVersion": _SERVER_VERSION,
    }
    if payload:
        body.update(payload)
    return jsonify({"subsonic-response": body})


def err(code: int, message: str):
    """Error response."""
    body = {
        "status": "failed",
        "version": _VERSION,
        "type": _SERVER_TYPE,
        "serverVersion": _SERVER_VERSION,
        "error": {"code": code, "message": message},
    }
    return jsonify({"subsonic-response": body})


# Subsonic error codes (subset)
ERR_GENERIC        = 0
ERR_MISSING_PARAM  = 10
ERR_WRONG_VERSION  = 20
ERR_WRONG_CREDS    = 40
ERR_NOT_FOUND      = 70
