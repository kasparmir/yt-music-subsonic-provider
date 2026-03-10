"""
ytmusic-subsonic — Open Subsonic proxy for YouTube Music
"""
import logging
from flask import Flask
from config import load_config
from routes.system   import system_bp
from routes.browsing import browsing_bp
from routes.search   import search_bp
from routes.media    import media_bp
from routes.scrobble import scrobble_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

def create_app():
    cfg = load_config()
    app = Flask(__name__)
    app.config.update(cfg)

    for bp in (system_bp, browsing_bp, search_bp, media_bp, scrobble_bp):
        app.register_blueprint(bp, url_prefix="/rest")

    return app


if __name__ == "__main__":
    app = create_app()
    cfg = app.config
    host = cfg.get("HOST", "0.0.0.0")
    port = cfg.get("PORT", 5000)

    print("=" * 60)
    print("  ytmusic-subsonic — Open Subsonic proxy for YouTube Music")
    print("=" * 60)
    print(f"  Listening : http://{host}:{port}")
    print(f"  Subsonic  : http://{host}:{port}/rest")
    print(f"  Username  : {list(cfg['USERS'].keys())[0]}")
    print("=" * 60)

    app.run(host=host, port=port, debug=cfg.get("DEBUG", False))
