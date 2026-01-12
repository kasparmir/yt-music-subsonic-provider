from flask import jsonify

def subsonic_response(data, status="ok"):
    """Vytvoření OpenSubsonic odpovědi"""
    response = {
        "subsonic-response": {
            "status": status,
            "version": "1.16.1",
            "type": "ytmusic",
            "serverVersion": "1.0.0",
            **data
        }
    }
    return jsonify(response)

