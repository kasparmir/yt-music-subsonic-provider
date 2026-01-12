from ytmusicapi import YTMusic
import yt_dlp
from datetime import datetime
import time

class YTMusicService:
    def __init__(self):
        self.ytmusic = YTMusic()
        self.stream_cache = {}
        self.cache_duration = 3600  # 1 hodina
    
    def search(self, query, filter_type='songs', limit=20):
        """Vyhledávání v YouTube Music"""
        try:
            return self.ytmusic.search(query, filter=filter_type, limit=limit)
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_artist(self, artist_id):
        """Získání informací o umělci"""
        try:
            return self.ytmusic.get_artist(artist_id)
        except Exception as e:
            print(f"Get artist error: {e}")
            return None
    
    def get_album(self, album_id):
        """Získání informací o albu"""
        try:
            album_info = self.ytmusic.get_album(album_id)
            if album_info and isinstance(album_info, dict):
                if 'title' not in album_info:
                    album_info['title'] = 'Unknown Album'
                if 'tracks' not in album_info:
                    album_info['tracks'] = []
                if 'thumbnails' not in album_info:
                    album_info['thumbnails'] = []
                if 'artists' not in album_info:
                    album_info['artists'] = []
                return album_info
            return None
        except KeyError as e:
            print(f"Get album KeyError: {e}")
            return None
        except Exception as e:
            print(f"Get album error: {e}")
            return None
    
    def get_song(self, video_id):
        """Získání informací o skladbě"""
        try:
            return self.ytmusic.get_song(video_id)
        except Exception as e:
            print(f"Get song error: {e}")
            return None
    
    def get_stream_url(self, video_id):
        """Získání stream URL s cachováním a optimalizací pro Music Assistant"""
        current_time = time.time()
        if video_id in self.stream_cache:
            cached_url, cached_time = self.stream_cache[video_id]
            if current_time - cached_time < self.cache_duration:
                print(f"[get_stream_url] Using cached URL for {video_id}")
                return cached_url
        
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'nocheckcertificate': True,
                'prefer_insecure': True,
                'no_check_certificate': True,
                'socket_timeout': 15,
                # OPRAVA: Vynutíme HTTP pro lepší kompatibilitu s Music Assistant
                'prefer_free_formats': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://music.youtube.com/watch?v={video_id}", download=False)
                
                url = None
                
                # OPRAVA: Preferujeme formáty s dobrou kompatibilitou
                if 'formats' in info:
                    # Najdeme audio formáty
                    audio_formats = [f for f in info['formats'] if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                    
                    if audio_formats:
                        # Seřadíme podle kvality a vybereme nejlepší
                        audio_formats.sort(key=lambda x: (
                            x.get('abr', 0),
                            1 if 'm4a' in x.get('ext', '') else 0  # Preferujeme m4a
                        ), reverse=True)
                        
                        url = audio_formats[0].get('url')
                        print(f"[get_stream_url] Best audio format: {audio_formats[0].get('format_id')} ({audio_formats[0].get('ext')}) for {video_id}")
                
                if not url and 'url' in info:
                    url = info['url']
                    print(f"[get_stream_url] Direct URL found for {video_id}")
                
                if url:
                    self.stream_cache[video_id] = (url, current_time)
                    return url
                
                print(f"[get_stream_url] No suitable URL found for {video_id}")
                return None
        except Exception as e:
            print(f"Get stream URL error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_best_thumbnail(self, thumbnails):
        """Získání největšího thumbnaiulu"""
        if not thumbnails:
            return ''
        largest = max(thumbnails, key=lambda x: x.get('width', 0))
        url = largest.get('url', '')
        return url.replace('=w60-h60', '=w600-h600').replace('=w226-h226', '=w600-h600')

ytmusic_service = YTMusicService()
