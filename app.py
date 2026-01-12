from flask import Flask
from routes.web import web_bp
from routes.api import api_bp
from routes.subsonic import subsonic_bp

app = Flask(__name__)

# Registrace blueprintů
app.register_blueprint(web_bp)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(subsonic_bp, url_prefix='/rest')

if __name__ == '__main__':
    print("=" * 60)
    print("YouTube Music Web Aplikace")
    print("=" * 60)
    print("\nWebové rozhraní: http://localhost:5000")
    print("\nOpenSubsonic API:")
    print("  URL: http://localhost:5000/rest")
    print("  Uživatel: admin")
    print("  Heslo: admin")
    print("\nPro Music Assistant:")
    print("  Server: http://localhost:5000/rest")
    print("  Username: admin")
    print("  Password: admin")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
