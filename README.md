# YouTube Music Web Aplikace s OpenSubsonic API

Webová aplikace pro streamování hudby z YouTube Music s podporou OpenSubsonic API pro integraci s Music Assistant.

## Funkce

- 🎵 Vyhledávání skladeb, interpretů, alb a playlistů
- 🎧 Přehrávání hudby přímo z YouTube Music
- 📱 Responzivní webové rozhraní
- 🔌 OpenSubsonic API pro Music Assistant
- 🚫 Bez reklam
- 🔓 Bez potřeby API klíčů nebo přihlášení

## Struktura projektu

```
ytmusic-app/
├── app.py                      # Hlavní aplikace
├── config.py                   # Konfigurace
├── requirements.txt            # Závislosti
├── utils/
│   ├── __init__.py
│   ├── auth.py                 # Autentizace
│   └── subsonic_helper.py      # Subsonic helpers
├── services/
│   ├── __init__.py
│   └── ytmusic_service.py      # YouTube Music služba
└── routes/
    ├── __init__.py
    ├── web.py                  # Web rozhraní
    ├── api.py                  # REST API
    └── subsonic.py             # OpenSubsonic API
```

## Instalace

### 1. Vytvoření struktury adresářů

```bash
mkdir ytmusic-app
cd ytmusic-app
mkdir utils services routes
touch utils/__init__.py services/__init__.py routes/__init__.py
```

### 2. Instalace závislostí

```bash
pip install -r requirements.txt
```

### 3. Spuštění aplikace

```bash
python app.py
```

Aplikace bude dostupná na `http://localhost:5000`

## Připojení do Music Assistant

1. Otevřete Music Assistant
2. Přejděte do Settings → Music Providers
3. Přidejte nový provider typu "Subsonic"
4. Zadejte následující údaje:
   - **Server URL:** `http://localhost:5000/rest` (nebo IP adresu serveru)
   - **Username:** `admin`
   - **Password:** `admin`
5. Uložte a otestujte připojení

## Konfigurace

V souboru `config.py` můžete změnit:

```python
USERS = {
    "admin": {
        "password": "vaše_heslo",
        ...
    }
}
```

## Podporované OpenSubsonic endpointy

- `/rest/ping` - Ping server
- `/rest/getLicense` - Informace o licenci
- `/rest/getMusicFolders` - Seznam hudebních složek
- `/rest/search3` - Vyhledávání
- `/rest/getArtist` - Detail umělce
- `/rest/getAlbum` - Detail alba
- `/rest/getSong` - Detail skladby
- `/rest/stream` - Stream audio
- `/rest/getCoverArt` - Obrázky

## Webové rozhraní

Aplikace obsahuje také webové rozhraní dostupné na `http://localhost:5000` kde můžete:
- Vyhledávat skladby, interprety, alba
- Přehrávat hudbu
- Procházet výsledky

## Požadavky

- Python 3.8+
- Flask
- ytmusicapi
- yt-dlp

## Poznámky

- Aplikace je určena pro osobní použití
- Neobsahuje žádné API klíče - využívá veřejné YouTube Music API
- Streaming může být pomalý v závislosti na rychlosti internetu
- Cover arty jsou stahovány v vysokém rozlišení (600x600px)

## Řešení problémů

### Music Assistant nemůže najít server
- Ujistěte se, že používáte správnou IP adresu
- Zkontrolujte, že port 5000 není blokován firewallem
- Použijte `http://` (ne `https://`)

### Skladby se nepřehrávají
- Zkontrolujte, že máte funkční připojení k internetu
- Některé skladby mohou být geograficky omezené
- Zkuste restartovat aplikaci

### Chyby při vyhledávání
- Zkontrolujte konzoli pro detailní chybové zprávy
- Ujistěte se, že ytmusicapi je správně nainstalováno

## Licence

Projekt je poskytován "tak jak je" pro vzdělávací účely.

## Autor

Vytvořeno pomocí Claude (Anthropic)
