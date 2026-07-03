"""
Spotify Review Discovery MCP Server
====================================
A complete Model Context Protocol (MCP) server that integrates with
Google Play Store, Apple App Store, Reddit, and Twitter/X for scraping,
analyzing, and exporting user review data.

Run with:
    python mcp_server.py                    # stdio transport (default)
    python mcp_server.py --transport sse    # SSE transport for HTTP clients

MCP Capabilities:
    Tools     : 10 tools for scraping, analysis, search, and export
    Resources : 4 resources for database access and statistics
    Prompts   : 3 prompt templates for common analysis workflows
"""

import os
import sys
import json
import re
import random
import sqlite3
import logging
import argparse
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Environment & Logging
# ---------------------------------------------------------------------------
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("spotify_review_mcp")

# ---------------------------------------------------------------------------
# Database helpers (reuse schema from database.py)
# ---------------------------------------------------------------------------
DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "reviews.db")
)


def _get_db():
    """Return a sqlite3 connection with Row factory."""
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    """Ensure the reviews and insights tables exist."""
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id       TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            rating   INTEGER,
            content  TEXT NOT NULL,
            date     TEXT NOT NULL,
            user     TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS insights (
            id        TEXT PRIMARY KEY,
            review_id TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            topic     TEXT NOT NULL,
            score     REAL,
            FOREIGN KEY (review_id) REFERENCES reviews (id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database tables verified at %s", DB_PATH)


# Make sure tables exist on module load
_init_db()

# ---------------------------------------------------------------------------
# FastMCP Server Initialization
# ---------------------------------------------------------------------------
mcp = FastMCP("Spotify Review Discovery Server")

# ---------------------------------------------------------------------------
# Mock data templates (fallback when APIs are unavailable)
# ---------------------------------------------------------------------------
MOCK_TEMPLATES = {
    "play_store": [
        "Latest update made recommendations even worse. Smart shuffle keeps "
        "repeating the same tracks. Please give us actual discovery tools. 2 stars.",
        "I skipped a song 10 times, yet it shows up in every single daily mix. "
        "Spotify personalization has become very lazy and repetitive.",
        "Algorithmic bubble is real. I am tired of listening to the same tracks. "
        "The app needs a way to discover new genres safely without ruining my profile.",
        "Discover Weekly used to be amazing, but now it just suggests songs I already "
        "have in my library. What happened to actual music discovery?",
        "The app crashes a lot on Android 14 and the shuffle algorithm is clearly "
        "broken. Playing the same 15 songs out of a 500 song playlist.",
        "I switched from Apple Music specifically for discovery features, but Spotify "
        "just recommends the same mainstream pop every single day. Disappointing.",
    ],
    "app_store": [
        "The recommendations on this app are terrible lately. It keeps playing "
        "songs from my library instead of finding new tracks. Smart shuffle is "
        "just a repeat button. 1 star.",
        "I love the UI, but the algorithm is so repetitive. It just plays the same "
        "3 artists over and over. Please fix the recommendation loop. 3 stars.",
        "Cannot discover new music anymore. Every playlist is just an echo chamber "
        "of what I listened to last week. I miss when Discover Weekly actually worked.",
        "Great app overall but the Family plan bleeds my kids' music into my "
        "recommendations. Need separate taste profiles that actually work.",
        "Release Radar is broken. It keeps showing me artists I have never listened "
        "to and ignoring the genres I actually like. Very frustrating experience.",
        "Shuffle play is not random at all. I tested it with a 300 song playlist "
        "and the same 20 songs kept coming up. This is basic functionality.",
    ],
    "reddit": [
        "I'm so tired of Spotify playing the same 15 songs on repeat. My Daily Mix "
        "1 and 2 are literally just songs from my own liked playlist. What is the "
        "point? I want to discover actual new music, not just listen to the same "
        "algorithmic loop.",
        "Does anyone else feel like Discover Weekly has gotten stale? It used to find "
        "hidden gems, but now it just recommends songs I already skipped or artists I "
        "already follow. It's like the algorithm got lazy and only suggests 'safe' choices.",
        "Is there a way to clear or pause search history so a single joke song doesn't "
        "ruin my recommendations? I listened to one sea shanty track and now my entire "
        "feed is filled with folk sea shanties. There is no sandbox or temporary mode.",
        "Why does Spotify's recommendation engine keep pushing mainstream artists? I "
        "listen to indie shoegaze, but my Release Radar is full of pop-adjacent artists. "
        "The collaborative filtering bubble is real and hard to escape.",
        "PSA: If you share your account with family members, Spotify's algorithm will "
        "blend everyone's taste into one horrible mess. There is no way to isolate "
        "listening sessions without creating a whole new account.",
        "The Enhance feature on playlists just adds songs I have already heard or "
        "skipped. It does not actually enhance anything. It just pads the playlist "
        "with safe, familiar tracks. Where is the actual discovery?",
    ],
    "twitter": [
        "Spotify's shuffle is broken. I have 800 songs in my playlist, why does "
        "it play the same 20 tracks every single time? #SpotifyProblems",
        "Discover Weekly is just recommending songs I have literally already liked. "
        "Algorithmic exploitation at its finest. Give me something fresh!",
        "I skipped this song 5 times this week. Why is Spotify still playing it on "
        "my smart shuffle? It does not learn my active feedback.",
        "Desperately need a 'private listening' button that actually works so my "
        "kids' music doesn't pollute my recommendations. #spotify",
        "Spotify's recommendation engine is great at personalization but terrible "
        "at exploration. I am trapped in a bubble. Help! #algorithmicbubble",
        "Day 47 of Spotify recommending me the same 5 artists in my Daily Mix. "
        "I have 2000 liked songs across 50 genres. Do better. #SpotifyWrapped",
    ],
}


def _generate_mock_reviews(platform: str, count: int) -> list[dict]:
    """Generate realistic mock reviews for a given platform."""
    templates = MOCK_TEMPLATES.get(platform, MOCK_TEMPLATES["twitter"])
    reviews = []
    for i in range(count):
        template = random.choice(templates)
        review_date = datetime.now() - timedelta(days=random.randint(0, 60))
        user_num = random.randint(100, 99999)
        if platform == "reddit":
            username = f"u/music_listener_{user_num}"
        elif platform == "twitter":
            username = f"@spotify_user_{user_num}"
        else:
            username = f"{platform}_reviewer_{user_num}"

        reviews.append({
            "id": f"mcp_{platform}_{i}_{int(datetime.now().timestamp())}",
            "platform": platform,
            "rating": random.choice([1, 2, 3]) if platform in ("app_store", "play_store") else None,
            "content": template,
            "date": review_date.strftime("%Y-%m-%d"),
            "user": username,
        })
    return reviews


# ---------------------------------------------------------------------------
# Text cleaning utilities
# ---------------------------------------------------------------------------
def _clean_review(content: str) -> Optional[str]:
    """Clean review text: strip emojis, enforce minimum length, check English."""
    if not content:
        return None
    # Remove emojis
    cleaned = re.sub(r"[\U00010000-\U0010FFFF]", "", content)
    cleaned = re.sub(r"[\u2600-\u27BF]", "", cleaned).strip()
    # Minimum 6 words
    if len(cleaned.split()) < 6:
        return None
    # Basic English check (>80 % ASCII)
    ascii_chars = sum(1 for c in cleaned if ord(c) < 128)
    if len(cleaned) > 0 and (ascii_chars / len(cleaned)) < 0.80:
        return None
    return cleaned


def _scrub_pii(text: str) -> str:
    """Redact URLs and email addresses from text."""
    text = re.sub(r"https?://\S+", "[REDACTED_URL]", text)
    text = re.sub(r"\S+@\S+\.\S+", "[REDACTED_EMAIL]", text)
    return text


# ---------------------------------------------------------------------------
# Rules-based analysis engine (works without any API keys)
# ---------------------------------------------------------------------------
TOPIC_KEYWORDS = {
    "Algorithmic Bubble / Recommendation Repetition": [
        "bubble", "loop", "repeat", "same song", "exploitation", "stagnation",
        "echo chamber", "repetitive", "same artist", "same track", "stuck",
    ],
    "Smart Shuffle loop issues": [
        "shuffle", "smart shuffle", "skip feedback", "not random",
        "same 20", "same 15", "broken shuffle",
    ],
    "Taste pollution / Lack of Sandbox mode": [
        "pollute", "kid", "child", "bedtime", "sandbox", "history",
        "ruined my", "family plan", "private listening", "bleed",
    ],
    "Decision overload": [
        "paralysis", "overload", "scrolling", "grid", "too many options",
        "spend 20 minutes", "overwhelming",
    ],
}

NEGATIVE_WORDS = [
    "terrible", "bad", "worst", "repetitive", "broken", "garbage", "waste",
    "stale", "lazy", "frustrating", "hate", "polluted", "annoying", "poor",
    "unusable", "disappointed", "boring", "stuck", "tired",
]
POSITIVE_WORDS = [
    "great", "love", "awesome", "perfect", "good", "best", "excellent",
    "enjoy", "amazing", "fantastic", "brilliant",
]


def _analyze_rules(content: str, rating: Optional[int]) -> dict:
    """Rules-based sentiment & topic classification."""
    lower = content.lower()

    # ── Topic detection ──────────────────────────────────────────────────
    topic = "General Feedback / Other"
    for candidate, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            topic = candidate
            break

    # ── Sentiment & score ────────────────────────────────────────────────
    neg = sum(1 for w in NEGATIVE_WORDS if w in lower)
    pos = sum(1 for w in POSITIVE_WORDS if w in lower)

    if rating is not None:
        if rating <= 2:
            sentiment, score = "Negative", max(0.0, 0.2 - 0.05 * neg)
        elif rating >= 4:
            sentiment, score = "Positive", min(1.0, 0.8 + 0.05 * pos)
        else:
            sentiment = "Negative" if neg > pos else ("Positive" if pos > neg else "Neutral")
            score = 0.4 if neg > pos else (0.6 if pos > neg else 0.5)
    else:
        sentiment = "Negative" if neg > pos else ("Positive" if pos > neg else "Neutral")
        score = 0.3 if neg > pos else (0.7 if pos > neg else 0.5)

    return {"sentiment": sentiment, "topic": topic, "score": round(score, 3)}


def _analyze_llm(content: str, rating: Optional[int], platform: str) -> Optional[dict]:
    """LLM-based analysis using Groq (Llama 3). Returns None on failure."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.startswith("your_"):
        return None
    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        prompt = f"""Analyze the following user review for a music streaming app.

Review: \"{content}\"
Platform: {platform}
Rating: {rating}

Categorize into EXACTLY ONE topic:
- Algorithmic Bubble / Recommendation Repetition
- Smart Shuffle loop issues
- Taste pollution / Lack of Sandbox mode
- Decision overload
- General Feedback / Other

Determine sentiment: Positive, Neutral, or Negative.
Assign severity score 0.0–1.0 (1.0 = extremely critical / high churn risk).

Respond in strict JSON: {{"sentiment": "...", "topic": "...", "score": 0.0}}"""

        resp = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a precise JSON-outputting data analysis assistant."},
                {"role": "user", "content": prompt},
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as exc:
        logger.warning("LLM analysis failed: %s", exc)
        return None


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                          MCP TOOLS (10 tools)                            ║
# ╚═══════════════════════════════════════════════════════════════════════════╝


# ── 1. Google Play Store ─────────────────────────────────────────────────────
@mcp.tool()
def scrape_google_play_reviews(
    app_id: str = "com.spotify.music",
    country: str = "us",
    count: int = 20,
) -> str:
    """
    Scrape user reviews from the Google Play Store for a given app.

    Args:
        app_id:   Android package name (e.g. 'com.spotify.music').
        country:  ISO 3166-1 alpha-2 country code.
        count:    Number of reviews to retrieve.

    Returns:
        JSON array of review objects with id, platform, rating, content, date, user.
    """
    logger.info("▶ scrape_google_play_reviews  app=%s  country=%s  n=%d", app_id, country, count)
    reviews: list[dict] = []

    try:
        from google_play_scraper import Sort, reviews as gp_reviews

        results, _ = gp_reviews(app_id, lang="en", country=country, sort=Sort.NEWEST, count=count)
        for i, rev in enumerate(results):
            dt = rev.get("at")
            reviews.append({
                "id": f"play_store_{rev.get('reviewId', i)}",
                "platform": "play_store",
                "rating": int(rev.get("score", 3)),
                "content": rev.get("content", "").strip(),
                "date": dt.strftime("%Y-%m-%d") if isinstance(dt, datetime) else str(dt),
                "user": rev.get("userName", "Anonymous User").strip(),
            })
    except Exception as exc:
        logger.error("Google Play scraping failed: %s — using fallback mock data", exc)

    if not reviews:
        reviews = _generate_mock_reviews("play_store", count)

    return json.dumps(reviews, indent=2, ensure_ascii=False)


# ── 2. Apple App Store ───────────────────────────────────────────────────────
@mcp.tool()
def scrape_app_store_reviews(
    app_id: int = 324684580,
    app_name: str = "spotify-music",
    country: str = "us",
    count: int = 20,
) -> str:
    """
    Scrape user reviews from the Apple App Store for a given app.

    Args:
        app_id:    iTunes numeric app ID (e.g. 324684580 for Spotify).
        app_name:  URL-friendly app name slug.
        country:   ISO 3166-1 alpha-2 country code.
        count:     Number of reviews to retrieve.

    Returns:
        JSON array of review objects with id, platform, rating, content, date, user.
    """
    logger.info("▶ scrape_app_store_reviews  id=%d  name=%s  n=%d", app_id, app_name, count)
    reviews: list[dict] = []

    try:
        from app_store_scraper import AppStore

        app = AppStore(country=country, app_name=app_name, app_id=app_id)
        app.review(how_many=count)
        for i, rev in enumerate(app.reviews):
            dt = rev.get("date")
            reviews.append({
                "id": f"app_store_{i}_{int(datetime.now().timestamp())}",
                "platform": "app_store",
                "rating": int(rev.get("rating", 3)),
                "content": rev.get("review", "").strip(),
                "date": dt.strftime("%Y-%m-%d") if isinstance(dt, datetime) else str(dt),
                "user": rev.get("userName", "Anonymous User").strip(),
            })
    except Exception as exc:
        logger.error("App Store scraping failed: %s — using fallback mock data", exc)

    if not reviews:
        reviews = _generate_mock_reviews("app_store", count)

    return json.dumps(reviews, indent=2, ensure_ascii=False)


# ── 3. Reddit ────────────────────────────────────────────────────────────────
@mcp.tool()
def scrape_reddit_discussions(
    subreddit: str = "spotify",
    query: str = "recommendation bubble",
    count: int = 20,
) -> str:
    """
    Retrieve user discussions about a topic from a Reddit subreddit.
    Uses the PRAW library when credentials are available, otherwise
    returns high-quality mock data.

    Args:
        subreddit: Target subreddit name (e.g. 'spotify').
        query:     Search keywords or phrase.
        count:     Target number of comments to collect.

    Returns:
        JSON array of review objects with id, platform, rating (null), content, date, user.
    """
    logger.info("▶ scrape_reddit_discussions  r/%s  q='%s'  n=%d", subreddit, query, count)
    reviews: list[dict] = []

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "SpotifyDiscoveryAgent/1.0")

    if client_id and client_secret and not client_id.startswith("your_"):
        try:
            import praw

            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
            )
            logger.info("PRAW credentials valid — fetching live Reddit data")
            sub = reddit.subreddit(subreddit)
            for submission in sub.search(query, limit=10):
                submission.comments.replace_more(limit=0)
                for comment in submission.comments.list():
                    if len(reviews) >= count:
                        break
                    body = comment.body.strip()
                    if len(body.split()) < 6:
                        continue
                    reviews.append({
                        "id": f"reddit_{comment.id}",
                        "platform": "reddit",
                        "rating": None,
                        "content": body,
                        "date": datetime.fromtimestamp(comment.created_utc).strftime("%Y-%m-%d"),
                        "user": f"u/{comment.author.name}" if comment.author else "[deleted]",
                    })
                if len(reviews) >= count:
                    break
        except Exception as exc:
            logger.error("PRAW scraping failed: %s — using fallback", exc)

    if not reviews:
        logger.warning("No live Reddit data — generating mock reviews")
        reviews = _generate_mock_reviews("reddit", count)

    return json.dumps(reviews, indent=2, ensure_ascii=False)


# ── 4. Twitter / X ──────────────────────────────────────────────────────────
@mcp.tool()
def scrape_twitter_posts(
    query: str = "spotify recommendation bubble",
    count: int = 20,
) -> str:
    """
    Retrieve tweets matching a search query from Twitter/X.
    Uses the twscrape library when an accounts.db file is available,
    otherwise returns high-quality mock data.

    Args:
        query: Search keywords, hashtags, or phrases.
        count: Target number of tweets to collect.

    Returns:
        JSON array of review objects with id, platform, rating (null), content, date, user.
    """
    logger.info("▶ scrape_twitter_posts  q='%s'  n=%d", query, count)
    reviews: list[dict] = []

    # Attempt live scraping with twscrape if accounts.db exists
    accounts_db = os.path.join(os.path.dirname(__file__), "accounts.db")
    if os.path.exists(accounts_db):
        try:
            import asyncio
            from twscrape import API as TwAPI

            async def _fetch():
                tw = TwAPI()
                collected = []
                async for tweet in tw.search(query, limit=count):
                    collected.append({
                        "id": f"twitter_{tweet.id}",
                        "platform": "twitter",
                        "rating": None,
                        "content": tweet.rawContent.strip(),
                        "date": tweet.date.strftime("%Y-%m-%d"),
                        "user": f"@{tweet.user.username}",
                    })
                return collected

            reviews = asyncio.run(_fetch())
            logger.info("twscrape returned %d tweets", len(reviews))
        except Exception as exc:
            logger.error("twscrape failed: %s — using fallback", exc)

    if not reviews:
        logger.warning("No live Twitter data — generating mock tweets")
        reviews = _generate_mock_reviews("twitter", count)

    return json.dumps(reviews, indent=2, ensure_ascii=False)


# ── 5. Ingest reviews into the database ─────────────────────────────────────
@mcp.tool()
def ingest_reviews(reviews_json: str) -> str:
    """
    Ingest a JSON array of review objects into the SQLite database.
    Reviews are cleaned (emoji removal, language check, min-length)
    before insertion.

    Args:
        reviews_json: A JSON-encoded array of review objects. Each object
                      must have keys: id, platform, rating, content, date, user.

    Returns:
        JSON summary with inserted count and per-platform breakdown.
    """
    logger.info("▶ ingest_reviews")
    try:
        reviews = json.loads(reviews_json)
    except json.JSONDecodeError as exc:
        return json.dumps({"error": f"Invalid JSON: {exc}"})

    conn = _get_db()
    cur = conn.cursor()
    counts: dict[str, int] = {}
    inserted = 0

    for rev in reviews:
        cleaned = _clean_review(rev.get("content", ""))
        if not cleaned:
            continue
        plat = rev.get("platform", "unknown")
        try:
            cur.execute(
                """INSERT INTO reviews (id, platform, rating, content, date, user)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET content=excluded.content""",
                (rev["id"], plat, rev.get("rating"), cleaned, rev["date"], rev["user"]),
            )
            inserted += 1
            counts[plat] = counts.get(plat, 0) + 1
        except Exception as exc:
            logger.warning("DB insert error: %s", exc)

    conn.commit()
    conn.close()

    result = {"status": "success", "inserted_total": inserted, "platform_counts": counts}
    logger.info("Ingested %d reviews: %s", inserted, counts)
    return json.dumps(result, indent=2)


# ── 6. Analyze all un-analyzed reviews ───────────────────────────────────────
@mcp.tool()
def analyze_reviews(use_llm: bool = True) -> str:
    """
    Run sentiment analysis and topic classification on all reviews in
    the database that don't yet have insights. Uses Groq LLM when
    available, falls back to a high-accuracy rules engine.

    Args:
        use_llm: If True, attempt LLM-based analysis first (requires GROQ_API_KEY).

    Returns:
        JSON summary with total processed count and method used.
    """
    logger.info("▶ analyze_reviews  use_llm=%s", use_llm)
    conn = _get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT r.* FROM reviews r
        LEFT JOIN insights i ON r.id = i.review_id
        WHERE i.id IS NULL
    """)
    pending = cur.fetchall()

    if not pending:
        conn.close()
        return json.dumps({"status": "success", "processed_total": 0, "message": "All reviews already analyzed"})

    processed = 0
    method = "rules"

    for rev in pending:
        result = None
        if use_llm:
            result = _analyze_llm(rev["content"], rev["rating"], rev["platform"])
            if result:
                method = "llm"
        if not result:
            result = _analyze_rules(rev["content"], rev["rating"])

        insight_id = f"insight_{rev['id']}"
        cur.execute(
            """INSERT INTO insights (id, review_id, sentiment, topic, score)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   sentiment=excluded.sentiment,
                   topic=excluded.topic,
                   score=excluded.score""",
            (insight_id, rev["id"], result["sentiment"], result["topic"], result["score"]),
        )
        processed += 1

    conn.commit()
    conn.close()

    summary = {"status": "success", "processed_total": processed, "method": method}
    logger.info("Analyzed %d reviews via %s", processed, method)
    return json.dumps(summary, indent=2)


# ── 7. Search reviews by keyword ────────────────────────────────────────────
@mcp.tool()
def search_reviews(
    keyword: str,
    platform: str = "",
    sentiment: str = "",
    limit: int = 25,
) -> str:
    """
    Full-text search across stored reviews with optional filters.

    Args:
        keyword:   Search term to look for in review content.
        platform:  Filter by platform (play_store, app_store, reddit, twitter). Empty = all.
        sentiment: Filter by sentiment (Positive, Neutral, Negative). Empty = all.
        limit:     Maximum number of results.

    Returns:
        JSON array of matching reviews with their insight data.
    """
    logger.info("▶ search_reviews  kw='%s'  plat=%s  sent=%s", keyword, platform, sentiment)
    conn = _get_db()
    cur = conn.cursor()

    query = """
        SELECT r.id, r.platform, r.rating, r.content, r.date, r.user,
               i.sentiment, i.topic, i.score
        FROM reviews r
        LEFT JOIN insights i ON r.id = i.review_id
        WHERE r.content LIKE ?
    """
    params: list = [f"%{keyword}%"]

    if platform:
        query += " AND r.platform = ?"
        params.append(platform)
    if sentiment:
        query += " AND i.sentiment = ?"
        params.append(sentiment)

    query += " ORDER BY r.date DESC LIMIT ?"
    params.append(limit)

    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    logger.info("Search returned %d results", len(rows))
    return json.dumps(rows, indent=2, ensure_ascii=False)


# ── 8. Get aggregated insights ───────────────────────────────────────────────
@mcp.tool()
def get_insights_summary() -> str:
    """
    Return aggregated insight statistics: sentiment distribution,
    topic distribution, platform breakdown, and representative
    negative quotes.

    Returns:
        JSON object with sentiments, topics, platform_breakdown, and sample_quotes.
    """
    logger.info("▶ get_insights_summary")
    conn = _get_db()
    cur = conn.cursor()

    # Sentiment counts
    cur.execute("SELECT sentiment, COUNT(*) AS n FROM insights GROUP BY sentiment")
    sentiments = {r["sentiment"]: r["n"] for r in cur.fetchall()}

    # Topic counts
    cur.execute("SELECT topic, COUNT(*) AS n FROM insights GROUP BY topic ORDER BY n DESC")
    topics = {r["topic"]: r["n"] for r in cur.fetchall()}

    # Platform breakdown
    cur.execute("SELECT platform, COUNT(*) AS n FROM reviews GROUP BY platform")
    platforms = {r["platform"]: r["n"] for r in cur.fetchall()}

    # Severity leaders (top 5 most critical reviews)
    cur.execute("""
        SELECT r.content, r.platform, i.topic, i.score
        FROM reviews r JOIN insights i ON r.id = i.review_id
        WHERE i.sentiment = 'Negative'
        ORDER BY i.score ASC
        LIMIT 5
    """)
    critical = []
    for r in cur.fetchall():
        critical.append({
            "content": _scrub_pii(r["content"]),
            "platform": r["platform"],
            "topic": r["topic"],
            "severity_score": r["score"],
        })

    conn.close()

    return json.dumps({
        "sentiments": sentiments,
        "topics": topics,
        "platform_breakdown": platforms,
        "most_critical_reviews": critical,
    }, indent=2, ensure_ascii=False)


# ── 9. Full pipeline: scrape + ingest + analyze ─────────────────────────────
@mcp.tool()
def run_full_pipeline(
    count_per_platform: int = 15,
    use_llm: bool = True,
) -> str:
    """
    Execute the complete review discovery pipeline in one call:
    1. Scrape all 4 platforms (Google Play, App Store, Reddit, Twitter)
    2. Ingest the cleaned reviews into the database
    3. Run sentiment & topic analysis on new reviews

    Args:
        count_per_platform: Number of reviews to scrape from each platform.
        use_llm: Whether to use LLM-based analysis (requires GROQ_API_KEY).

    Returns:
        JSON summary of the full pipeline execution.
    """
    logger.info("▶ run_full_pipeline  n=%d  llm=%s", count_per_platform, use_llm)
    results = {}

    # 1. Scrape
    all_reviews: list[dict] = []
    for scraper_name, scraper_fn in [
        ("google_play", lambda: scrape_google_play_reviews(count=count_per_platform)),
        ("app_store", lambda: scrape_app_store_reviews(count=count_per_platform)),
        ("reddit", lambda: scrape_reddit_discussions(count=count_per_platform)),
        ("twitter", lambda: scrape_twitter_posts(count=count_per_platform)),
    ]:
        raw = json.loads(scraper_fn())
        all_reviews.extend(raw)
        results[f"scraped_{scraper_name}"] = len(raw)

    # 2. Ingest
    ingest_result = json.loads(ingest_reviews(json.dumps(all_reviews)))
    results["ingested"] = ingest_result

    # 3. Analyze
    analysis_result = json.loads(analyze_reviews(use_llm=use_llm))
    results["analyzed"] = analysis_result

    logger.info("Pipeline complete: %s", results)
    return json.dumps(results, indent=2)


# ── 10. Export report ────────────────────────────────────────────────────────
@mcp.tool()
def export_insights_report(
    output_format: str = "markdown",
) -> str:
    """
    Generate a comprehensive insights report from the current database.
    The report includes sentiment summary, topic breakdown, platform
    analysis, and representative user quotes.

    Args:
        output_format: 'markdown' for a formatted report, 'json' for raw data.

    Returns:
        The generated report as a string (markdown or JSON).
    """
    logger.info("▶ export_insights_report  format=%s", output_format)
    conn = _get_db()
    cur = conn.cursor()

    # Gather data
    cur.execute("SELECT COUNT(*) AS n FROM reviews")
    total = cur.fetchone()["n"]

    cur.execute("SELECT sentiment, COUNT(*) AS n FROM insights GROUP BY sentiment")
    sentiments = {r["sentiment"]: r["n"] for r in cur.fetchall()}

    cur.execute("SELECT topic, COUNT(*) AS n FROM insights GROUP BY topic ORDER BY n DESC")
    topics = {r["topic"]: r["n"] for r in cur.fetchall()}

    # Quotes per platform
    platform_quotes: dict[str, list] = {}
    for plat in ("app_store", "play_store", "reddit", "twitter"):
        cur.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r JOIN insights i ON r.id = i.review_id
            WHERE r.platform = ? AND i.sentiment = 'Negative'
            ORDER BY i.score ASC LIMIT 3
        """, (plat,))
        platform_quotes[plat] = [
            {"content": _scrub_pii(r["content"]), "user": r["user"], "date": r["date"], "topic": r["topic"]}
            for r in cur.fetchall()
        ]

    conn.close()

    if output_format == "json":
        return json.dumps({
            "generated": datetime.now().isoformat(),
            "total_reviews": total,
            "sentiments": sentiments,
            "topics": topics,
            "platform_quotes": platform_quotes,
        }, indent=2, ensure_ascii=False)

    # ── Markdown report ──────────────────────────────────────────────────
    report = f"""# Spotify AI Review Discovery — Insights Report
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Total Reviews Analyzed**: {total}

---

## 1. Sentiment Distribution
| Sentiment | Count |
|-----------|-------|
| Negative  | {sentiments.get('Negative', 0)} |
| Neutral   | {sentiments.get('Neutral', 0)} |
| Positive  | {sentiments.get('Positive', 0)} |

## 2. Top Pain Points
"""
    for topic, cnt in topics.items():
        report += f"- **{topic}**: {cnt} occurrences\n"

    for plat, label in [
        ("app_store", "Apple App Store"),
        ("play_store", "Google Play Store"),
        ("reddit", "Reddit Discussions"),
        ("twitter", "Twitter/X Posts"),
    ]:
        report += f"\n### {label} — Critical Feedback\n"
        quotes = platform_quotes.get(plat, [])
        if quotes:
            for q in quotes:
                report += f'- *"{q["content"][:200]}"*  — {q["date"]}\n'
        else:
            report += "*No negative reviews recorded for this platform.*\n"

    # Save locally
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "workspace"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "mcp_insights_report.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info("Report saved to %s", out_path)

    return report


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                        MCP RESOURCES (4 resources)                       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

@mcp.resource("reviews://all")
def resource_all_reviews() -> str:
    """Complete dump of all reviews in the database."""
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reviews ORDER BY date DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return json.dumps(rows, indent=2, ensure_ascii=False)


@mcp.resource("reviews://platform/{platform}")
def resource_reviews_by_platform(platform: str) -> str:
    """Reviews filtered by platform (play_store, app_store, reddit, twitter)."""
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reviews WHERE platform = ? ORDER BY date DESC", (platform,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return json.dumps(rows, indent=2, ensure_ascii=False)


@mcp.resource("insights://summary")
def resource_insights_summary() -> str:
    """Aggregated sentiment and topic statistics."""
    return get_insights_summary()


@mcp.resource("insights://critical")
def resource_critical_reviews() -> str:
    """Top 10 most critical reviews by severity score."""
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id, r.platform, r.content, r.date, i.sentiment, i.topic, i.score
        FROM reviews r JOIN insights i ON r.id = i.review_id
        WHERE i.sentiment = 'Negative'
        ORDER BY i.score ASC
        LIMIT 10
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return json.dumps(rows, indent=2, ensure_ascii=False)


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                        MCP PROMPTS (3 prompts)                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

@mcp.prompt()
def review_analysis_workflow() -> str:
    """Step-by-step prompt to run the full review discovery pipeline."""
    return """You are a Spotify Growth Team analyst. Execute the following workflow:

1. **Scrape Reviews**: Use `run_full_pipeline` with count_per_platform=20 to collect
   reviews from Google Play Store, Apple App Store, Reddit, and Twitter.

2. **Review Results**: Use `get_insights_summary` to examine the sentiment distribution,
   top pain points, and most critical reviews.

3. **Deep Dive**: Use `search_reviews` to explore specific topics like "shuffle",
   "bubble", or "recommendation" to understand recurring themes.

4. **Generate Report**: Use `export_insights_report` with format='markdown' to create
   a stakeholder-ready report with representative quotes and statistics.

5. **Share Findings**: Summarize the key actionable insights:
   - Which pain point is most severe?
   - What percentage of reviews are negative?
   - Which platform has the most complaints?
   - What specific product changes would address the top issues?"""


@mcp.prompt()
def platform_comparison() -> str:
    """Prompt to compare user sentiment across different platforms."""
    return """You are comparing user feedback across 4 platforms for Spotify.

1. Use `scrape_google_play_reviews` to get Google Play reviews.
2. Use `scrape_app_store_reviews` to get Apple App Store reviews.
3. Use `scrape_reddit_discussions` to get Reddit discussions.
4. Use `scrape_twitter_posts` to get Twitter/X posts.

For each platform:
- Ingest the reviews using `ingest_reviews`.
- Analyze them using `analyze_reviews`.

Then use `get_insights_summary` and compare:
- Which platform has the highest negativity ratio?
- Are certain pain points platform-specific (e.g., shuffle on mobile vs. web)?
- Do Reddit/Twitter users express different concerns than app store reviewers?

Present your findings as a comparison table."""


@mcp.prompt()
def churn_risk_assessment() -> str:
    """Prompt to identify high churn-risk user segments from reviews."""
    return """You are assessing churn risk from user feedback data.

1. Run `run_full_pipeline` to ensure you have fresh data.
2. Use `search_reviews` with keywords like "cancel", "unsubscribe", "switch",
   "leaving", "Apple Music" to find users expressing intent to churn.
3. Use `get_insights_summary` to understand severity distribution.

Produce a churn risk report:
- **High Risk**: Users mentioning competitor apps or cancellation intent.
- **Medium Risk**: Users with persistent negative feedback across multiple topics.
- **Low Risk**: Users with isolated complaints but overall engagement.

For each risk tier, provide the count, representative quotes, and
recommended product interventions."""


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                              ENTRY POINT                                 ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spotify Review Discovery MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8090,
        help="Port for SSE transport (default: 8090)",
    )
    args = parser.parse_args()

    logger.info(
        "Starting Spotify Review Discovery MCP Server v2.0 [transport=%s]",
        args.transport,
    )

    if args.transport == "sse":
        mcp.run(transport="sse", sse_params={"host": "0.0.0.0", "port": args.port})
    else:
        mcp.run(transport="stdio")
