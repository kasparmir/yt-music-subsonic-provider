from datetime import datetime
import json
import os

class ScrobbleService:
    def __init__(self, db_file='scrobbles.json'):
        self.db_file = db_file
        self.scrobbles = self.load_scrobbles()
    
    def load_scrobbles(self):
        """Načtení historie z disku"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading scrobbles: {e}")
                return []
        return []
    
    def save_scrobbles(self):
        """Uložení historie na disk"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.scrobbles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving scrobbles: {e}")
    
    def add_scrobble(self, song_id, title, artist, album, album_id=None, submission=True):
        """Přidání záznamu o přehrání"""
        scrobble = {
            "id": song_id,
            "title": title,
            "artist": artist,
            "album": album,
            "albumId": album_id,
            "time": datetime.now().isoformat(),
            "submission": submission
        }
        
        self.scrobbles.insert(0, scrobble)  # Přidáme na začátek
        
        # Omezíme na posledních 1000 záznamů
        if len(self.scrobbles) > 1000:
            self.scrobbles = self.scrobbles[:1000]
        
        self.save_scrobbles()
        print(f"[Scrobble] Added: {title} by {artist}")
        return True
    
    def get_now_playing(self):
        """Získání aktuálně přehrávané skladby (ne submission)"""
        for scrobble in self.scrobbles[:10]:  # Hledáme v posledních 10
            if not scrobble.get('submission', True):
                return scrobble
        return None
    
    def get_scrobbles(self, username=None, limit=50, since=None):
        """Získání historie přehrání"""
        filtered = self.scrobbles
        
        if since:
            try:
                since_dt = datetime.fromisoformat(since)
                filtered = [s for s in filtered if datetime.fromisoformat(s['time']) >= since_dt]
            except:
                pass
        
        return filtered[:limit]

# Globální instance
scrobble_service = ScrobbleService()
