import os
import sqlite3

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "reviews.db")
)

def get_db_connection():
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create reviews table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id TEXT PRIMARY KEY,
        platform TEXT NOT NULL,
        rating INTEGER,
        content TEXT NOT NULL,
        date TEXT NOT NULL,
        user TEXT NOT NULL
    )
    """)
    
    # Create insights table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS insights (
        id TEXT PRIMARY KEY,
        review_id TEXT NOT NULL,
        sentiment TEXT NOT NULL,
        topic TEXT NOT NULL,
        score REAL,
        FOREIGN KEY (review_id) REFERENCES reviews (id) ON DELETE CASCADE
    )
    """)
    
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

    # Persist Spotify OAuth tokens per browser session
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS spotify_sessions (
        session_id TEXT PRIMARY KEY,
        token_json TEXT NOT NULL,
        display_name TEXT,
        updated_at TEXT NOT NULL
    )
    """)

    # Create local_playlists table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS local_playlists (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        tracks TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()
    print("Database tables initialized successfully.")

if __name__ == "__main__":
    init_db()
