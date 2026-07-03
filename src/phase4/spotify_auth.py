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
]

# In-memory token store (keyed by session_id)
_token_store: dict[str, dict] = {}


def _is_mock_mode() -> bool:
    """Check if Spotify credentials are placeholder values."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
    return not client_id or client_id.startswith("your_")


# ---------------------------------------------------------------------------
# OAuth Flow
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
        _token_store[session_id] = mock_token
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
    _token_store[session_id] = token_data
    logger.info("Spotify token stored for session %s", session_id)
    return token_data


def get_token(session_id: str) -> dict | None:
    """Retrieve stored token for a session."""
    return _token_store.get(session_id)


def is_authenticated(session_id: str) -> bool:
    """Check if a session has a valid token."""
    return session_id in _token_store


# ---------------------------------------------------------------------------
# Spotify API Operations
# ---------------------------------------------------------------------------
def get_current_user(session_id: str) -> dict:
    """Get the current user's Spotify profile."""
    token = _token_store.get(session_id)
    if not token:
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
        headers={"Authorization": f"Bearer {token['access_token']}"},
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

    Args:
        session_id: Session with stored Spotify token.
        name: Playlist name.
        description: Playlist description.
        track_names: List of track names (for mock mode / display).

    Returns:
        Playlist creation result with url and track count.
    """
    token = _token_store.get(session_id)
    if not token:
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
            "Authorization": f"Bearer {token['access_token']}",
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

    Args:
        session_id: Session with stored Spotify token.
        query: Search query (usually "track_name artist").
        limit: Max results per search.

    Returns:
        List of simplified track dicts with uri, name, artist.
    """
    token = _token_store.get(session_id)
    if not token or _is_mock_mode():
        return [{
            "uri": f"spotify:track:mock_{hash(query) % 999999:06d}",
            "name": query.split(" by ")[0] if " by " in query else query,
            "artist": query.split(" by ")[1] if " by " in query else "Unknown Artist",
            "preview_url": None,
        }]

    resp = requests.get(
        f"{SPOTIFY_API_BASE}/search",
        headers={"Authorization": f"Bearer {token['access_token']}"},
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
