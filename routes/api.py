from flask import Blueprint, jsonify, request
from services.ytmusic_service import ytmusic_service

api_bp = Blueprint('api', __name__)

@api_bp.route('/search')
def search():
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'songs')
    try:
        results = ytmusic_service.search(query, filter_type=search_type)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/stream/<video_id>')
def stream(video_id):
    try:
        url = ytmusic_service.get_stream_url(video_id)
        if url:
            return jsonify({"url": url})
        return jsonify({"error": "Stream not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

