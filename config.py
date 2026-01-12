import secrets

# Autentizační konfigurace
USERS = {
    "admin": {
        "password": "admin",
        "salt": secrets.token_hex(16),
        "token": secrets.token_hex(32)
    }
}

# YouTube Music konfigurace
YTMUSIC_LANGUAGE = "cs"
YTMUSIC_LOCATION = "CZ"

