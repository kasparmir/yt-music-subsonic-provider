# ytmusic-subsonic

An **Open Subsonic API proxy** for YouTube Music.  
Add it to [Music Assistant](https://music-assistant.io) (or any Subsonic client) and browse/play YouTube Music without a Google account.

---

## Features

| Feature | Details |
|---|---|
| No Google account needed | Uses `ytmusicapi` in unauthenticated mode |
| Proxy streaming | Audio piped through this server (Range requests supported) |
| Optional ffmpeg transcode | Re-encode to mp3 on the fly |
| Cover-art proxy | Images served locally — no CORS issues for clients |
| SQLite scrobble history | Light listen-history stored in `scrobbles.db` |
| YAML + env-var config | Easy deployment in Docker / systemd |

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) copy and edit the example config
cp config.yaml.example config.yaml

# 3. Run
python app.py
```

The server starts on **http://0.0.0.0:5000** by default.

---

## Connecting Music Assistant

1. Open Music Assistant → **Settings → Music Providers → Add Provider**
2. Choose **Subsonic / OpenSubsonic**
3. Fill in:
   - **Server URL**: `http://<your-server-ip>:5000/rest`
   - **Username**: `admin`
   - **Password**: `admin`
4. Save and test the connection.

---

## Configuration

### config.yaml (recommended)

```yaml
host: "0.0.0.0"
port: 5000
debug: false

users:
  admin: "yourpassword"

stream:
  cache_ttl: 3600          # seconds before re-resolving a CDN URL
  proxy: true              # pipe audio through this server
  ffmpeg_transcode: false  # re-encode to mp3 via ffmpeg
  ffmpeg_bitrate: "192k"
```

### Environment variables (override config.yaml)

| Variable | Default | Description |
|---|---|---|
| `YTM_HOST` | `0.0.0.0` | Bind address |
| `YTM_PORT` | `5000` | Port |
| `YTM_DEBUG` | `false` | Flask debug mode |
| `YTM_ADMIN_PASSWORD` | `admin` | Password for the `admin` user |
| `CONFIG_PATH` | `config.yaml` | Path to the YAML config file |

---

## Streaming modes

### `proxy: true` (default)
Audio bytes are fetched from YouTube CDN and piped through this server.  
Supports **HTTP Range requests** so clients can seek without re-buffering.

### `proxy: false`
The server returns a `302 redirect` to the YouTube CDN URL.  
Faster (one less hop) but requires the client to be able to reach YouTube directly.

### `ffmpeg_transcode: true`
Requires `ffmpeg` on `PATH`.  
Re-encodes the audio stream to mp3 before sending it.  
Useful for clients that don't support opus or m4a containers.

---

## Project structure

```
ytmusic-subsonic/
├── app.py                  # Application factory & entry point
├── config.py               # Config loader (YAML + env vars)
├── config.yaml.example     # Annotated example configuration
├── requirements.txt
├── utils/
│   ├── auth.py             # Subsonic token-auth + plain-password auth
│   └── response.py         # ok() / err() response helpers
├── services/
│   ├── ytmusic_client.py   # Unauthenticated ytmusicapi wrapper
│   ├── mapper.py           # YTMusic dicts → Subsonic-shaped dicts
│   ├── stream_service.py   # yt-dlp URL resolver + proxy/transcode
│   └── scrobble_service.py # SQLite-backed listen history
└── routes/
    ├── system.py           # ping, getLicense, getMusicFolders, stubs
    ├── search.py           # search3
    ├── browsing.py         # getArtist, getAlbum, getSong, getTopSongs, …
    ├── media.py            # stream, getCoverArt
    └── scrobble.py         # scrobble, getNowPlaying, getScrobbles
```

---

## Supported endpoints

### System
- `GET /rest/ping`
- `GET /rest/getLicense`
- `GET /rest/getMusicFolders`
- `GET /rest/getOpenSubsonicExtensions`
- `GET /rest/getArtists` *(returns empty — no persistent library)*
- `GET /rest/getPlaylists` *(stub)*
- `GET /rest/getStarred2` *(stub)*

### Search
- `GET /rest/search3?query=…`

### Browsing
- `GET /rest/getArtist?id=<browseId>`
- `GET /rest/getArtistInfo2?id=<browseId>`
- `GET /rest/getAlbum?id=<browseId>`
- `GET /rest/getAlbumInfo2?id=<browseId>`
- `GET /rest/getSong?id=<videoId>`
- `GET /rest/getTopSongs?artist=…`

### Media
- `GET /rest/stream?id=<videoId>`
- `GET /rest/getCoverArt?id=<videoId|browseId>`

### Scrobbling
- `GET /rest/scrobble?id=<videoId>&submission=true`
- `GET /rest/getNowPlaying`
- `GET /rest/getScrobbles`

---

## Notes

- **Authentication**: Token-auth (`t` + `s` params) and plain-password (`p` param) are both supported, matching the Subsonic spec.
- **No persistent music library**: All data is fetched live from YouTube Music on every request.  
  Album/artist browsing only works after a search surfaces the relevant IDs.
- **Geographic restrictions**: Some tracks are region-locked on YouTube.
- **Rate limits**: Heavy use may trigger YouTube's rate-limiting.  Increase `cache_ttl` to reduce requests.

---

*For educational and personal use only.*
