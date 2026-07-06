import os
import json
import math
import sqlite3
from datetime import datetime

CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "mood_config.json")
)
DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "reviews.db")
)

# Global in-memory cache for fast loading
_catalog_cache = {}

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_mood_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Mood configuration not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def init_mood_tables():
    """Ensure the new tables are created in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create songs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS songs (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        artist TEXT NOT NULL,
        album TEXT,
        duration_ms INTEGER,
        valence REAL,
        energy REAL,
        tempo REAL,
        danceability REAL,
        acousticness REAL,
        instrumentalness REAL,
        mood_tags TEXT,
        mood_confidence TEXT,
        popularity INTEGER DEFAULT 50,
        release_year INTEGER,
        description TEXT,
        last_tagged_at TEXT
    )
    """)

    # Create mood_catalogs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mood_catalogs (
        mood TEXT PRIMARY KEY,
        songs TEXT,
        refresh_frequency TEXT,
        personalization_enabled INTEGER
    )
    """)

    # Create user_feedback table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        song_id TEXT NOT NULL,
        mood TEXT NOT NULL,
        feedback_type TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (song_id) REFERENCES songs (id) ON DELETE CASCADE
    )
    """)

    # Create listening_history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS listening_history (
        user_id TEXT NOT NULL,
        song_id TEXT NOT NULL,
        play_count INTEGER DEFAULT 1,
        last_played_at TEXT,
        PRIMARY KEY (user_id, song_id),
        FOREIGN KEY (song_id) REFERENCES songs (id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()

def closeness(value, min_val, max_val, scale=1.0):
    """Calculates how close a value is to a range [min_val, max_val]. Returns 1.0 if inside, 0-1 if outside."""
    if min_val <= value <= max_val:
        return 1.0
    elif value < min_val:
        return max(0.0, 1.0 - (min_val - value) / scale)
    else:
        return max(0.0, 1.0 - (value - max_val) / scale)

def classify_song(song: dict, config: dict, feedback_penalties: dict = None) -> tuple[dict, list[str]]:
    """
    Scores a song against all moods using rule-based thresholds from the config.
    Returns:
        mood_confidence: dict of {mood: float 0-1}
        mood_tags: list of matching mood strings (max 3)
    """
    song_id = song.get("id")
    penalties = feedback_penalties or {}

    valence = float(song.get("valence", 0.5))
    energy = float(song.get("energy", 0.5))
    tempo = float(song.get("tempo", 120))
    danceability = float(song.get("danceability", 0.5))
    acousticness = float(song.get("acousticness", 0.5))
    instrumentalness = float(song.get("instrumentalness", 0.0))
    release_year = int(song.get("release_year", 2020))
    genre = song.get("genre", "").lower()
    description = song.get("description", "").lower()

    confidence_scores = {}

    for mood_key, mood_cfg in config.items():
        if mood_key == "nostalgic":
            # Nostalgic heuristic based on era + genres
            base = 0.3
            if release_year < 1980:
                base = 0.98
            elif release_year < 1990:
                base = 0.95
            elif release_year < 2000:
                base = 0.90
            elif release_year < 2010:
                base = 0.70
            
            # Boost based on genre tags
            if any(w in genre for w in ["old classic", "90s", "80s", "70s", "retro", "nostalgic", "classic"]):
                base = max(base, 0.95)
            
            # Boost based on description
            if any(w in description for w in ["nostalgic", "wistful", "memories", "past", "classic", "retro", "childhood"]):
                base = min(1.0, base + 0.15)
                
            confidence_scores[mood_key] = base
        else:
            # Standard closeness metric for audio features
            feature_scores = []
            
            # Map features to ranges
            features_mapping = {
                "valence": (valence, 0.15),
                "energy": (energy, 0.15),
                "tempo": (tempo, 30.0),
                "danceability": (danceability, 0.15),
                "acousticness": (acousticness, 0.15),
                "instrumentalness": (instrumentalness, 0.15)
            }

            for f_name, (val, scale) in features_mapping.items():
                range_key = f"{f_name}_range"
                if range_key in mood_cfg:
                    r_min, r_max = mood_cfg[range_key]
                    # Only include features that are actually constrained (not [0.0, 1.0] or equivalent)
                    if (f_name in ["valence", "energy", "danceability", "acousticness", "instrumentalness"] and (r_min > 0.0 or r_max < 1.0)) or \
                       (f_name == "tempo" and (r_min > 0 or r_max < 250)):
                        feature_scores.append(closeness(val, r_min, r_max, scale))
            
            if feature_scores:
                confidence_scores[mood_key] = sum(feature_scores) / len(feature_scores)
            else:
                confidence_scores[mood_key] = 0.5

        # Apply feedback penalties (drop confidence by 0.2 per negative feedback)
        neg_count = penalties.get((song_id, mood_key), 0)
        if neg_count > 0:
            confidence_scores[mood_key] = max(0.0, confidence_scores[mood_key] - (neg_count * 0.2))

    # Determine tags: filter >= 0.55 confidence and cap at 3
    valid_moods = [(m, score) for m, score in confidence_scores.items() if score >= 0.55]
    valid_moods.sort(key=lambda x: x[1], reverse=True)
    tags = [m for m, _ in valid_moods[:3]]

    # Ensure hook for ML classifier swap
    ml_tags = _classify_mood_ml_hook(song)
    if ml_tags:
        # If ML hook returned tags in a future implementation, merge them
        pass

    return confidence_scores, tags

def _classify_mood_ml_hook(song: dict) -> list[str]:
    """Hook for swapping in an ML-based classifier in the future."""
    # Returns None for now (inactive fallback to rule-based)
    return None

def rebuild_mood_catalogs(conn=None):
    """
    Batch job that calculates mood confidence for all songs,
    saves the tags and confidence to SQLite, and updates `mood_catalogs`
    by ranking them. Caches the result in memory.
    """
    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True

    # Ensure row factory is set to Row for dictionary row conversion
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()
        config = load_mood_config()

        # 1. Fetch negative feedback counts
        cursor.execute("SELECT song_id, mood, COUNT(*) as count FROM user_feedback WHERE feedback_type = 'negative' GROUP BY song_id, mood")
        feedback_penalties = {}
        for row in cursor.fetchall():
            feedback_penalties[(row["song_id"], row["mood"])] = row["count"]

        # 2. Fetch all songs
        cursor.execute("SELECT * FROM songs")
        songs = [dict(r) for r in cursor.fetchall()]

        if not songs:
            print("No songs found in the database. Seeding tracks required.")
            return

        # 3. Classify all songs and save confidence
        now_str = datetime.now().isoformat()
        updated_songs = []
        for song in songs:
            scores, tags = classify_song(song, config, feedback_penalties)
            
            # Save back to SQLite
            cursor.execute("""
            UPDATE songs
            SET mood_tags = ?, mood_confidence = ?, last_tagged_at = ?
            WHERE id = ?
            """, (json.dumps(tags), json.dumps(scores), now_str, song["id"]))
            
            song_copy = dict(song)
            song_copy["mood_tags"] = tags
            song_copy["mood_confidence"] = scores
            song_copy["last_tagged_at"] = now_str
            updated_songs.append(song_copy)

        conn.commit()

        # 4. Generate catalogs
        new_cache = {}
        for mood in config.keys():
            # Get songs tagged with this mood
            mood_songs = [s for s in updated_songs if mood in s["mood_tags"]]
            
            # CRITICAL REQUIREMENT: If less than 50 songs are tagged, fallback by taking the top 50 highest confidence scores for this mood!
            if len(mood_songs) < 50 and len(updated_songs) >= 50:
                # Rank all songs by confidence for this mood
                all_sorted_by_conf = sorted(updated_songs, key=lambda s: s["mood_confidence"].get(mood, 0.0), reverse=True)
                mood_songs = all_sorted_by_conf[:50]
            elif len(mood_songs) < 50:
                # If we don't even have 50 songs total, take all of them
                mood_songs = updated_songs

            # Rank songs per mood by mood_confidence (60%), popularity (20%), and release_year/recency (20%)
            ranked_songs = []
            for s in mood_songs:
                conf = s["mood_confidence"].get(mood, 0.5)
                pop = float(s.get("popularity", 50)) / 100.0
                year = float(s.get("release_year", 2020))
                # Recency factor normalized between 1950 and 2026
                recency = max(0.0, min(1.0, (year - 1950) / (2026 - 1950)))
                
                score = (conf * 0.6) + (pop * 0.2) + (recency * 0.2)
                ranked_songs.append((s, score))
            
            # Sort by ranking score descending
            ranked_songs.sort(key=lambda x: x[1], reverse=True)
            sorted_songs_list = [x[0] for x in ranked_songs]
            
            # Store in DB
            song_ids = [s["id"] for s in sorted_songs_list]
            cursor.execute("""
            INSERT INTO mood_catalogs (mood, songs, refresh_frequency, personalization_enabled)
            VALUES (?, ?, 'daily', 1)
            ON CONFLICT(mood) DO UPDATE SET songs=excluded.songs
            """, (mood, json.dumps(song_ids)))
            
            new_cache[mood] = sorted_songs_list

        conn.commit()
        
        # Update global memory cache
        global _catalog_cache
        _catalog_cache = new_cache
        print(f"Successfully rebuilt all 8 mood catalogs. Cached {len(_catalog_cache)} catalogs in memory.")

    finally:
        if own_conn:
            conn.close()

def get_moods_list():
    """Returns available moods list with metadata and styles."""
    config = load_mood_config()
    moods = []
    for k, v in config.items():
        moods.append({
            "id": k,
            "name": v["name"],
            "description": v["description"],
            "gradient": v["gradient"],
            "text_color": v.get("text_color", "#ffffff")
        })
    return moods

def get_mood_catalog(mood: str, limit: int = 50, offset: int = 0, personalized: bool = False, session_id: str = "default_user") -> list[dict]:
    """
    Retrieves the paginated catalog list for a mood, with optional dynamic personalization re-ranking.
    """
    global _catalog_cache
    if mood not in _catalog_cache:
        # Load from DB fallback
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT songs FROM mood_catalogs WHERE mood = ?", (mood,))
        row = cursor.fetchone()
        if row:
            song_ids = json.loads(row["songs"])
            # Fetch song details
            placeholders = ",".join("?" for _ in song_ids)
            cursor.execute(f"SELECT * FROM songs WHERE id IN ({placeholders})", song_ids)
            db_songs = {r["id"]: dict(r) for r in cursor.fetchall()}
            
            # Resolve JSON fields
            songs_list = []
            for s_id in song_ids:
                if s_id in db_songs:
                    s = db_songs[s_id]
                    s["mood_tags"] = json.loads(s.get("mood_tags", "[]"))
                    s["mood_confidence"] = json.loads(s.get("mood_confidence", "{}"))
                    songs_list.append(s)
            _catalog_cache[mood] = songs_list
            conn.close()
        else:
            conn.close()
            # Cache empty or rebuild
            rebuild_mood_catalogs()
            
    catalog = _catalog_cache.get(mood, [])

    if personalized:
        # 1. Fetch user listening history
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT song_id, play_count FROM listening_history WHERE user_id = ?", (session_id,))
        history = {row["song_id"]: row["play_count"] for row in cursor.fetchall()}
        
        # 2. Fetch artists the user listens to
        user_artists = {}
        if history:
            placeholders = ",".join("?" for _ in history.keys())
            cursor.execute(f"SELECT id, artist FROM songs WHERE id IN ({placeholders})", list(history.keys()))
            for row in cursor.fetchall():
                artist = row["artist"]
                play_cnt = history.get(row["id"], 0)
                user_artists[artist] = user_artists.get(artist, 0) + play_cnt
        conn.close()

        if history:
            # Re-rank on the fly
            ranked = []
            for s in catalog:
                # Start with base score from cache ranking
                # Re-calculate default catalog score
                conf = s["mood_confidence"].get(mood, 0.5)
                pop = float(s.get("popularity", 50)) / 100.0
                year = float(s.get("release_year", 2020))
                recency = max(0.0, min(1.0, (year - 1950) / (2026 - 1950)))
                base_score = (conf * 0.6) + (pop * 0.2) + (recency * 0.2)
                
                # Boost if song in history
                song_boost = 0.0
                play_cnt = history.get(s["id"], 0)
                if play_cnt > 0:
                    song_boost = 0.20 * math.log1p(play_cnt)
                
                # Boost if artist in history
                artist_boost = 0.0
                artist_play_cnt = user_artists.get(s["artist"], 0)
                if artist_play_cnt > 0:
                    artist_boost = 0.10 * math.log1p(artist_play_cnt)
                
                final_score = base_score + song_boost + artist_boost
                ranked.append((s, final_score))
            
            # Sort by personalized score descending
            ranked.sort(key=lambda x: x[1], reverse=True)
            catalog = [x[0] for x in ranked]

    # Paginate
    return catalog[offset:offset+limit]

def log_mood_feedback(song_id: str, mood: str, feedback_type: str = "negative"):
    """
    Logs user feedback on a mood-song pair.
    Triggers an immediate re-classification of the song and re-ranks the affected mood catalog
    so the changes take effect immediately in the UI.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Insert feedback record
    now_str = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO user_feedback (song_id, mood, feedback_type, created_at)
    VALUES (?, ?, ?, ?)
    """, (song_id, mood, feedback_type, now_str))
    conn.commit()

    # 2. Re-run catalog rebuild to update database and memory cache
    rebuild_mood_catalogs(conn)
    conn.close()

def log_simulated_play(user_id: str, song_id: str):
    """Logs a play event for personalization testing."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO listening_history (user_id, song_id, play_count, last_played_at)
    VALUES (?, ?, 1, ?)
    ON CONFLICT(user_id, song_id) DO UPDATE SET play_count = play_count + 1, last_played_at = excluded.last_played_at
    """, (user_id, song_id, now_str))
    conn.commit()
    conn.close()
