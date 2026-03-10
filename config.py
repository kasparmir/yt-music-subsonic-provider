"""
config.py — load configuration from config.yaml (if present) with env-var overrides.

Minimal config.yaml example
----------------------------
host: "0.0.0.0"
port: 5000
debug: false
users:
  admin: "admin"
stream:
  cache_ttl: 3600          # seconds a resolved stream URL is considered fresh
  proxy: true              # True → pipe audio through this app; False → 302 redirect
  ffmpeg_transcode: false  # True → re-encode to mp3 via ffmpeg (requires ffmpeg on PATH)
  ffmpeg_bitrate: "192k"
"""
import os
import secrets

# ── defaults ──────────────────────────────────────────────────────────────────
_DEFAULTS = {
    "HOST": "0.0.0.0",
    "PORT": 5000,
    "DEBUG": False,
    "USERS": {"admin": "admin"},
    "STREAM": {
        "cache_ttl": 3600,
        "proxy": True,
        "ffmpeg_transcode": False,
        "ffmpeg_bitrate": "192k",
    },
}


def load_config() -> dict:
    cfg = dict(_DEFAULTS)

    # Try to load YAML config
    config_path = os.environ.get("CONFIG_PATH", "config.yaml")
    if os.path.exists(config_path):
        try:
            import yaml  # optional dep — only needed when config.yaml exists
            with open(config_path, "r", encoding="utf-8") as f:
                file_cfg = yaml.safe_load(f) or {}

            if "host" in file_cfg:
                cfg["HOST"] = file_cfg["host"]
            if "port" in file_cfg:
                cfg["PORT"] = int(file_cfg["port"])
            if "debug" in file_cfg:
                cfg["DEBUG"] = bool(file_cfg["debug"])
            if "users" in file_cfg:
                cfg["USERS"] = {str(k): str(v) for k, v in file_cfg["users"].items()}
            if "stream" in file_cfg:
                cfg["STREAM"].update(file_cfg["stream"])
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Could not parse config.yaml: %s", exc)

    # Env-var overrides
    if os.environ.get("YTM_HOST"):
        cfg["HOST"] = os.environ["YTM_HOST"]
    if os.environ.get("YTM_PORT"):
        cfg["PORT"] = int(os.environ["YTM_PORT"])
    if os.environ.get("YTM_DEBUG"):
        cfg["DEBUG"] = os.environ["YTM_DEBUG"].lower() in ("1", "true", "yes")
    if os.environ.get("YTM_ADMIN_PASSWORD"):
        cfg["USERS"]["admin"] = os.environ["YTM_ADMIN_PASSWORD"]

    return cfg
