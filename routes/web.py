from flask import Blueprint, render_template_string

web_bp = Blueprint('web', __name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Music Player</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { text-align: center; padding: 40px 0; }
        h1 { font-size: 3em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .search-box {
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            margin-bottom: 30px;
        }
        .search-input {
            width: 100%;
            padding: 15px 20px;
            font-size: 1.1em;
            border: none;
            border-radius: 25px;
            outline: none;
        }
        .tabs { display: flex; gap: 10px; margin: 20px 0; }
        .tab {
            padding: 10px 20px;
            background: rgba(255,255,255,0.2);
            border: none;
            border-radius: 20px;
            color: white;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
        }
        .tab.active, .tab:hover { background: rgba(255,255,255,0.4); }
        .results {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .item {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            cursor: pointer;
            transition: all 0.3s;
        }
        .item:hover {
            background: rgba(255,255,255,0.2);
            transform: translateY(-5px);
        }
        .item img { width: 100%; border-radius: 8px; margin-bottom: 10px; }
        .item-title { font-weight: bold; margin-bottom: 5px; }
        .item-artist { font-size: 0.9em; opacity: 0.8; }
        .player {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(0,0,0,0.9);
            backdrop-filter: blur(20px);
            padding: 20px;
            display: none;
        }
        .player.active { display: block; }
        .player-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .player-info { flex: 1; }
        .player-title { font-weight: bold; font-size: 1.1em; }
        .player-artist { opacity: 0.7; }
        .player-controls { display: flex; gap: 15px; align-items: center; }
        .control-btn {
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2em;
            transition: all 0.3s;
        }
        .control-btn:hover { background: rgba(255,255,255,0.4); }
        .loading { text-align: center; padding: 40px; font-size: 1.2em; }
        audio { width: 300px; }
    </style>
</head>
<body>
    <div class="container">
        <header><h1>🎵 YouTube Music Player</h1></header>
        <div class="search-box">
            <input type="text" class="search-input" id="searchInput" placeholder="Hledat skladby, interprety, alba...">
            <div class="tabs">
                <button class="tab active" data-type="songs">Skladby</button>
                <button class="tab" data-type="artists">Interpreti</button>
                <button class="tab" data-type="albums">Alba</button>
                <button class="tab" data-type="playlists">Playlisty</button>
            </div>
        </div>
        <div id="results" class="results"></div>
        <div id="loading" class="loading" style="display:none;">Načítání...</div>
    </div>
    <div class="player" id="player">
        <div class="player-content">
            <div class="player-info">
                <div class="player-title" id="playerTitle">-</div>
                <div class="player-artist" id="playerArtist">-</div>
            </div>
            <div class="player-controls">
                <button class="control-btn" onclick="playPause()">⏯</button>
                <audio id="audio" controls></audio>
            </div>
        </div>
    </div>
    <script>
        let searchTimeout, currentType = 'songs';
        const searchInput = document.getElementById('searchInput');
        const resultsDiv = document.getElementById('results');
        const loadingDiv = document.getElementById('loading');
        const playerDiv = document.getElementById('player');
        const audio = document.getElementById('audio');
        
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                currentType = tab.dataset.type;
                if (searchInput.value) search(searchInput.value);
            });
        });
        
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => search(e.target.value), 500);
        });
        
        async function search(query) {
            if (!query) { resultsDiv.innerHTML = ''; return; }
            loadingDiv.style.display = 'block';
            resultsDiv.innerHTML = '';
            try {
                const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&type=${currentType}`);
                const data = await response.json();
                loadingDiv.style.display = 'none';
                displayResults(data.results);
            } catch (error) {
                loadingDiv.style.display = 'none';
                resultsDiv.innerHTML = '<p>Chyba při hledání</p>';
            }
        }
        
        function displayResults(results) {
            if (!results || results.length === 0) {
                resultsDiv.innerHTML = '<p>Žádné výsledky</p>';
                return;
            }
            resultsDiv.innerHTML = results.map(item => {
                const thumbnail = item.thumbnails?.[0]?.url || '';
                const title = item.title || item.name || 'Bez názvu';
                const artist = item.artists?.[0]?.name || item.artist || '';
                return `
                    <div class="item" onclick='playTrack(${JSON.stringify(item)})'>
                        ${thumbnail ? `<img src="${thumbnail}" alt="${title}">` : ''}
                        <div class="item-title">${title}</div>
                        <div class="item-artist">${artist}</div>
                    </div>
                `;
            }).join('');
        }
        
        async function playTrack(track) {
            if (!track.videoId) { alert('Nelze přehrát'); return; }
            try {
                const response = await fetch(`/api/stream/${track.videoId}`);
                const data = await response.json();
                if (data.url) {
                    audio.src = data.url;
                    audio.play();
                    document.getElementById('playerTitle').textContent = track.title || 'Bez názvu';
                    document.getElementById('playerArtist').textContent = track.artists?.[0]?.name || '';
                    playerDiv.classList.add('active');
                }
            } catch (error) { alert('Chyba při přehrávání'); }
        }
        
        function playPause() {
            if (audio.paused) { audio.play(); } else { audio.pause(); }
        }
    </script>
</body>
</html>
"""

@web_bp.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


