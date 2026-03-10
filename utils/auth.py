"""utils/auth.py — Subsonic token-auth + plain-password auth."""
import hashlib
import logging
from flask import request, current_app

log = logging.getLogger(__name__)


def verify_auth() -> bool:
    """
    Verify a Subsonic request using either:
      • token-auth  : ?u=<user>&t=<md5(password+salt)>&s=<salt>
      • plain-pass  : ?u=<user>&p=<password>   (or enc:<hex>)
    Returns True on success, False otherwise.
    """
    users: dict = current_app.config.get("USERS", {})

    username = _get("u", "username")
    if not username or username not in users:
        log.debug("Auth failed: unknown user %r", username)
        return False

    stored_password: str = users[username]

    token = _get("t", "token")
    salt  = _get("s", "salt")
    if token and salt:
        expected = hashlib.md5((stored_password + salt).encode()).hexdigest()
        ok = token == expected
        log.debug("Token-auth for %r: %s", username, "ok" if ok else "failed")
        return ok

    password = _get("p", "password")
    if password:
        # enc:<hex> encoding
        if password.startswith("enc:"):
            try:
                password = bytes.fromhex(password[4:]).decode("utf-8")
            except Exception:
                pass
        ok = password == stored_password
        log.debug("Plain-auth for %r: %s", username, "ok" if ok else "failed")
        return ok

    log.debug("Auth failed: no credentials provided for %r", username)
    return False


def _get(*keys: str) -> str:
    """Fetch first matching key from query-string or form body."""
    for key in keys:
        value = request.args.get(key) or request.form.get(key)
        if value:
            return value
    return ""
