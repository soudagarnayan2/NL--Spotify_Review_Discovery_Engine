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
    
    conn.commit()
    conn.close()
    print("Database tables initialized successfully.")

if __name__ == "__main__":
    init_db()
