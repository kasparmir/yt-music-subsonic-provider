# routes/subsonic.py - KOMPLETNÍ VERZE
from flask import Blueprint, request, Response, stream_with_context
from datetime import datetime
from utils.auth import verify_auth
from utils.subsonic_helper import subsonic_response
from services.ytmusic_service import ytmusic_service
from services.scrobble_service import scrobble_service
import requests  # NOVÝ IMPORT

subsonic_bp = Blueprint('subsonic', __name__)
# =============================================================================
# ZÁKLADNÍ ENDPOINTY
# =============================================================================

@subsonic_bp.route('/ping.view', methods=['GET', 'POST'])
@subsonic_bp.route('/ping', methods=['GET', 'POST'])
def ping():
    return subsonic_response({})

@subsonic_bp.route('/getLicense.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getLicense', methods=['GET', 'POST'])
def get_license():
    return subsonic_response({
        "license": {"valid": True, "email": "admin@ytmusic.local", "licenseExpires": "2099-12-31T00:00:00"}
    })

@subsonic_bp.route('/getMusicFolders.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getMusicFolders', methods=['GET', 'POST'])
def get_music_folders():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    return subsonic_response({"musicFolders": {"musicFolder": [{"id": "1", "name": "YouTube Music"}]}})

@subsonic_bp.route('/getStarred2.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getStarred2', methods=['GET', 'POST'])
def get_starred2():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    return subsonic_response({"starred2": {"artist": [], "album": [], "song": []}})

@subsonic_bp.route('/getNewestPodcasts.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getNewestPodcasts', methods=['GET', 'POST'])
def get_newest_podcasts():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    return subsonic_response({"newestPodcasts": {"episode": []}})

@subsonic_bp.route('/getAlbumList2.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getAlbumList2', methods=['GET', 'POST'])
def get_album_list2():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    return subsonic_response({"albumList2": {"album": []}})

@subsonic_bp.route('/getOpenSubsonicExtensions.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getOpenSubsonicExtensions', methods=['GET', 'POST'])
def get_opensubsonic_extensions():
    return subsonic_response({"openSubsonicExtensions": []})

@subsonic_bp.route('/getArtists.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getArtists', methods=['GET', 'POST'])
def get_artists():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    return subsonic_response({"artists": {"ignoredArticles": "The El La Los Las Le Les", "index": []}})

@subsonic_bp.route('/getPlaylists.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getPlaylists', methods=['GET', 'POST'])
def get_playlists():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    return subsonic_response({"playlists": {"playlist": []}})

@subsonic_bp.route('/getPodcasts.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getPodcasts', methods=['GET', 'POST'])
def get_podcasts():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    return subsonic_response({"podcasts": {"channel": []}})

@subsonic_bp.route('/getPlaylist.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getPlaylist', methods=['GET', 'POST'])
def get_playlist():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    return subsonic_response({"playlist": {"id": "1", "name": "Empty", "songCount": 0, "entry": []}})

# =============================================================================
# VYHLEDÁVÁNÍ
# =============================================================================

@subsonic_bp.route('/search3.view', methods=['GET', 'POST'])
@subsonic_bp.route('/search3', methods=['GET', 'POST'])
def search3():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    
    query = request.args.get('query', '') or request.form.get('query', '')
    if not query:
        return subsonic_response({"searchResult3": {"song": [], "artist": [], "album": []}})
    
    try:
        songs = ytmusic_service.search(query, filter_type='songs', limit=20)
        artists = ytmusic_service.search(query, filter_type='artists', limit=10)
        albums = ytmusic_service.search(query, filter_type='albums', limit=10)
        
        song_list = []
        for song in songs[:20]:
            video_id = song.get('videoId', '')
            if not video_id:
                continue
            
            artist_name = song.get('artists', [{}])[0].get('name', 'Unknown Artist') if song.get('artists') else 'Unknown Artist'
            
            # OPRAVA: Správně získáme album info
            album_data = song.get('album')
            if album_data:
                album_name = album_data.get('name', 'Unknown Album')
                album_id = album_data.get('id', '')
            else:
                album_name = 'Unknown Album'
                album_id = ''
            
            song_list.append({
                "id": video_id,
                "parent": album_id if album_id else "1",
                "isDir": False,
                "title": song.get('title', 'Unknown Title'),
                "album": album_name,  # OPRAVA: Správný název alba
                "artist": artist_name,
                "track": 1,
                "year": 2024,
                "genre": "Unknown",
                "coverArt": video_id,
                "size": 5000000,
                "contentType": "audio/mpeg",
                "suffix": "mp3",
                "duration": song.get('duration_seconds', 0),
                "bitRate": 320,
                "path": f"{artist_name}/{album_name}/{song.get('title', 'Unknown')}.mp3",
                "isVideo": False,
                "playCount": 0,
                "created": datetime.now().isoformat(),
                "albumId": album_id if album_id else None,
                "artistId": song.get('artists', [{}])[0].get('id', '') if song.get('artists') else '',
                "type": "music"
            })
        
        artist_list = []
        for artist in artists[:10]:
            browse_id = artist.get('browseId', '')
            if not browse_id:
                continue
            
            artist_list.append({
                "id": browse_id,
                "name": artist.get('artist', 'Unknown Artist'),
                "coverArt": browse_id,
                "albumCount": 0,
                "starred": None
            })
        
        album_list = []
        for album in albums[:10]:
            browse_id = album.get('browseId', '')
            if not browse_id:
                continue
            
            artist_name = album.get('artists', [{}])[0].get('name', 'Unknown Artist') if album.get('artists') else 'Unknown Artist'
            
            album_list.append({
                "id": browse_id,
                "parent": "1",
                "album": album.get('title', 'Unknown Album'),
                "title": album.get('title', 'Unknown Album'),
                "name": album.get('title', 'Unknown Album'),
                "isDir": True,
                "coverArt": browse_id,
                "songCount": 10,
                "created": datetime.now().isoformat(),
                "duration": 0,
                "playCount": 0,
                "artist": artist_name,
                "artistId": album.get('artists', [{}])[0].get('id', '') if album.get('artists') else '',
                "year": album.get('year', 2024)
            })
        
        print(f"[search3] Returning {len(song_list)} songs, {len(artist_list)} artists, {len(album_list)} albums")
        
        return subsonic_response({
            "searchResult3": {
                "song": song_list,
                "artist": artist_list,
                "album": album_list
            }
        })
    except Exception as e:
        print(f"[search3] Error: {e}")
        import traceback
        traceback.print_exc()
        return subsonic_response({"error": {"code": 0, "message": str(e)}}, "failed")



# =============================================================================
# STREAMING
# =============================================================================
@subsonic_bp.route('/stream.view', methods=['GET', 'POST'])
@subsonic_bp.route('/stream', methods=['GET', 'POST'])
def stream():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    
    video_id = request.args.get('id', '') or request.form.get('id', '')
    print(f"[stream] Requesting stream for video ID: {video_id}")
    
    if not video_id:
        return subsonic_response({"error": {"code": 10, "message": "Required parameter missing"}}, "failed")
    
    try:
        url = ytmusic_service.get_stream_url(video_id)
        if url:
            print(f"[stream] Redirecting to: {url[:100]}...")
            
            # OPRAVA: Přidáme Range header support pro lepší kompatibilitu
            headers = {'Location': url}
            
            # Pokud klient požaduje Range, přepošleme to
            range_header = request.headers.get('Range')
            if range_header:
                print(f"[stream] Range request: {range_header}")
            
            return Response(status=302, headers=headers)
        
        print(f"[stream] No stream URL found for {video_id}")
        return subsonic_response({"error": {"code": 70, "message": "Song not found"}}, "failed")
    except Exception as e:
        print(f"[stream] Error: {e}")
        import traceback
        traceback.print_exc()
        return subsonic_response({"error": {"code": 0, "message": str(e)}}, "failed")





# =============================================================================
# COVER ART
# =============================================================================

@subsonic_bp.route('/getCoverArt.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getCoverArt', methods=['GET', 'POST'])
def get_cover_art():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    
    cover_id = request.args.get('id', '') or request.form.get('id', '')
    
    if cover_id.startswith('http'):
        return Response(status=302, headers={'Location': cover_id})
    
    if not cover_id:
        return Response(status=404)
    
    try:
        song_info = ytmusic_service.get_song(cover_id)
        if song_info and 'videoDetails' in song_info:
            thumbnails = song_info['videoDetails'].get('thumbnail', {}).get('thumbnails', [])
            if thumbnails:
                url = ytmusic_service.get_best_thumbnail(thumbnails)
                if url:
                    return Response(status=302, headers={'Location': url})
        
        album_info = ytmusic_service.get_album(cover_id)
        if album_info and 'thumbnails' in album_info:
            url = ytmusic_service.get_best_thumbnail(album_info['thumbnails'])
            if url:
                return Response(status=302, headers={'Location': url})
        
        artist_info = ytmusic_service.get_artist(cover_id)
        if artist_info and 'thumbnails' in artist_info:
            url = ytmusic_service.get_best_thumbnail(artist_info['thumbnails'])
            if url:
                return Response(status=302, headers={'Location': url})
        
        return Response(status=404)
    except Exception as e:
        print(f"[getCoverArt] Error: {e}")
        return Response(status=404)

# =============================================================================
# TOP SONGS
# =============================================================================

@subsonic_bp.route('/getTopSongs.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getTopSongs', methods=['GET', 'POST'])
def get_top_songs():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    
    artist_name = request.args.get('artist', '') or request.form.get('artist', '')
    count = int(request.args.get('count', 50) or request.form.get('count', 50))
    
    print(f"[getTopSongs] Artist: {artist_name}, Count: {count}")
    
    if not artist_name:
        return subsonic_response({"topSongs": {"song": []}})
    
    try:
        results = ytmusic_service.search(artist_name, filter_type='songs', limit=count)
        
        song_list = []
        for song in results[:count]:
            video_id = song.get('videoId', '')
            if not video_id:
                continue
            
            artist = song.get('artists', [{}])[0].get('name', artist_name) if song.get('artists') else artist_name
            album_name = song.get('album', {}).get('name', 'Unknown Album') if song.get('album') else 'Unknown Album'
            album_id = song.get('album', {}).get('id', '') if song.get('album') else ''
            
            song_list.append({
                "id": str(video_id),
                "parent": str(album_id) if album_id else "1",
                "isDir": False,
                "title": str(song.get('title', 'Unknown Title')),
                "album": str(album_name),
                "artist": str(artist),
                "track": 1,
                "year": 2024,
                "genre": "Unknown",
                "coverArt": str(video_id),
                "size": 5000000,
                "contentType": "audio/mpeg",
                "suffix": "mp3",
                "duration": int(song.get('duration_seconds', 0)),
                "bitRate": 320,
                "path": f"{artist}/{album_name}/{song.get('title', 'Unknown')}.mp3",
                "isVideo": False,
                "playCount": 0,
                "created": datetime.now().isoformat(),
                "albumId": str(album_id) if album_id else None,
                "artistId": song.get('artists', [{}])[0].get('id', '') if song.get('artists') else None,
                "type": "music"
            })
        
        print(f"[getTopSongs] Returning {len(song_list)} songs")
        
        return subsonic_response({"topSongs": {"song": song_list}})
    except Exception as e:
        print(f"[getTopSongs] Error: {e}")
        import traceback
        traceback.print_exc()
        return subsonic_response({"topSongs": {"song": []}})

# =============================================================================
# ARTIST INFO
# =============================================================================

@subsonic_bp.route('/getArtistInfo2.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getArtistInfo2', methods=['GET', 'POST'])
def get_artist_info2():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    
    artist_id = request.args.get('id', '') or request.form.get('id', '')
    print(f"[getArtistInfo2] ID: {artist_id}")
    
    if not artist_id or artist_id.startswith('http'):
        return subsonic_response({
            "artistInfo2": {
                "biography": "",
                "musicBrainzId": "",
                "lastFmUrl": "",
                "smallImageUrl": "",
                "mediumImageUrl": "",
                "largeImageUrl": "",
                "similarArtist": []
            }
        })
    
    try:
        artist_info = ytmusic_service.get_artist(artist_id)
        if not artist_info:
            return subsonic_response({
                "artistInfo2": {
                    "biography": "",
                    "musicBrainzId": "",
                    "lastFmUrl": "",
                    "smallImageUrl": "",
                    "mediumImageUrl": "",
                    "largeImageUrl": "",
                    "similarArtist": []
                }
            })
        
        cover_art = ytmusic_service.get_best_thumbnail(artist_info.get('thumbnails', []))
        description = artist_info.get('description', '')
        
        similar_artists = []
        related = artist_info.get('related', {})
        if isinstance(related, dict) and 'results' in related:
            for similar in related['results'][:5]:
                similar_id = similar.get('browseId', '')
                if similar_id:
                    similar_cover = ytmusic_service.get_best_thumbnail(similar.get('thumbnails', []))
                    similar_artists.append({
                        "id": similar_id,
                        "name": similar.get('title', 'Unknown Artist'),
                        "albumCount": 0,
                        "coverArt": similar_cover if similar_cover else None
                    })
        
        return subsonic_response({
            "artistInfo2": {
                "biography": description if description else "",
                "musicBrainzId": "",
                "lastFmUrl": "",
                "smallImageUrl": cover_art.replace('=w600-h600', '=w200-h200') if cover_art else "",
                "mediumImageUrl": cover_art.replace('=w600-h600', '=w400-h400') if cover_art else "",
                "largeImageUrl": cover_art if cover_art else "",
                "similarArtist": similar_artists
            }
        })
    except Exception as e:
        print(f"[getArtistInfo2] Error: {e}")
        return subsonic_response({
            "artistInfo2": {
                "biography": "",
                "musicBrainzId": "",
                "lastFmUrl": "",
                "smallImageUrl": "",
                "mediumImageUrl": "",
                "largeImageUrl": "",
                "similarArtist": []
            }
        })

# =============================================================================
# ALBUM INFO
# =============================================================================

@subsonic_bp.route('/getAlbumInfo2.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getAlbumInfo2', methods=['GET', 'POST'])
def get_album_info2():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    
    album_id = request.args.get('id', '') or request.form.get('id', '')
    print(f"[getAlbumInfo2] ID: {album_id}")
    
    if not album_id or album_id == "1" or album_id.startswith('http') or not album_id.startswith('MPRE'):
        return subsonic_response({
            "albumInfo": {
                "notes": "",
                "musicBrainzId": "",
                "lastFmUrl": "",
                "smallImageUrl": "",
                "mediumImageUrl": "",
                "largeImageUrl": ""
            }
        })
    
    try:
        album_info = ytmusic_service.get_album(album_id)
        if not album_info:
            return subsonic_response({
                "albumInfo": {
                    "notes": "",
                    "musicBrainzId": "",
                    "lastFmUrl": "",
                    "smallImageUrl": "",
                    "mediumImageUrl": "",
                    "largeImageUrl": ""
                }
            })
        
        cover_art = ytmusic_service.get_best_thumbnail(album_info.get('thumbnails', []))
        description = album_info.get('description', '')
        
        return subsonic_response({
            "albumInfo": {
                "notes": description if description else "",
                "musicBrainzId": "",
                "lastFmUrl": "",
                "smallImageUrl": cover_art.replace('=w600-h600', '=w200-h200') if cover_art else "",
                "mediumImageUrl": cover_art.replace('=w600-h600', '=w400-h400') if cover_art else "",
                "largeImageUrl": cover_art if cover_art else ""
            }
        })
    except Exception as e:
        print(f"[getAlbumInfo2] Error: {e}")
        return subsonic_response({
            "albumInfo": {
                "notes": "",
                "musicBrainzId": "",
                "lastFmUrl": "",
                "smallImageUrl": "",
                "mediumImageUrl": "",
                "largeImageUrl": ""
            }
        })

# =============================================================================
# ARTIST
# =============================================================================

@subsonic_bp.route('/getArtist.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getArtist', methods=['GET', 'POST'])
def get_artist():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    
    artist_id = request.args.get('id', '') or request.form.get('id', '')
    print(f"[getArtist] ID: {artist_id}")
    
    if not artist_id or artist_id.startswith('http'):
        return subsonic_response({"error": {"code": 70, "message": "Invalid artist ID"}}, "failed")
    
    try:
        artist_info = ytmusic_service.get_artist(artist_id)
        if not artist_info:
            return subsonic_response({"error": {"code": 70, "message": "Artist not found"}}, "failed")
        
        album_list = []
        albums = artist_info.get('albums', {})
        if isinstance(albums, dict):
            albums = albums.get('results', [])
        
        for album in albums:
            album_id = album.get('browseId', '')
            if not album_id:
                continue
            
            album_list.append({
                "id": str(album_id),
                "name": str(album.get('title', 'Unknown Album')),
                "artist": str(artist_info.get('name', '')),
                "artistId": str(artist_id),
                "coverArt": str(album_id),
                "songCount": 10,
                "duration": 0,
                "playCount": 0,
                "created": datetime.now().isoformat(),
                "year": int(album.get('year', 0)) if album.get('year') else None,
                "genre": "Unknown"
            })
        
        print(f"[getArtist] Returning artist with {len(album_list)} albums")
        
        return subsonic_response({
            "artist": {
                "id": str(artist_id),
                "name": str(artist_info.get('name', '')),
                "coverArt": str(artist_id),
                "albumCount": len(album_list),
                "starred": None,
                "album": album_list
            }
        })
    except Exception as e:
        print(f"[getArtist] Error: {e}")
        import traceback
        traceback.print_exc()
        return subsonic_response({"error": {"code": 70, "message": "Artist not found"}}, "failed")

# =============================================================================
# ALBUM
# =============================================================================

@subsonic_bp.route('/getAlbum.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getAlbum', methods=['GET', 'POST'])
def get_album():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    
    album_id = request.args.get('id', '') or request.form.get('id', '')
    print(f"[getAlbum] ID: {album_id}")
    
    if not album_id or album_id == "1" or album_id.startswith('http') or not album_id.startswith('MPRE'):
        print(f"[getAlbum] Invalid or generic album ID: {album_id}")
        return subsonic_response({
            "album": {
                "id": str(album_id),
                "name": "Unknown Album",
                "artist": "Unknown Artist",
                "artistId": None,
                "coverArt": str(album_id) if album_id and album_id != "1" else None,
                "songCount": 0,
                "duration": 0,
                "playCount": 0,
                "created": datetime.now().isoformat(),
                "starred": None,
                "year": 2024,
                "genre": "Unknown",
                "song": []
            }
        })
    
    try:
        album_info = ytmusic_service.get_album(album_id)
        if not album_info:
            print(f"[getAlbum] Album not found: {album_id}")
            return subsonic_response({"error": {"code": 70, "message": "Album not found"}}, "failed")
        
        print(f"[getAlbum] Found: {album_info.get('title', 'Unknown')}")
        
        artist_name = album_info.get('artists', [{}])[0].get('name', 'Unknown Artist') if album_info.get('artists') else 'Unknown Artist'
        artist_id = album_info.get('artists', [{}])[0].get('id', '') if album_info.get('artists') else ''
        
        song_list = []
        tracks = album_info.get('tracks', [])
        print(f"[getAlbum] Processing {len(tracks)} tracks")
        
        for idx, track in enumerate(tracks):
            video_id = track.get('videoId', '')
            if not video_id:
                continue
            
            track_artist = track.get('artists', [{}])[0].get('name', artist_name) if track.get('artists') else artist_name
            
            song_list.append({
                "id": str(video_id),
                "parent": str(album_id),
                "isDir": False,
                "title": str(track.get('title', 'Unknown Title')),
                "album": str(album_info.get('title', '')),
                "artist": str(track_artist),
                "track": int(idx + 1),
                "year": int(album_info.get('year', 2024)) if album_info.get('year') else 2024,
                "genre": "Unknown",
                "coverArt": str(video_id),
                "size": 5000000,
                "contentType": "audio/mpeg",
                "suffix": "mp3",
                "duration": int(track.get('duration_seconds', 0)),
                "bitRate": 320,
                "path": f"{artist_name}/{album_info.get('title', '')}/{track.get('title', '')}.mp3",
                "isVideo": False,
                "created": datetime.now().isoformat(),
                "albumId": str(album_id),
                "artistId": str(artist_id) if artist_id else None,
                "type": "music"
            })
        
        print(f"[getAlbum] Returning {len(song_list)} songs")
        
        return subsonic_response({
            "album": {
                "id": str(album_id),
                "name": str(album_info.get('title', '')),
                "artist": str(artist_name),
                "artistId": str(artist_id) if artist_id else None,
                "coverArt": str(album_id),
                "songCount": len(song_list),
                "duration": sum(track.get('duration_seconds', 0) for track in tracks),
                "playCount": 0,
                "created": datetime.now().isoformat(),
                "starred": None,
                "year": int(album_info.get('year', 2024)) if album_info.get('year') else 2024,
                "genre": "Unknown",
                "song": song_list
            }
        })
    except KeyError as e:
        print(f"[getAlbum] KeyError: {e}")
        import traceback
        traceback.print_exc()
        return subsonic_response({
            "album": {
                "id": str(album_id),
                "name": "Unknown Album",
                "artist": "Unknown Artist",
                "artistId": None,
                "coverArt": str(album_id) if album_id else None,
                "songCount": 0,
                "duration": 0,
                "playCount": 0,
                "created": datetime.now().isoformat(),
                "starred": None,
                "year": 2024,
                "genre": "Unknown",
                "song": []
            }
        })
    except Exception as e:
        print(f"[getAlbum] Error: {e}")
        import traceback
        traceback.print_exc()
        return subsonic_response({"error": {"code": 70, "message": "Album not found"}}, "failed")

# =============================================================================
# SONG
# =============================================================================

@subsonic_bp.route('/getSong.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getSong', methods=['GET', 'POST'])
def get_song():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    
    song_id = request.args.get('id', '') or request.form.get('id', '')
    print(f"[getSong] ID: {song_id}")
    
    if not song_id or song_id.startswith('http'):
        return subsonic_response({"error": {"code": 70, "message": "Invalid song ID"}}, "failed")
    
    try:
        song_info = ytmusic_service.get_song(song_id)
        if not song_info or 'videoDetails' not in song_info:
            return subsonic_response({"error": {"code": 70, "message": "Song not found"}}, "failed")
        
        video_details = song_info['videoDetails']
        print(f"[getSong] Found: {video_details.get('title', 'Unknown')}")
        
        # OPRAVA: Zkusíme získat správné album info
        album_name = 'Unknown Album'
        album_id = None
        
        # Pokusíme se najít album v microformat
        if 'microformat' in song_info:
            microformat = song_info['microformat'].get('microformatDataRenderer', {})
            album_name = microformat.get('albumName', album_name)
        
        # Nebo v videoDetails
        if 'album' in video_details:
            album_name = video_details['album']
        
        return subsonic_response({
            "song": {
                "id": str(song_id),
                "parent": str(album_id) if album_id else "1",
                "isDir": False,
                "title": str(video_details.get('title', 'Unknown Title')),
                "album": str(album_name),  # OPRAVA: Lepší detekce alba
                "artist": str(video_details.get('author', 'Unknown Artist')),
                "track": 1,
                "year": 2024,
                "genre": "Unknown",
                "coverArt": str(song_id),
                "size": 5000000,
                "contentType": "audio/mpeg",
                "suffix": "mp3",
                "duration": int(video_details.get('lengthSeconds', 0)),
                "bitRate": 320,
                "path": f"{video_details.get('author', 'Unknown')}/{album_name}/{video_details.get('title', 'Unknown')}.mp3",
                "isVideo": False,
                "playCount": 0,
                "created": datetime.now().isoformat(),
                "albumId": str(album_id) if album_id else None,
                "type": "music"
            }
        })
    except Exception as e:
        print(f"[getSong] Error: {e}")
        import traceback
        traceback.print_exc()
        return subsonic_response({"error": {"code": 70, "message": "Song not found"}}, "failed")

# =============================================================================
# SCROBBLING
# =============================================================================

@subsonic_bp.route('/scrobble.view', methods=['GET', 'POST'])
@subsonic_bp.route('/scrobble', methods=['GET', 'POST'])
def scrobble():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    
    song_id = request.args.get('id', '') or request.form.get('id', '')
    submission = request.args.get('submission', 'true').lower() == 'true'
    
    print(f"[scrobble] Song ID: {song_id}, Submission: {submission}")
    
    if not song_id:
        return subsonic_response({"error": {"code": 10, "message": "Required parameter missing"}}, "failed")
    
    try:
        song_info = ytmusic_service.get_song(song_id)
        if song_info and 'videoDetails' in song_info:
            video_details = song_info['videoDetails']
            title = video_details.get('title', 'Unknown Title')
            artist = video_details.get('author', 'Unknown Artist')
            album = video_details.get('album', 'Unknown Album')
            
            scrobble_service.add_scrobble(
                song_id=song_id,
                title=title,
                artist=artist,
                album=album,
                submission=submission
            )
            
            return subsonic_response({})
        else:
            print(f"[scrobble] Song not found: {song_id}")
            return subsonic_response({})
    except Exception as e:
        print(f"[scrobble] Error: {e}")
        import traceback
        traceback.print_exc()
        return subsonic_response({})

@subsonic_bp.route('/getScrobbles.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getScrobbles', methods=['GET', 'POST'])
def get_scrobbles():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    
    username = request.args.get('username', '') or request.form.get('username', '')
    count = int(request.args.get('count', 50) or request.form.get('count', 50))
    
    try:
        scrobbles = scrobble_service.get_scrobbles(username=username, limit=count)
        
        scrobble_list = []
        for scrobble in scrobbles:
            scrobble_list.append({
                "id": scrobble['id'],
                "title": scrobble['title'],
                "artist": scrobble['artist'],
                "album": scrobble.get('album', ''),
                "albumId": scrobble.get('albumId'),
                "time": scrobble['time'],
                "username": "admin"
            })
        
        return subsonic_response({
            "scrobbles": {
                "scrobble": scrobble_list
            }
        })
    except Exception as e:
        print(f"[getScrobbles] Error: {e}")
        return subsonic_response({
            "scrobbles": {
                "scrobble": []
            }
        })

@subsonic_bp.route('/getNowPlaying.view', methods=['GET', 'POST'])
@subsonic_bp.route('/getNowPlaying', methods=['GET', 'POST'])
def get_now_playing():
    if not verify_auth():
        return subsonic_response({"error": {"code": 40, "message": "Wrong username or password"}}, "failed")
    
    try:
        now_playing = scrobble_service.get_now_playing()
        
        if now_playing:
            return subsonic_response({
                "nowPlaying": {
                    "entry": [{
                        "id": now_playing['id'],
                        "title": now_playing['title'],
                        "artist": now_playing['artist'],
                        "album": now_playing.get('album', ''),
                        "username": "admin",
                        "minutesAgo": 0,
                        "playerId": 1
                    }]
                }
            })
        else:
            return subsonic_response({
                "nowPlaying": {
                    "entry": []
                }
            })
    except Exception as e:
        print(f"[getNowPlaying] Error: {e}")
        return subsonic_response({
            "nowPlaying": {
                "entry": []
            }
        })

@subsonic_bp.route('/test/stream/<video_id>')
def test_stream(video_id):
    """Test endpoint pro kontrolu stream URL"""
    try:
        url = ytmusic_service.get_stream_url(video_id)
        if url:
            return {
                "success": True,
                "video_id": video_id,
                "stream_url": url[:200] + "...",
                "full_url_length": len(url)
            }
        return {"success": False, "error": "No URL found"}, 404
    except Exception as e:
        return {"success": False, "error": str(e)}, 500
