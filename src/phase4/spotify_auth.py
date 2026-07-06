"""
Spotify OAuth Helper
====================
Pure requests-based Spotify OAuth 2.0 Authorization Code flow.
No external Spotify SDK dependency required.

Works in mock mode when credentials are placeholder values.
"""

import os
import base64
import json
import logging
import requests
from urllib.parse import urlencode

logger = logging.getLogger("spotify_auth")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

DEFAULT_SCOPES = [
    "playlist-modify-public",
    "playlist-modify-private",
    "user-read-private",
    "user-read-playback-state",
    "user-read-currently-playing",
    "user-modify-playback-state",
]

# In-memory token store (keyed by session_id)
_token_store: dict[str, dict] = {}

_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "reviews.db")
)


def _ensure_spotify_sessions_table(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS spotify_sessions (
            session_id TEXT PRIMARY KEY,
            token_json TEXT NOT NULL,
            display_name TEXT,
            updated_at TEXT NOT NULL
        )
    """)


def _persist_token(session_id: str, token_data: dict, display_name: str | None = None) -> None:
    import sqlite3
    from datetime import datetime, timezone

    db_dir = os.path.dirname(_DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(_DB_PATH)
    try:
        _ensure_spotify_sessions_table(conn)
        conn.execute(
            """
            INSERT INTO spotify_sessions (session_id, token_json, display_name, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                token_json = excluded.token_json,
                display_name = COALESCE(excluded.display_name, spotify_sessions.display_name),
                updated_at = excluded.updated_at
            """,
            (
                session_id,
                json.dumps(token_data),
                display_name,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _load_persisted_token(session_id: str) -> dict | None:
    import sqlite3

    if not os.path.exists(_DB_PATH):
        return None

    conn = sqlite3.connect(_DB_PATH)
    try:
        _ensure_spotify_sessions_table(conn)
        row = conn.execute(
            "SELECT token_json FROM spotify_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        return json.loads(row[0])
    except Exception as e:
        logger.warning("Failed to load persisted Spotify token for %s: %s", session_id, e)
        return None
    finally:
        conn.close()


def _load_persisted_display_name(session_id: str) -> str | None:
    import sqlite3

    if not os.path.exists(_DB_PATH):
        return None

    conn = sqlite3.connect(_DB_PATH)
    try:
        _ensure_spotify_sessions_table(conn)
        row = conn.execute(
            "SELECT display_name FROM spotify_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        return row[0]
    finally:
        conn.close()


def _hydrate_session(session_id: str) -> None:
    if session_id in _token_store:
        return
    token = _load_persisted_token(session_id)
    if token:
        _token_store[session_id] = token


def restore_persisted_sessions() -> int:
    """Load all persisted Spotify sessions into memory on startup."""
    import sqlite3

    if not os.path.exists(_DB_PATH):
        return 0

    conn = sqlite3.connect(_DB_PATH)
    try:
        _ensure_spotify_sessions_table(conn)
        rows = conn.execute("SELECT session_id, token_json FROM spotify_sessions").fetchall()
        for session_id, token_json in rows:
            try:
                _token_store[session_id] = json.loads(token_json)
            except json.JSONDecodeError:
                logger.warning("Skipping invalid Spotify token for session %s", session_id)
        return len(rows)
    finally:
        conn.close()


def _is_mock_mode() -> bool:
    """Check if Spotify credentials are placeholder values."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
    return not client_id or client_id.startswith("your_") or os.getenv("WORKSPACE_MODE") == "offline"



# ---------------------------------------------------------------------------
# OAuth Flow & Token Management
# ---------------------------------------------------------------------------
def get_auth_url(session_id: str, redirect_uri: str = None) -> str:
    """
    Build the Spotify authorization URL.

    Args:
        session_id: Unique session identifier (used as state param).
        redirect_uri: OAuth redirect URI.

    Returns:
        Authorization URL string.
    """
    if _is_mock_mode():
        return f"http://localhost:8081/api/v1/spotify/callback?code=mock_code_12345&state={session_id}"

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    redirect_uri = redirect_uri or os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8000/callback")

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(DEFAULT_SCOPES),
        "state": session_id,
        "show_dialog": "true",
    }
    return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str, session_id: str, redirect_uri: str = None) -> dict:
    """
    Exchange an authorization code for access and refresh tokens.

    Args:
        code: Authorization code from Spotify callback.
        session_id: Session identifier.
        redirect_uri: Must match the redirect_uri used in get_auth_url.

    Returns:
        Token dict with access_token, refresh_token, expires_in.
    """
    if _is_mock_mode() or code.startswith("mock_"):
        mock_token = {
            "access_token": "mock_access_token_BQDj3xK9e5Wd2m",
            "refresh_token": "mock_refresh_token_AQArlj7h5s2b",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": " ".join(DEFAULT_SCOPES),
        }
        import time
        mock_token["expires_at"] = time.time() + 3600
        _token_store[session_id] = mock_token
        _persist_token(session_id, mock_token, display_name="Discovery Demo User")
        logger.info("Mock Spotify token stored for session %s", session_id)
        return mock_token

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = redirect_uri or os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8000/callback")

    # Base64 encode client credentials
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    resp = requests.post(
        SPOTIFY_TOKEN_URL,
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
        timeout=10,
    )
    resp.raise_for_status()
    token_data = resp.json()
    import time
    token_data["expires_at"] = time.time() + token_data.get("expires_in", 3600)
    _token_store[session_id] = token_data

    display_name = None
    try:
        user_resp = requests.get(
            f"{SPOTIFY_API_BASE}/me",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
            timeout=10,
        )
        if user_resp.ok:
            display_name = user_resp.json().get("display_name") or user_resp.json().get("id")
    except Exception as e:
        logger.warning("Could not fetch Spotify profile for session %s: %s", session_id, e)

    _persist_token(session_id, token_data, display_name=display_name)
    logger.info("Spotify token stored for session %s", session_id)
    return token_data


def refresh_access_token(session_id: str) -> dict | None:
    """Refresh the Spotify access token using the stored refresh token."""
    token = _token_store.get(session_id)
    if not token or _is_mock_mode():
        return token

    refresh_token_str = token.get("refresh_token")
    if not refresh_token_str:
        logger.warning("No refresh token found for session %s", session_id)
        return None

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    try:
        resp = requests.post(
            SPOTIFY_TOKEN_URL,
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token_str,
            },
            timeout=10,
        )
        resp.raise_for_status()
        new_token_data = resp.json()
        
        # Merge new token data into existing token data
        token.update(new_token_data)
        import time
        token["expires_at"] = time.time() + new_token_data.get("expires_in", 3600)
        
        _token_store[session_id] = token
        _persist_token(session_id, token, display_name=_load_persisted_display_name(session_id))
        logger.info("Successfully refreshed Spotify token for session %s", session_id)
        return token
    except Exception as e:
        logger.error("Failed to refresh Spotify token for session %s: %s", session_id, e)
        return None


def get_valid_token(session_id: str) -> str | None:
    """Get a valid access token, refreshing it if expired."""
    _hydrate_session(session_id)
    token = _token_store.get(session_id)
    if not token:
        return None

    if _is_mock_mode():
        return token.get("access_token")

    import time
    # If expired or expiring in less than 60 seconds
    if token.get("expires_at", 0) - time.time() < 60:
        refreshed = refresh_access_token(session_id)
        if refreshed:
            return refreshed.get("access_token")
        return None

    return token.get("access_token")


def get_token(session_id: str) -> dict | None:
    """Retrieve stored token for a session."""
    return _token_store.get(session_id)


def is_authenticated(session_id: str) -> bool:
    """Check if a session has a valid token."""
    return get_valid_token(session_id) is not None


def get_session_display_name(session_id: str) -> str | None:
    """Return the cached Spotify display name for a connected session."""
    _hydrate_session(session_id)
    if not is_authenticated(session_id):
        return None
    return _load_persisted_display_name(session_id)


# ---------------------------------------------------------------------------
# Spotify API Operations
# ---------------------------------------------------------------------------
def get_current_user(session_id: str) -> dict:
    """Get the current user's Spotify profile."""
    access_token = get_valid_token(session_id)
    if not access_token:
        return {"error": "Not authenticated"}

    if _is_mock_mode():
        return {
            "id": "mock_user_spotify",
            "display_name": "Discovery Demo User",
            "email": "demo@spotify-discovery.local",
            "product": "premium",
            "country": "US",
        }

    resp = requests.get(
        f"{SPOTIFY_API_BASE}/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def create_playlist(
    session_id: str,
    name: str,
    description: str = "",
    track_names: list[str] = None,
) -> dict:
    """
    Create a playlist on the user's Spotify account.
    """
    access_token = get_valid_token(session_id)
    if not access_token:
        return {"error": "Not authenticated", "status": "failed"}

    if _is_mock_mode():
        return {
            "status": "success",
            "mode": "mock",
            "playlist_name": name,
            "playlist_url": f"https://open.spotify.com/playlist/mock_{hash(name) % 999999:06d}",
            "tracks_added": len(track_names or []),
            "track_names": track_names or [],
            "message": "Playlist created in mock mode. Configure SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env for live Spotify integration.",
        }

    # Get user ID
    user = get_current_user(session_id)
    user_id = user.get("id")
    if not user_id:
        return {"error": "Could not get user profile", "status": "failed"}

    # Create playlist
    resp = requests.post(
        f"{SPOTIFY_API_BASE}/users/{user_id}/playlists",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "name": name,
            "description": description or f"AI-curated discovery playlist — {name}",
            "public": True,
        },
        timeout=10,
    )
    resp.raise_for_status()
    playlist_data = resp.json()

    return {
        "status": "success",
        "mode": "live",
        "playlist_name": name,
        "playlist_url": playlist_data.get("external_urls", {}).get("spotify", ""),
        "playlist_id": playlist_data.get("id", ""),
        "tracks_added": 0,
        "message": "Playlist created successfully on your Spotify account!",
    }


def search_spotify_tracks(session_id: str, query: str, limit: int = 5) -> list[dict]:
    """
    Search for tracks on Spotify to find URIs for playlist addition.
    """
    try:
        access_token = get_valid_token(session_id)
    except Exception as e:
        logger.warning("Failed to retrieve valid Spotify token for session %s: %s", session_id, e)
        access_token = None

    if not access_token or _is_mock_mode():
        return [{
            "uri": f"spotify:track:mock_{hash(query) % 999999:06d}",
            "name": query.split(" by ")[0] if " by " in query else query,
            "artist": query.split(" by ")[1] if " by " in query else "Unknown Artist",
            "preview_url": None,
        }]

    try:
        resp = requests.get(
            f"{SPOTIFY_API_BASE}/search",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"q": query, "type": "track", "limit": limit},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        tracks = []
        for item in data.get("tracks", {}).get("items", []):
            tracks.append({
                "uri": item["uri"],
                "name": item["name"],
                "artist": ", ".join(a["name"] for a in item["artists"]),
                "album": item.get("album", {}).get("name", ""),
                "preview_url": item.get("preview_url"),
            })
        return tracks
    except Exception as e:
        logger.warning("Spotify API search failed, falling back to mock: %s", e)
        return [{
            "uri": f"spotify:track:mock_{hash(query) % 999999:06d}",
            "name": query.split(" by ")[0] if " by " in query else query,
            "artist": query.split(" by ")[1] if " by " in query else "Unknown Artist",
            "preview_url": None,
        }]

def get_client_credentials_token() -> str | None:
    """Retrieve an access token using Client Credentials Flow (no user sign-in needed)."""
    if _is_mock_mode():
        return "mock_client_credentials_token_12345"

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        logger.warning("Spotify client credentials missing in environment.")
        return None

    try:
        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        resp = requests.post(
            SPOTIFY_TOKEN_URL,
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
            timeout=10,
        )
        resp.raise_for_status()
        token_data = resp.json()
        return token_data.get("access_token")
    except Exception as e:
        logger.error("Failed to retrieve Spotify client credentials token: %s", e)
        return None

def get_real_client_credentials_token() -> str | None:
    """Retrieve a real Spotify client credentials access token, bypassing mock mode checks."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or client_id.startswith("your_") or not client_secret:
        return None
    try:
        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        resp = requests.post(
            SPOTIFY_TOKEN_URL,
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception as e:
        logger.error("Failed to retrieve real client credentials token: %s", e)
        return None

