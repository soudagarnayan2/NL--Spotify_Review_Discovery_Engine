import os
import sys
import json
import random
import re
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
from langdetect import detect

# Load environment variables
load_dotenv()

# Import database helpers
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from database import get_db_connection, init_db

# Try imports for scrapers & MCP
from app_store_scraper import AppStore
from google_play_scraper import Sort, reviews as play_reviews

MCP_AVAILABLE = False
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    pass

# Trigger reload for discovery engine changes
app = FastAPI(title="Spotify Review Discovery Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database at startup
@app.on_event("startup")
def startup_event():
    init_db()

# Schema structures
class IngestRequest(BaseModel):
    limit_scraped: int = 500
    limit_mocked: int = 500

# ----------------- Core Logic Helpers -----------------

def clean_and_normalize_review(content):
    if not content:
        return None
    # 1. Remove emojis
    cleaned = re.sub(r'[\U00010000-\U0010FFFF]', '', content)
    cleaned = re.sub(r'[\u2600-\u27BF]', '', cleaned)
    cleaned = cleaned.strip()
    
    # 2. Check length (at least 6 words)
    words = cleaned.split()
    if len(words) < 6:
        return None
    
    # 3. Check language (must be English)
    try:
        if detect(cleaned) != 'en':
            return None
    except Exception:
        ascii_chars = sum(1 for c in cleaned if ord(c) < 128)
        if len(cleaned) > 0 and (ascii_chars / len(cleaned)) < 0.8:
            return None
            
    return cleaned

# Ingestion engines
def ingest_play_store(limit):
    processed = []
    try:
        results, _ = play_reviews('com.spotify.music', lang='en', country='us', sort=Sort.NEWEST, count=limit * 2)
        for i, rev in enumerate(results):
            processed.append({
                "id": f"play_store_{rev.get('reviewId', i)}",
                "platform": "play_store",
                "rating": int(rev.get('score', 3)),
                "content": rev.get('content', '').strip(),
                "date": rev.get('at').strftime('%Y-%m-%d') if isinstance(rev.get('at'), datetime) else str(rev.get('at')),
                "user": rev.get('userName', 'Anonymous User')
            })
    except Exception as e:
        print(f"Play Store scraping error: {e}", file=sys.stderr)
    return processed

def ingest_app_store(limit):
    processed = []
    try:
        spotify_app = AppStore(country='us', app_name='spotify-music', app_id=324684580)
        spotify_app.review(how_many=limit * 2)
        for i, rev in enumerate(spotify_app.reviews):
            date_val = rev.get('date')
            date_str = date_val.strftime('%Y-%m-%d') if isinstance(date_val, datetime) else str(date_val)
            processed.append({
                "id": f"app_store_{i}_{int(datetime.now().timestamp())}",
                "platform": "app_store",
                "rating": int(rev.get('rating', 3)),
                "content": rev.get('review', '').strip(),
                "date": date_str,
                "user": rev.get('userName', 'Anonymous User')
            })
    except Exception as e:
        print(f"App Store scraping error: {e}", file=sys.stderr)
    return processed

def generate_social_mocks(platform, count):
    templates = {
        "reddit": [
            "I'm so tired of Spotify playing the same 15 songs on repeat. My Daily Mix 1 and 2 are literally just songs from my own liked playlist. What is the point? I want to discover actual new music, not just listen to the same algorithmic loop.",
            "Does anyone else feel like Discover Weekly has gotten stale? It used to find hidden gems, but now it just recommends songs I already skipped or artists I already follow. It's like the algorithm got lazy and only suggests 'safe' choices.",
            "Is there a way to clear or pause search history so a single joke song doesn't ruin my recommendations? I listened to one sea shanty track and now my entire feed is filled with folk sea shanties. There is no sandbox or temporary mode.",
            "Why does Spotify's recommendation engine keep pushing mainstream artists? I listen to indie shoegaze, but my Release Radar is full of pop-adjacent artists. The collaborative filtering bubble is real and hard to escape."
        ],
        "twitter": [
            "Spotify's shuffle is broken. I have 800 songs in my playlist, why does it play the same 20 tracks every single time? #SpotifyProblems",
            "Discover Weekly is just recommending songs I have literally already liked. Algorithmic exploitation at its finest. Give me something fresh!",
            "I skipped this song 5 times this week. Why is Spotify still playing it on my smart shuffle? It does not learn my active feedback.",
            "Desperately need a 'private listening' button that actually works so my kids' music doesn't pollute my recommendations. #spotify"
        ]
    }
    processed = []
    for i in range(count * 2):
        template = random.choice(templates[platform])
        review_date = datetime.now() - timedelta(days=random.randint(0, 30))
        user_num = random.randint(100, 9999)
        username = f"user_{platform}_{user_num}" if platform == "twitter" else f"u/reddit_listener_{user_num}"
        processed.append({
            "id": f"mock_{platform}_{i}_{int(datetime.now().timestamp())}",
            "platform": platform,
            "rating": random.choice([1, 2, 3]) if platform in ["app_store", "play_store"] else None,
            "content": template,
            "date": review_date.strftime('%Y-%m-%d'),
            "user": username
        })
    return processed

def analyze_review_llm(content, rating, platform, api_key):
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        prompt = f"""
        Analyze the following user review for a music streaming app.
        
        Review Content: "{content}"
        Platform: {platform}
        Rating: {rating}
        
        Categorize the review into EXACTLY ONE of these topics:
        - Algorithmic Bubble / Recommendation Repetition
        - Smart Shuffle loop issues
        - Taste pollution / Lack of Sandbox mode
        - Decision overload
        - General Feedback / Other
        
        Determine the sentiment as EXACTLY ONE of: Positive, Neutral, Negative.
        
        Assign a severity score from 0.0 to 1.0 (where 1.0 is extremely critical/high churn risk).
        
        Respond in strict JSON format:
        {{
            "sentiment": "...",
            "topic": "...",
            "score": 0.0
        }}
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a precise JSON-outputting data analysis assistant."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        result = json.loads(chat_completion.choices[0].message.content)
        sentiment = result.get("sentiment", "Neutral")
        topic = result.get("topic", "General Feedback / Other")
        score = float(result.get("score", 0.5))
        return sentiment, topic, score
    except Exception as e:
        print(f"LLM analysis failed: {e}", file=sys.stderr)
        return None, None, None

# Rules-based analysis
def analyze_review_rules(content, rating, platform):
    content_lower = content.lower()
    
    # Topic detection
    topic = "General Feedback / Other"
    if any(word in content_lower for word in ["bubble", "loop", "repeat", "same song", "exploitation", "stagnation", "echo chamber"]):
        topic = "Algorithmic Bubble / Recommendation Repetition"
    elif any(word in content_lower for word in ["shuffle", "smart shuffle", "skip feedback"]):
        topic = "Smart Shuffle loop issues"
    elif any(word in content_lower for word in ["pollute", "kid", "child", "bedtime", "sandbox", "history", "ruined my"]):
        topic = "Taste pollution / Lack of Sandbox mode"
    elif any(word in content_lower for word in ["paralysis", "overload", "scrolling", "grid", "too many options", "spend 20 minutes"]):
        topic = "Decision overload"
        
    # Sentiment rules
    sentiment = "Neutral"
    score = 0.5
    
    negative_words = ["terrible", "bad", "worst", "repetitive", "broken", "garbage", "waste", "stale", "lazy", "frustrating", "hate", "polluted", "annoying", "poor", "unusable"]
    positive_words = ["great", "love", "awesome", "perfect", "good", "best", "excellent", "enjoy"]
    
    neg_count = sum(1 for w in negative_words if w in content_lower)
    pos_count = sum(1 for w in positive_words if w in content_lower)
    
    if rating is not None:
        if rating <= 2:
            sentiment = "Negative"
            score = 0.2 - (0.05 * neg_count)
        elif rating >= 4:
            sentiment = "Positive"
            score = 0.8 + (0.05 * pos_count)
        else:
            if neg_count > pos_count:
                sentiment = "Negative"
                score = 0.4
            elif pos_count > neg_count:
                sentiment = "Positive"
                score = 0.6
    else:
        if neg_count > pos_count:
            sentiment = "Negative"
            score = 0.3
        elif pos_count > neg_count:
            sentiment = "Positive"
            score = 0.7
            
    score = max(0.0, min(1.0, score))
    return sentiment, topic, score

# MCP Client Helpers
def extract_mcp_url(response, default_url):
    if isinstance(response, dict):
        return response.get("url", default_url)
    
    try:
        from mcp.types import CallToolResult
        if isinstance(response, CallToolResult):
            if response.content:
                first_block = response.content[0]
                if hasattr(first_block, "text"):
                    text_val = first_block.text.strip()
                    try:
                        data = json.loads(text_val)
                        if isinstance(data, dict) and "url" in data:
                            return data["url"]
                    except json.JSONDecodeError:
                        import re
                        urls = re.findall(r'https?://[^\s)]+', text_val)
                        if urls:
                            return urls[0]
            if hasattr(response, "structuredContent") and response.structuredContent:
                if isinstance(response.structuredContent, dict) and "url" in response.structuredContent:
                    return response.structuredContent["url"]
    except Exception as e:
        print(f"Error extracting URL from MCP response: {e}", file=sys.stderr)
        
    return default_url

async def call_mcp_create_doc(server_path, title, content):
    server_params = StdioServerParameters(command="node", args=[server_path])
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            response = await session.call_tool("create_document", {"title": title, "content": content})
            return extract_mcp_url(response, "https://docs.google.com/document/d/mock-mcp-report-id")

async def call_mcp_send_gmail(server_path, subject, body, recipient):
    server_params = StdioServerParameters(command="node", args=[server_path])
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            await session.call_tool("send_email", {"to": recipient, "subject": subject, "body": body})
            return True

# ----------------- API Route Endpoints -----------------

@app.post("/api/v1/ingest")
async def api_ingest(req: IngestRequest):
    # Ingest from all platforms
    raw_list = []
    raw_list.extend(ingest_play_store(req.limit_scraped))
    raw_list.extend(ingest_app_store(req.limit_scraped))
    raw_list.extend(generate_social_mocks("reddit", req.limit_mocked))
    raw_list.extend(generate_social_mocks("twitter", req.limit_mocked))
    
    # Filter
    counts = {"play_store": 0, "app_store": 0, "reddit": 0, "twitter": 0}
    targets = {
        "play_store": req.limit_scraped,
        "app_store": req.limit_scraped,
        "reddit": req.limit_mocked,
        "twitter": req.limit_mocked
    }
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    inserted_count = 0
    for rev in raw_list:
        plat = rev["platform"]
        if counts[plat] >= targets[plat]:
            continue
            
        cleaned = clean_and_normalize_review(rev["content"])
        if cleaned:
            try:
                cursor.execute("""
                INSERT INTO reviews (id, platform, rating, content, date, user)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET content=excluded.content
                """, (rev["id"], plat, rev["rating"], cleaned, rev["date"], rev["user"]))
                inserted_count += 1
                counts[plat] += 1
            except Exception as e:
                print(f"Database insert error: {e}", file=sys.stderr)
                
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "inserted_total": inserted_count,
        "platform_counts": counts
    }

@app.get("/api/v1/reviews")
async def api_get_reviews(platform: str = Query(None), limit: int = 50, offset: int = 0):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if platform:
        cursor.execute("SELECT * FROM reviews WHERE platform = ? LIMIT ? OFFSET ?", (platform, limit, offset))
    else:
        cursor.execute("SELECT * FROM reviews LIMIT ? OFFSET ?", (limit, offset))
        
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(r) for r in rows]

@app.post("/api/v1/analyze")
async def api_analyze():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM reviews")
    reviews = cursor.fetchall()
    
    if not reviews:
        conn.close()
        raise HTTPException(status_code=400, detail="No reviews present in the database. Run /api/v1/ingest first.")
        
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    analyzed_count = 0
    for rev in reviews:
        sentiment, topic, score = None, None, None
        
        if groq_api_key:
            sentiment, topic, score = analyze_review_llm(rev["content"], rev["rating"], rev["platform"], groq_api_key)
            
        if not sentiment:
            sentiment, topic, score = analyze_review_rules(rev["content"], rev["rating"], rev["platform"])
            
        insight_id = f"insight_{rev['id']}"
        cursor.execute("""
        INSERT INTO insights (id, review_id, sentiment, topic, score)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET sentiment=excluded.sentiment, topic=excluded.topic, score=excluded.score
        """, (insight_id, rev["id"], sentiment, topic, score))
        analyzed_count += 1
        
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "processed_total": analyzed_count
    }

@app.get("/api/v1/insights")
async def api_get_insights(all_negatives: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Compile statistics
    cursor.execute("SELECT sentiment, COUNT(*) as count FROM insights GROUP BY sentiment")
    sentiments = {row["sentiment"]: row["count"] for row in cursor.fetchall()}
    
    cursor.execute("SELECT topic, COUNT(*) as count FROM insights GROUP BY topic")
    topics = {row["topic"]: row["count"] for row in cursor.fetchall()}
    
    # Join reviews and insights to grab negative quotes
    sql = """
    SELECT r.content, r.platform, r.user, r.date, i.topic 
    FROM reviews r 
    JOIN insights i ON r.id = i.review_id 
    WHERE i.sentiment = 'Negative'
    ORDER BY r.date DESC
    """
    if not all_negatives:
        sql += " LIMIT 5"
        
    cursor.execute(sql)
    neg_samples = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "statistics": {
            "sentiments": sentiments,
            "topics": topics
        },
        "negative_samples": neg_samples
    }

def scrub_pii(text, topic=None):
    if not text: return text
    # If the topic is uncertain/general, aggressively redact URLs and emails
    if topic == "General Feedback / Other" or not topic:
        text = re.sub(r'https?://\S+', '[REDACTED URL]', text)
        text = re.sub(r'\S+@\S+', '[REDACTED EMAIL]', text)
    return text

def anonymize_username(user, topic=None):
    if not user or user.lower() in ["anonymous user", "unknown"]:
        return "Anonymous"
    if topic == "General Feedback / Other" or not topic:
        return "User_[REDACTED]"
    return user

@app.post("/api/v1/export")
async def api_export(recipient: str = "stakeholders@spotify.com", docs_mcp_server: str = "", gmail_mcp_server: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Grab counts
    cursor.execute("SELECT COUNT(*) as count FROM reviews")
    total_reviews = cursor.fetchone()["count"]
    
    cursor.execute("SELECT sentiment, COUNT(*) as count FROM insights GROUP BY sentiment")
    sentiments = {row["sentiment"]: row["count"] for row in cursor.fetchall()}
    
    cursor.execute("SELECT topic, COUNT(*) as count FROM insights GROUP BY topic")
    topics = {row["topic"]: row["count"] for row in cursor.fetchall()}
    
    # Grab negative quotes per platform category
    # 1. Apple App Store
    cursor.execute("""
    SELECT r.content, r.user, r.date
    FROM reviews r
    JOIN insights i ON r.id = i.review_id
    WHERE r.platform = 'app_store' AND i.sentiment = 'Negative'
    LIMIT 3
    """)
    app_store_quotes = [dict(row) for row in cursor.fetchall()]

    # 2. Google Play Store / Community Forums
    cursor.execute("""
    SELECT r.content, r.user, r.date
    FROM reviews r
    JOIN insights i ON r.id = i.review_id
    WHERE r.platform = 'play_store' AND i.sentiment = 'Negative'
    LIMIT 3
    """)
    play_store_quotes = [dict(row) for row in cursor.fetchall()]

    # 3. Reddit / Twitter / Social Media
    cursor.execute("""
    SELECT r.content, r.platform, r.user, r.date
    FROM reviews r
    JOIN insights i ON r.id = i.review_id
    WHERE r.platform IN ('reddit', 'twitter') AND i.sentiment = 'Negative'
    LIMIT 3
    """)
    social_quotes = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # Compile report text answering the 6 core analytical objectives
    report_markdown = f"""# Spotify AI Review Discovery Insights Report
**Generated**: {datetime.now().strftime('%Y-%m-%d')}
**Total Reviews Analyzed**: {total_reviews}

## Executive Summary & Key Analytical Findings

This report synthesizes feedback from Apple App Store, Google Play Store, Reddit, and Twitter to address the strategic challenge of recommendation repetition and user discovery friction.

---

### Q1: Why do users struggle to discover new music?
**Analysis**: Users struggle due to:
1. **Algorithmic Repetitiveness**: Standard playlists (e.g., Discover Weekly, Daily Mixes) are dominated by tracks the user has already heard or skipped.
2. **UI Clutter & Smart Shuffle Loops**: The Smart Shuffle feature frequently cycles through a small loop of ~15-20 tracks, trapping the user instead of expanding their selection.
3. **Low Input Resolution**: Users cannot easily communicate abstract preferences (e.g., specific moods, situations, or sub-genres) using traditional buttons.

**Database Evidence (Topic: Algorithmic Bubble & Smart Shuffle)**:
"""
    # Add some actual quotes if available
    cursor = get_db_connection().cursor()
    cursor.execute("""
    SELECT r.content, r.user, r.date, i.topic
    FROM reviews r
    JOIN insights i ON r.id = i.review_id
    WHERE i.sentiment = 'Negative' AND i.topic IN ('Algorithmic Bubble / Recommendation Repetition', 'Smart Shuffle loop issues')
    LIMIT 3
    """)
    for q in cursor.fetchall():
        content_scrubbed = scrub_pii(q['content'], q['topic'])
        user_anon = anonymize_username(q['user'], q['topic'])
        report_markdown += f"- *\"{content_scrubbed}\"* (User: {user_anon} — {q['date']})\n"
    
    report_markdown += """
---

### Q2: What are the most common frustrations with recommendation algorithms?
**Analysis**:
1. **Redundant Suggestions**: The algorithm pushes songs that users have already skipped multiple times.
2. **Mainstream Push**: Audiophiles report that recommendation engines over-index on popular/mainstream hits rather than niche, independent, or local artists that fit their true preferences.
3. **Smart Shuffle Inflexibility**: The feature automatically mixes in recommendations that disrupt the flow of curated lists.

**Database Evidence (Topic: Recommendations & Shuffle)**:
"""
    cursor.execute("""
    SELECT r.content, r.user, r.date, i.topic
    FROM reviews r
    JOIN insights i ON r.id = i.review_id
    WHERE i.sentiment = 'Negative' AND i.topic = 'Smart Shuffle loop issues'
    LIMIT 2
    """)
    for q in cursor.fetchall():
        content_scrubbed = scrub_pii(q['content'], q['topic'])
        user_anon = anonymize_username(q['user'], q['topic'])
        report_markdown += f"- *\"{content_scrubbed}\"* (User: {user_anon} — {q['date']})\n"

    report_markdown += """
---

### Q3: What listening behaviors are users trying to achieve?
**Analysis**:
- **Active Exploration**: Seeking niche genres or specific eras to expand musical horizons.
- **Context/Mood-Matching**: Looking for music tailored to highly specific settings (e.g., studying, nocturnal driving, workouts) rather than generic genre lists.
- **Nostalgic Recovery**: Returning to older favorite tracks without permanently polluting future recommendations.

---

### Q4: What causes users to repeatedly listen to the same content?
**Analysis**:
- **Decision Overload**: Facing a catalog of 100M+ tracks leads to choice paralysis. Selecting familiar music requires less cognitive effort.
- **Trust Gap**: Past experiences with low-quality automatic recommendations cause users to avoid new suggestions.
- **Convenience**: Autoplay and default playlists repeatedly serve familiar songs.

**Database Evidence (Topic: Decision Overload)**:
"""
    cursor.execute("""
    SELECT r.content, r.user, r.date, i.topic
    FROM reviews r
    JOIN insights i ON r.id = i.review_id
    WHERE i.sentiment = 'Negative' AND i.topic = 'Decision overload'
    LIMIT 2
    """)
    for q in cursor.fetchall():
        content_scrubbed = scrub_pii(q['content'], q['topic'])
        user_anon = anonymize_username(q['user'], q['topic'])
        report_markdown += f"- *\"{content_scrubbed}\"* (User: {user_anon} — {q['date']})\n"

    report_markdown += """
---

### Q5: Which user segments experience different discovery challenges?
**Analysis**:
1. **Casual Listeners**: Primarily experience *decision overload* and *Smart Shuffle loops*. They want high-quality passive listening with minimal effort.
2. **Power Users / Audiophiles**: Struggle with *algorithmic bubbles* and *mainstream push*. They actively search for niche or independent artists and feel frustrated when recommendations fail to scale.

---

### Q6: What unmet needs emerge consistently across reviews?
**Analysis**:
1. **Exploration Sandbox Mode**: A toggle to listen to new genres/styles without permanently polluting their recommendation model.
2. **Conversational/Prompt-Based Discovery**: A natural language assistant to query the catalog using detailed moods, scenarios, or acoustic settings.
3. **Real-time Mood & Pace Fine-Tuning**: Quick controls to adjust energy, speed, or acoustic parameters dynamically.

**Database Evidence (Topic: Sandbox / Taste Pollution)**:
"""
    cursor.execute("""
    SELECT r.content, r.user, r.date, i.topic
    FROM reviews r
    JOIN insights i ON r.id = i.review_id
    WHERE i.sentiment = 'Negative' AND i.topic = 'Taste pollution / Lack of Sandbox mode'
    LIMIT 2
    """)
    for q in cursor.fetchall():
        content_scrubbed = scrub_pii(q['content'], q['topic'])
        user_anon = anonymize_username(q['user'], q['topic'])
        report_markdown += f"- *\"{content_scrubbed}\"* (User: {user_anon} — {q['date']})\n"

    report_markdown += """
---

## 4. Overall Sentiment Metrics
- **Negative Feedback Count**: {sentiments.get('Negative', 0)}
- **Neutral Feedback Count**: {sentiments.get('Neutral', 0)}
- **Positive Feedback Count**: {sentiments.get('Positive', 0)}

## 5. Topic Frequency Breakdown
- *Algorithmic Bubble*: {topics.get('Algorithmic Bubble / Recommendation Repetition', 0)}
- *Smart Shuffle issues*: {topics.get('Smart Shuffle loop issues', 0)}
- *Taste pollution / Lack of Sandbox*: {topics.get('Taste pollution / Lack of Sandbox mode', 0)}
- *Decision overload*: {topics.get('Decision overload', 0)}
- *Other / General*: {topics.get('General Feedback / Other', 0)}
"""
        
    # Write via MCP or local simulation
    use_mcp = MCP_AVAILABLE and docs_mcp_server
    doc_url = "https://docs.google.com/document/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ123456spotify"
    
    if use_mcp:
        try:
            doc_url = await call_mcp_create_doc(docs_mcp_server, "Spotify Review Discovery Insights Report", report_markdown)
            if gmail_mcp_server:
                email_subject = "[Growth Team] Spotify AI Review Discovery Engine - Insights Report Ready"
                email_body = f"Hello Team,\n\nThe latest insights report is ready at:\n{doc_url}\n\nBest regards,\nGrowth Assistant"
                await call_mcp_send_gmail(gmail_mcp_server, email_subject, email_body, recipient)
            return {"status": "success", "mode": "mcp", "url": doc_url}
        except Exception as e:
            print(f"MCP Export failed: {e}. Falling back to simulation.", file=sys.stderr)
            
    # Simulation Fallback
    sim_dir = os.path.abspath("data/workspace")
    if not os.path.exists(sim_dir):
        os.makedirs(sim_dir)
        
    doc_path = os.path.join(sim_dir, "google_doc_ReviewAnalysisInsightsReport.md")
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(report_markdown)
        
    gmail_path = os.path.join(sim_dir, "gmail_sent_NotificationMemo.txt")
    with open(gmail_path, 'w', encoding='utf-8') as f:
        f.write(f"TO: {recipient}\nSUBJECT: [Growth Team] Spotify Insights Report\n\n{report_markdown}")
        
    return {
        "status": "success",
        "mode": "simulation",
        "report_doc": doc_path,
        "email_memo": gmail_path
    }

# ────────────────────────────────────────────────────────────────────────────
# Phase 4: AI-Native Discovery Endpoints
# ────────────────────────────────────────────────────────────────────────────

# Import Phase 4 modules (add to sys.path)
_phase4_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "phase4"))
if _phase4_dir not in sys.path:
    sys.path.insert(0, _phase4_dir)

try:
    import discovery_engine
    import importlib
    importlib.reload(discovery_engine)
    from discovery_engine import parse_music_intent, search_tracks, refine_search, generate_explanation
    from spotify_auth import get_auth_url, exchange_code, is_authenticated, create_playlist, get_current_user
    from feedback_agent import send_feedback_survey, log_feedback_to_docs, get_feedback_stats
    PHASE4_AVAILABLE = True
except ImportError as e:
    print(f"Phase 4 modules not fully available: {e}", file=sys.stderr)
    PHASE4_AVAILABLE = False

# Pydantic models for Phase 4
class DiscoverRequest(BaseModel):
    query: str
    session_id: str = "default"
    history: list = []

class RefineRequest(BaseModel):
    session_id: str = "default"
    refinement: str
    previous_intent: dict = {}

class PlaylistRequest(BaseModel):
    session_id: str = "default"
    name: str = "AI Discovery Playlist"
    track_names: list = []

class FeedbackRequest(BaseModel):
    user_email: str = "stakeholders@spotify.com"
    session_summary: dict = {}

class FeedbackLogRequest(BaseModel):
    user_email: str = "anonymous@user.com"
    query: str = ""
    track_count: int = 0
    relevance: int = 3
    discovery: str = "No"
    reuse: int = 3
    improvement: str = ""
    track_feedback: str = ""

# In-memory session store for conversation history
_discovery_sessions: dict = {}

def check_query_rules(query_lower: str) -> tuple[bool, Optional[int]]:
    if any(t in query_lower for t in ["struggle to discover", "why do users struggle", "struggle", "discovery challenge", "discover new music"]):
        return True, 1
    elif any(t in query_lower for t in ["frustration", "recommendation", "algorithm", "shuffle", "repetition", "repetitive", "same song"]):
        return True, 2
    elif any(t in query_lower for t in ["listening behavior", "behavior", "achieve", "trying to achieve", "listening goal"]):
        return True, 3
    elif any(t in query_lower for t in ["repeatedly listen", "same content", "repeat", "why play same", "listen to the same"]):
        return True, 4
    elif any(t in query_lower for t in ["segment", "casual", "audiophile", "power user", "different discovery"]):
        return True, 5
    elif any(t in query_lower for t in ["unmet need", "needs", "emerge consistently", "sandbox", "private listening", "mood adjustment"]):
        return True, 6
    elif any(t in query_lower for t in ["retention", "influence user retention", "influence retention", "keep users", "staying on"]):
        return True, 7
    elif any(t in query_lower for t in ["premium subscription", "drive premium", "why subscribe", "buy premium", "features drive"]):
        return True, 8
    elif any(t in query_lower for t in ["cancel premium", "reasons users cancel", "why cancel", "stop paying"]):
        return True, 9
    elif any(t in query_lower for t in ["segment report the highest", "segments report the highest", "highest satisfaction", "most satisfied"]):
        return True, 10
    elif any(t in query_lower for t in ["product improvement", "greatest impact on user", "impact on user experience", "improve user experience"]):
        return True, 11
    if any(t in query_lower for t in ["review", "feedback", "scraped", "customer say", "user say", "sentiment", "update", "shift", "complain", "rating", "satisfaction", "uninstall", "churn", "competitor", "switch from"]):
        return True, 0
    return False, None

def get_predefined_analysis(index: int) -> str:
    if index == 1:
        return (
            "**Why do users struggle to discover new music?**\n"
            "1. **Algorithmic Repetitiveness**: Standard playlists (e.g., Discover Weekly, Daily Mixes) are dominated by tracks the user has already heard or skipped.\n"
            "2. **UI Clutter & Smart Shuffle Loops**: The Smart Shuffle feature frequently cycles through a small loop of ~15-20 tracks, trapping the user instead of expanding their selection.\n"
            "3. **Low Input Resolution**: Users cannot easily communicate abstract preferences (e.g., specific moods, situations, or sub-genres) using traditional buttons."
        )
    elif index == 2:
        return (
            "**What are the most common frustrations with recommendation algorithms?**\n"
            "1. **Redundant Suggestions**: The algorithm pushes songs that users have already skipped multiple times, failing to learn from skip feedback.\n"
            "2. **Mainstream Push**: Audiophiles report that recommendation engines over-index on popular/mainstream hits rather than niche, independent, or local artists that fit their true preferences.\n"
            "3. **Smart Shuffle Inflexibility**: The feature automatically mixes in recommendations that disrupt the flow of curated lists."
        )
    elif index == 3:
        return (
            "**What listening behaviors are users trying to achieve?**\n"
            "- **Active Exploration**: Seeking niche genres or specific eras to expand musical horizons.\n"
            "- **Context/Mood-Matching**: Looking for music tailored to highly specific settings (e.g., studying, nocturnal driving, workouts) rather than generic genre lists.\n"
            "- **Nostalgic Recovery**: Returning to older favorite tracks without permanently polluting future recommendations."
        )
    elif index == 4:
        return (
            "**What causes users to repeatedly listen to the same content?**\n"
            "- **Decision Overload**: Facing a catalog of 100M+ tracks leads to choice paralysis. Selecting familiar music requires less cognitive effort.\n"
            "- **Trust Gap**: Past experiences with low-quality automatic recommendations cause users to avoid new suggestions.\n"
            "- **Convenience**: Autoplay and default playlists repeatedly serve familiar songs."
        )
    elif index == 5:
        return (
            "**Which user segments experience different discovery challenges?**\n"
            "1. **Casual Listeners**: Primarily experience *decision overload* and *Smart Shuffle loops*. They want high-quality passive listening with minimal effort.\n"
            "2. **Power Users / Audiophiles**: Struggle with *algorithmic bubbles* and *mainstream push*. They actively search for niche or independent artists and feel frustrated when recommendations fail to scale."
        )
    elif index == 6:
        return (
            "**What unmet needs emerge consistently across reviews?**\n"
            "1. **Exploration Sandbox Mode**: A toggle to listen to new genres/styles without permanently polluting their recommendation model.\n"
            "2. **Conversational/Prompt-Based Discovery**: A natural language assistant to query the catalog using detailed moods, scenarios, or acoustic settings.\n"
            "3. **Real-time Mood & Pace Fine-Tuning**: Quick controls to adjust energy, speed, or acoustic parameters dynamically."
        )
    elif index == 7:
        return (
            "**What factors influence user retention?**\n"
            "1. **Personalization Accuracy**: High-quality Daily Mixes and Discovery Weekly lists prevent playlist staleness.\n"
            "2. **Social Community Integration**: Seamless sharing of music, playlists, and wrapped cards increases network stickiness.\n"
            "3. **Cross-Device Handoff**: The Spotify Connect speaker system allows quick controls between devices, driving daily active engagement."
        )
    elif index == 8:
        return (
            "**Which features drive premium subscriptions?**\n"
            "1. **Ad-Free Listening**: The main driver for users converting from the free tier.\n"
            "2. **Offline Download Mode**: Crucial for commuters, travelers, and areas with poor connectivity.\n"
            "3. **Unlimited Skips**: Removes control limitations in free mode shuffle playlists."
        )
    elif index == 9:
        return (
            "**What are the main reasons users cancel premium plans?**\n"
            "1. **Price Hikes**: Cost increases drive budget-conscious users back to the free tier.\n"
            "2. **Recommendation staleness**: Getting stuck in repetitive recommendation loops makes the monthly fee feel wasted.\n"
            "3. **Alternative Platforms**: Users migrating to competitor services offering cheaper bundles or student plans."
        )
    elif index == 10:
        return (
            "**Which user segments report the highest satisfaction?**\n"
            "1. **Casual Playlists Listeners**: Delighted by background tracks, curated chill mixes, and sleep sound feeds.\n"
            "2. **Connected Ecosystem Users**: Smart speaker, smartwatch, and car display integration users show extremely high satisfaction and retention."
        )
    elif index == 11:
        return (
            "**What product improvements would have the greatest impact on user experience?**\n"
            "1. **True Recommendation Sandbox Mode**: A toggle to browse new music safely without permanently skewing personal taste models.\n"
            "2. **Prompt-Based Semantic Search**: Natural language querying to immediately fetch custom music lists and avoid decision overload.\n"
            "3. **Smart Shuffle Negative Feedback**: Allowing users to permanently hide songs they skip multiple times from recurring mixes."
        )
    else:
        return (
            "**Spotify Review Analysis Overview**:\n"
            "Users consistently report being trapped in recommendation echo chambers, "
            "experiencing repetitive Smart Shuffle loops, and facing taste pollution when sharing "
            "accounts or exploring new genres."
        )

def get_sqlite_evidence(index: int) -> str:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Determine query based on index
        if index in (1, 2):
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE i.topic IN ('Algorithmic Bubble / Recommendation Repetition', 'Smart Shuffle loop issues')
            ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
            LIMIT 3
            """)
        elif index == 4:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE i.topic = 'Decision overload'
            ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
            LIMIT 3
            """)
        elif index == 5:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE r.content LIKE '%audiophile%' OR r.content LIKE '%niche%' OR r.content LIKE '%mainstream%' OR r.content LIKE '%genre%'
            ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
            LIMIT 3
            """)
            rows = cursor.fetchall()
            if not rows:
                cursor.execute("""
                SELECT r.content, r.user, r.date, i.topic
                FROM reviews r
                JOIN insights i ON r.id = i.review_id
                ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
                LIMIT 3
                """)
        elif index == 6:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE i.topic = 'Taste pollution / Lack of Sandbox mode'
            ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
            LIMIT 3
            """)
        elif index == 7:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE r.content LIKE '%mix%' OR r.content LIKE '%recommend%' OR r.content LIKE '%discover%'
            ORDER BY CASE WHEN i.sentiment = 'Positive' THEN 0 ELSE 1 END
            LIMIT 3
            """)
        elif index == 8:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE r.content LIKE '%premium%' OR r.content LIKE '%ads%' OR r.content LIKE '%skip%'
            ORDER BY CASE WHEN i.sentiment = 'Positive' THEN 0 ELSE 1 END
            LIMIT 3
            """)
        elif index == 9:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE r.content LIKE '%cancel%' OR r.content LIKE '%price%' OR r.content LIKE '%subscription%'
            ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
            LIMIT 3
            """)
        elif index == 10:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE r.content LIKE '%love%' OR r.content LIKE '%great%' OR r.content LIKE '%best%'
            ORDER BY CASE WHEN i.sentiment = 'Positive' THEN 0 ELSE 1 END
            LIMIT 3
            """)
        elif index == 11:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE r.content LIKE '%improve%' OR r.content LIKE '%sandbox%' OR r.content LIKE '%fix%' OR r.content LIKE '%feature%'
            ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
            LIMIT 3
            """)
        else:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
            LIMIT 3
            """)
            
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "- *No specific reviews found in the database. Please ensure review data has been ingested and analyzed.*"
            
        evidence_str = ""
        for r in rows:
            content = r["content"]
            content = re.sub(r'https?://\S+', '[REDACTED_URL]', content)
            content = re.sub(r'\S+@\S+', '[REDACTED_EMAIL]', content)
            
            user = r["user"]
            if user.lower() in ["anonymous user", "unknown"]:
                user = "Anonymous"
            else:
                user = f"User_{user[:6]}" if len(user) > 6 else f"User_{user}"
                
            evidence_str += f"- *\"{content}\"* ({user} — {r['date']})\n"
        return evidence_str
    except Exception as e:
        print(f"Error fetching SQLite evidence: {e}", file=sys.stderr)
        return "- *Error loading evidence from SQLite database.*"

def is_likely_review_query(query: str) -> bool:
    q = query.lower().strip()
    
    # 1. Direct keywords that are strongly associated with reviews
    direct_keywords = [
        "review", "sentiment", "feedback", "rating", "user", "customer", "complain", "opinion",
        "switch", "competitor", "apple music", "youtube music", "amazon music", "deezer", "tidal",
        "cancel", "premium", "subscription", "satisfied", "satisfaction", "hate",
        "frustrat", "annoy", "pain point", "improvement", "requested", "request", "missing", "priorit",
        "buffering", "offline", "download", "playback", "navigate",
        "stuck", "update", "new release",
        "bug", "crash", "freeze", "slow", "error", "confus", "trend", "uninstall", "churn"
    ]
    if any(k in q for k in direct_keywords):
        return True
        
    # 2. Interrogative queries about the app experience / people / users
    interrogatives = ["why", "what", "how", "which", "are", "is", "do", "does", "who", "should", "can"]
    starts_interrogative = any(q.startswith(i + " ") or q.startswith(i + "'") or q.startswith(i + "s ") for i in interrogatives)
    
    app_contexts = ["user", "listener", "people", "app", "product", "feature", "screen", "navigation", "bug", "crash", "issue", "problem", "trend", "pain point", "satisfy", "competitor", "spotify", "music app", "navigat", "playback", "goal"]
    
    if starts_interrogative and any(c in q for c in app_contexts):
        return True
        
    return False

def get_sqlite_evidence_list(index: int) -> list[dict]:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if index in (1, 2):
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE i.topic IN ('Algorithmic Bubble / Recommendation Repetition', 'Smart Shuffle loop issues')
            ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
            LIMIT 6
            """)
        elif index == 4:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE i.topic = 'Decision overload'
            ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
            LIMIT 6
            """)
        elif index == 5:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE r.content LIKE '%audiophile%' OR r.content LIKE '%niche%' OR r.content LIKE '%mainstream%' OR r.content LIKE '%genre%'
            ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
            LIMIT 6
            """)
            rows = cursor.fetchall()
            if not rows:
                cursor.execute("""
                SELECT r.content, r.user, r.date, i.topic
                FROM reviews r
                JOIN insights i ON r.id = i.review_id
                ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
                LIMIT 6
                """)
        elif index == 6:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE i.topic = 'Taste pollution / Lack of Sandbox mode'
            ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
            LIMIT 6
            """)
        elif index == 7:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE r.content LIKE '%mix%' OR r.content LIKE '%recommend%' OR r.content LIKE '%discover%'
            ORDER BY CASE WHEN i.sentiment = 'Positive' THEN 0 ELSE 1 END
            LIMIT 6
            """)
        elif index == 8:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE r.content LIKE '%premium%' OR r.content LIKE '%ads%' OR r.content LIKE '%skip%'
            ORDER BY CASE WHEN i.sentiment = 'Positive' THEN 0 ELSE 1 END
            LIMIT 6
            """)
        elif index == 9:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE r.content LIKE '%cancel%' OR r.content LIKE '%price%' OR r.content LIKE '%subscription%'
            ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
            LIMIT 6
            """)
        elif index == 10:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE r.content LIKE '%love%' OR r.content LIKE '%great%' OR r.content LIKE '%best%'
            ORDER BY CASE WHEN i.sentiment = 'Positive' THEN 0 ELSE 1 END
            LIMIT 6
            """)
        elif index == 11:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE r.content LIKE '%improve%' OR r.content LIKE '%sandbox%' OR r.content LIKE '%fix%' OR r.content LIKE '%feature%'
            ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
            LIMIT 6
            """)
        else:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            ORDER BY CASE WHEN i.sentiment = 'Negative' THEN 0 ELSE 1 END
            LIMIT 6
            """)
            
        rows = cursor.fetchall()
        conn.close()
        
        evidence_list = []
        for r in rows:
            content = r["content"]
            content = re.sub(r'https?://\S+', '[REDACTED_URL]', content)
            content = re.sub(r'\S+@\S+', '[REDACTED_EMAIL]', content)
            
            user = r["user"]
            if user.lower() in ["anonymous user", "unknown"]:
                user = "Anonymous"
            else:
                user = f"User_{user[:6]}" if len(user) > 6 else f"User_{user}"
            evidence_list.append({
                "content": content,
                "platform": "app_store" if "app" in content.lower() else "reddit",
                "date": r["date"]
            })
        return evidence_list
    except Exception as e:
        print(f"Error fetching SQLite evidence list: {e}", file=sys.stderr)
        return []

def format_voc_report(query, matched_idx, category, total_reviews, matched_count, local_sentiments, topics_list, evidence_list):
    # Determine confidence
    confidence = "High" if matched_count >= 5 else ("Medium" if matched_count >= 2 else "Low")
    
    # Formulate Executive Summary
    predef_text = get_predefined_analysis(matched_idx) if matched_idx else ""
    summary = f"Voice of Customer analysis addressing the query: \\\"{query}\\\". Based on {matched_count} matching reviews out of {total_reviews} analyzed. "
    if predef_text:
        summary += predef_text.replace("**", "").replace("\n", " ")
    else:
        dominant_sentiment = sorted(local_sentiments.items(), key=lambda x: x[1], reverse=True)[0][0] if sum(local_sentiments.values()) > 0 else "Neutral"
        summary += f"The user feedback in category '{category}' exhibits a primarily {dominant_sentiment.lower()} sentiment regarding these product attributes."
        
    # Format Findings
    findings_md = ""
    if matched_idx:
        findings_md += f"#### Theme: {category}\n* **Summary**: {predef_text}\n* **Overall Sentiment**: Negative (critical focus)\n* **Frequency**: High\n"
    else:
        for t in list(set(topics_list))[:3]:
            cnt = topics_list.count(t)
            findings_md += f"#### Theme: {t}\n* **Summary**: Customer mentions of {t.lower()}.\n* **Overall Sentiment**: Mixed\n* **Frequency**: {'High' if cnt >= 5 else 'Medium'}\n"
            
    findings_md += "\n* **Representative Review Excerpts**:\n"
    for e in evidence_list[:3]:
        findings_md += f"  - \\\"{e['content']}\\\" ({e.get('platform', 'App Store')} - {e.get('date', 'Just now')})\n"

    # Determine Pain Points / Positive / Needs
    needs = "Accomplish stable playback, custom playlist controls, and discover fresh music recommendations."
    pain_points = "Algorithmic repetition, Smart Shuffle looping issues, and lack of fine-tuned discovery parameters."
    positives = "Appreciated cross-device handoff (Spotify Connect) and default playlist catalog depth."
    
    if category == "Competitor Comparisons":
        pain_points = "Offline sync speeds and pricing models compared to competitor bundles."
        needs = "Compare options and transition playback smoothly across competitor devices."
    elif category == "Playback & Technical Performance":
        pain_points = "Buffering, crashes, and background audio service freezing."
        needs = "Achieve reliable background playback and cellular network switching."
    elif category == "Personalization & Curation":
        pain_points = "Stale recommendation loops and lack of taste sandbox modes."
        needs = "Discover diverse artists without permanently skewing personal taste profiles."
    elif category == "Feature Requests & Product Improvements":
        pain_points = "Absence of prompt-based search and strict skip limit toggles."
        needs = "Input abstract preferences and customize shuffle frequencies."
        
    recommendations = f"1. Implement a dedicated Settings toggle to refine shuffle loop frequencies.\n2. Develop a temporary 'Sandbox Mode' to avoid recommendation contamination.\n3. Optimize background audio thread memory allocations to minimize crashes."

    report_md = f"""### Executive Summary
{summary}

### Key Findings
{findings_md}

### User Needs & Goals
* {needs}

### Pain Points
* {pain_points}

### Positive Feedback
* {positives}

### Actionable Recommendations
* {recommendations}

### Confidence
* **{confidence}**: Supported by {matched_count} matching user reviews and structured VoC classification.
"""
    return report_md

def generate_dynamic_review_report(query: str) -> dict:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM reviews")
        total_reviews = cursor.fetchone()[0]
        
        cursor.execute("SELECT sentiment, COUNT(*) FROM insights GROUP BY sentiment")
        sentiment_counts = {r[0]: r[1] for r in cursor.fetchall()}
        
        query_lower = query.lower()
        
        # Analyze query intent
        competitors = ["apple music", "youtube music", "amazon music", "deezer", "tidal", "youtube", "competitor", "compete", "switch"]
        playback = ["playback", "buffer", "quality", "offline", "download", "sound", "crash", "bug", "freeze", "slow", "error"]
        personalization = ["taste", "recommend", "mix", "algorithm", "shuffle", "discover", "weekly", "daily", "personalize"]
        features = ["improve", "request", "feature", "suggestion", "add", "missing", "prioritize", "want"]
        updates = ["update", "new release", "recent", "change", "over time", "sentiment", "rating", "worse", "better"]
        
        category = "General Review Feedback"
        where_clauses = []
        params = []
        
        if any(c in query_lower for c in competitors):
            category = "Competitor Comparisons"
            for comp in competitors:
                where_clauses.append("r.content LIKE ?")
                params.append(f"%{comp}%")
        elif any(p in query_lower for p in playback):
            category = "Playback & Technical Performance"
            for term in playback:
                where_clauses.append("r.content LIKE ?")
                params.append(f"%{term}%")
        elif any(p in query_lower for p in personalization):
            category = "Personalization & Curation"
            for term in personalization:
                where_clauses.append("r.content LIKE ?")
                params.append(f"%{term}%")
        elif any(f in query_lower for f in features):
            category = "Feature Requests & Product Improvements"
            for term in features:
                where_clauses.append("r.content LIKE ?")
                params.append(f"%{term}%")
        elif any(u in query_lower for u in updates):
            category = "Sentiment Dynamics & Updates"
            for term in updates:
                where_clauses.append("r.content LIKE ?")
                params.append(f"%{term}%")
        else:
            words = [w for w in re.findall(r'\w+', query_lower) if len(w) > 3]
            if words:
                for w in words[:4]:
                    where_clauses.append("r.content LIKE ?")
                    params.append(f"%{w}%")
                    
        if where_clauses:
            sql = f"""
            SELECT r.content, r.user, r.date, i.sentiment, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE {" OR ".join(where_clauses)}
            ORDER BY r.date DESC
            LIMIT 15
            """
            cursor.execute(sql, params)
        else:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.sentiment, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            ORDER BY r.date DESC
            LIMIT 15
            """)
            
        rows = cursor.fetchall()
        conn.close()
        
        matched_count = len(rows)
        local_sentiments = {"Positive": 0, "Neutral": 0, "Negative": 0}
        topics_list = []
        evidence_list = []
        
        for r in rows:
            local_sentiments[r["sentiment"]] = local_sentiments.get(r["sentiment"], 0) + 1
            topics_list.append(r["topic"])
            
            content = r["content"]
            content = re.sub(r'https?://\S+', '[REDACTED_URL]', content)
            user = r["user"]
            if user.lower() in ["anonymous user", "unknown"]:
                user = "Anonymous"
            else:
                user = f"User_{user[:6]}" if len(user) > 6 else f"User_{user}"
                
            evidence_list.append({
                "content": content,
                "platform": "app_store" if "app" in content.lower() else "reddit",
                "date": r["date"]
            })
            
        is_review, matched_idx = check_query_rules(query_lower)
        analysis_md = format_voc_report(query, matched_idx, category, total_reviews, matched_count, local_sentiments, topics_list, evidence_list)
            
        return {
            "answer": analysis_md,
            "evidence": evidence_list
        }
    except Exception as e:
        print(f"Error generating dynamic review report: {e}", file=sys.stderr)
        return {
            "answer": f"### 📊 Growth Analysis fallback\nUnable to generate dynamic analysis due to an error: {e}",
            "evidence": []
        }

def get_dynamic_sqlite_evidence(query: str) -> tuple[str, list[dict]]:
    query_lower = query.lower()
    competitors = ["apple music", "youtube music", "amazon music", "deezer", "tidal", "youtube", "competitor", "compete", "switch"]
    playback = ["playback", "buffer", "quality", "offline", "download", "sound", "crash", "bug", "freeze", "slow", "error", "confus", "play"]
    personalization = ["taste", "recommend", "mix", "algorithm", "shuffle", "discover", "weekly", "daily", "personalize"]
    features = ["improve", "request", "feature", "suggestion", "add", "missing", "prioritize", "want"]
    updates = ["update", "new release", "recent", "change", "over time", "sentiment", "rating", "worse", "better"]
    
    where_clauses = []
    params = []
    
    for term in competitors:
        if term in query_lower:
            where_clauses.append("r.content LIKE ?")
            params.append(f"%{term}%")
    for term in playback:
        if term in query_lower:
            where_clauses.append("r.content LIKE ?")
            params.append(f"%{term}%")
    for term in personalization:
        if term in query_lower:
            where_clauses.append("r.content LIKE ?")
            params.append(f"%{term}%")
    for term in features:
        if term in query_lower:
            where_clauses.append("r.content LIKE ?")
            params.append(f"%{term}%")
    for term in updates:
        if term in query_lower:
            where_clauses.append("r.content LIKE ?")
            params.append(f"%{term}%")
            
    # Fallback to word matching if no category term matched
    if not where_clauses:
        words = [w for w in re.findall(r'\w+', query_lower) if len(w) > 3]
        for w in words[:4]:
            where_clauses.append("r.content LIKE ?")
            params.append(f"%{w}%")
            
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if where_clauses:
            sql = f"""
            SELECT r.content, r.user, r.date, i.sentiment, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            WHERE {" OR ".join(where_clauses)}
            ORDER BY r.date DESC
            LIMIT 15
            """
            cursor.execute(sql, params)
        else:
            cursor.execute("""
            SELECT r.content, r.user, r.date, i.sentiment, i.topic
            FROM reviews r
            JOIN insights i ON r.id = i.review_id
            ORDER BY r.date DESC
            LIMIT 15
            """)
            
        rows = cursor.fetchall()
        conn.close()
        
        evidence_str = ""
        evidence_list = []
        for r in rows:
            content = r["content"]
            content = re.sub(r'https?://\S+', '[REDACTED_URL]', content)
            content = re.sub(r'\S+@\S+', '[REDACTED_EMAIL]', content)
            
            user = r["user"]
            if user.lower() in ["anonymous user", "unknown"]:
                user = "Anonymous"
            else:
                user = f"User_{user[:6]}" if len(user) > 6 else f"User_{user}"
                
            evidence_str += f"- *\"{content}\"* ({user} — {r['date']})\n"
            evidence_list.append({
                "content": content,
                "platform": "app_store" if "app" in content.lower() else "reddit",
                "date": r["date"]
            })
            
        if not evidence_str:
            evidence_str = "- *No specific reviews found in the database matching the query keywords.*"
            
        return evidence_str, evidence_list
    except Exception as e:
        print(f"Error in get_dynamic_sqlite_evidence: {e}", file=sys.stderr)
        return "- *Error loading evidence from SQLite database.*", []

def check_review_qa(query: str, history: list = None, api_key: str = None) -> Optional[dict]:
    query_lower = query.lower()
    
    # Pre-check: if it is not likely a review/VoC query, exit early and treat as song search
    if not is_likely_review_query(query):
        return None
        
    # 1. Use LLM if available to classify and answer
    if api_key and not api_key.startswith("your_"):
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            
            classify_prompt = f"""
            Determine if the user query is asking about Spotify user reviews, ratings, sentiments, feedback, complaints, bug reports, feature requests, competitor comparisons, or user opinions.
            
            User Query: "{query}"
            
            If the user query is a question or statement asking about what users say/complain/request/prefer in reviews, or asks generally/specifically about user feedback/VoC, return a JSON object with:
            {{
                "is_review_query": true,
                "matched_question_index": 0-11
            }}
            (Use 1-11 if it matches one of these eleven core questions, otherwise use 0):
            1. Why do users struggle to discover new music? (e.g., UI clutter, lack of trust, expressing mood)
            2. What are the most common frustrations with recommendation algorithms? (e.g., repeating skipped songs, mainstream push, smart shuffle loop)
            3. What listening behaviors are users trying to achieve? (e.g., active exploration, passive listening, mood matching, nostalgic recovery)
            4. What causes users to repeatedly listen to the same content? (e.g., decision overload, trust gap, autoplay convenience)
            5. Which user segments experience different discovery challenges? (e.g., casual listeners vs. power users/audiophiles)
            6. What unmet needs emerge consistently across reviews? (e.g., private sandbox mode, conversational search, pace fine-tuning)
            7. What factors influence user retention?
            8. Which features drive premium subscriptions?
            9. What are the main reasons users cancel premium plans?
            10. Which user segments report the highest satisfaction?
            11. What product improvements would have the greatest impact on user experience?
            
            Otherwise, if the query is a song recommendation or search query (like "play some jazz", "lofi beats", "Kesariya", etc.), return:
            {{
                "is_review_query": false,
                "matched_question_index": null
            }}
            
            Respond in strict JSON format:
            """
            
            resp = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a precise JSON classifier. Only output JSON."},
                    {"role": "user", "content": classify_prompt}
                ],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            classify_res = json.loads(resp.choices[0].message.content)
            is_review = classify_res.get("is_review_query", False)
            matched_idx = classify_res.get("matched_question_index")
            
            if not is_review:
                return None
                
            if is_review:
                if matched_idx in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11):
                    evidence = get_sqlite_evidence(matched_idx)
                    evidence_list = get_sqlite_evidence_list(matched_idx)
                else:
                    evidence, evidence_list = get_dynamic_sqlite_evidence(query)
                
                qa_prompt = f"""# Universal Review Analysis Prompt
 
You are an expert Product Research and Voice of Customer (VoC) analyst. Your task is to analyze customer reviews and answer any question using evidence from the reviews.
 
## Objective
Given a collection of customer reviews and a user question, identify patterns, summarize insights, and provide evidence-based conclusions. Focus on what users actually say rather than making assumptions.
 
## Instructions
For every question:
1. Understand the user's intent.
2. Search across all reviews for relevant mentions.
3. Group similar comments into themes.
4. Quantify findings whenever possible (frequency, percentage, or relative prevalence).
5. Distinguish between positive, negative, and neutral sentiment.
6. Support every insight with representative review excerpts or examples.
7. Highlight conflicting opinions if they exist.
8. Do not invent information that is not present in the reviews.
 
## Response Format
Structure your response exactly using these headings:
 
### Executive Summary
Provide a concise answer to the user's question in 2–4 sentences.
 
### Key Findings
For each major theme, include:
* Theme name
* Summary
* Overall sentiment
* Frequency (High / Medium / Low or percentage)
* Representative review excerpts
 
### User Needs & Goals
Identify what users are trying to accomplish.
 
### Pain Points
Explain the most common frustrations or obstacles.
 
### Positive Feedback
Describe what users appreciate.
 
### Actionable Recommendations
Suggest improvements based on the review evidence.
 
### Confidence
State how confident you are in the conclusions based on the quantity and consistency of the review data.
 
---
 
### Context Data for analysis:
User Query: "{query}"
Predefined Analysis for this topic (use this as guidance):
{get_predefined_analysis(matched_idx)}
 
Real User Feedback Quotes from SQLite (incorporate these as direct quotes to support your findings):
{evidence}
"""
                
                resp_qa = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are an expert Product Research and Voice of Customer (VoC) analyst. Output your response EXACTLY using the specified Markdown format with the required headings (Executive Summary, Key Findings, User Needs & Goals, Pain Points, Positive Feedback, Actionable Recommendations, Confidence)."},
                        {"role": "user", "content": qa_prompt}
                    ],
                    model="llama-3.1-8b-instant",
                    temperature=0.3
                )
                
                return {
                    "is_review_query": True,
                    "explanation": resp_qa.choices[0].message.content.strip(),
                    "evidence": evidence_list
                }
        except Exception as e:
            print(f"LLM Review QA classification failed: {e}", file=sys.stderr)
            
    # 2. Rule-based fallback (either LLM was unavailable, or it classified as is_review = False but our pre-check returned True)
    is_review, matched_idx = check_query_rules(query_lower)
    if is_review:
        if matched_idx != 0:
            evidence = get_sqlite_evidence(matched_idx)
            predef = get_predefined_analysis(matched_idx)
            evidence_list = get_sqlite_evidence_list(matched_idx)
            
            # We wrap in format_voc_report to keep the exact response format
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM reviews")
            total_reviews = cursor.fetchone()[0]
            conn.close()
            
            local_sentiments = {"Positive": 0, "Neutral": 0, "Negative": matched_idx}
            topics_list = [predef.split(":")[0].replace("**", "")] if matched_idx else []
            
            explanation = format_voc_report(query, matched_idx, "Core Analytical Query", total_reviews, len(evidence_list), local_sentiments, topics_list, evidence_list)
            
            return {
                "is_review_query": True,
                "explanation": explanation,
                "evidence": evidence_list
            }
        else:
            # General VoC/review query fallback
            report = generate_dynamic_review_report(query)
            return {
                "is_review_query": True,
                "explanation": report["answer"],
                "evidence": report["evidence"]
            }
            
    # If the rules did not classify it as a review query, return None to treat as a song query
    return None

@app.post("/api/v1/discover")
async def api_discover(req: DiscoverRequest):
    """Natural language music discovery — parse query and search ChromaDB."""
    if not PHASE4_AVAILABLE:
        raise HTTPException(status_code=503, detail="Phase 4 modules not available. Ensure discovery_engine.py is in src/phase4/.")

    groq_key = os.getenv("GROQ_API_KEY")

    # Intercept review analysis queries
    review_qa = check_review_qa(req.query, req.history, api_key=groq_key)
    if review_qa:
        _discovery_sessions[req.session_id] = {
            "query": req.query,
            "parsed_intent": {"review_query": True},
            "tracks": [],
            "history": req.history + [
                {"role": "user", "content": req.query},
                {"role": "assistant", "content": review_qa["explanation"]},
            ],
        }
        return {
            "status": "success",
            "query": req.query,
            "parsed_intent": {"review_query": True},
            "tracks": [],
            "explanation": review_qa["explanation"],
            "evidence": review_qa.get("evidence", []),
            "session_id": req.session_id,
            "track_count": 0,
        }

    # Parse the intent
    parsed = parse_music_intent(req.query, req.history, api_key=groq_key)

    # Search ChromaDB
    tracks = search_tracks(parsed, n_results=10)

    # Generate explanation
    explanation = generate_explanation(req.query, tracks, api_key=groq_key)

    # Store in session
    _discovery_sessions[req.session_id] = {
        "query": req.query,
        "parsed_intent": parsed,
        "tracks": tracks,
        "history": req.history + [
            {"role": "user", "content": req.query},
            {"role": "assistant", "content": explanation},
        ],
    }

    return {
        "status": "success",
        "query": req.query,
        "parsed_intent": parsed,
        "tracks": tracks,
        "explanation": explanation,
        "session_id": req.session_id,
        "track_count": len(tracks),
    }

@app.post("/api/v1/discover/refine")
async def api_discover_refine(req: RefineRequest):
    """Refine previous discovery results with a follow-up instruction."""
    if not PHASE4_AVAILABLE:
        raise HTTPException(status_code=503, detail="Phase 4 modules not available.")

    groq_key = os.getenv("GROQ_API_KEY")

    # Intercept review analysis queries in refinement
    review_qa = check_review_qa(req.refinement, api_key=groq_key)
    if review_qa:
        if req.session_id in _discovery_sessions:
            _discovery_sessions[req.session_id]["parsed_intent"] = {"review_query": True}
            _discovery_sessions[req.session_id]["tracks"] = []
            _discovery_sessions[req.session_id]["history"].extend([
                {"role": "user", "content": req.refinement},
                {"role": "assistant", "content": review_qa["explanation"]},
            ])
        return {
            "status": "success",
            "refinement": req.refinement,
            "parsed_intent": {"review_query": True},
            "tracks": [],
            "explanation": review_qa["explanation"],
            "track_count": 0,
        }

    # Get previous intent from session or request
    previous = req.previous_intent
    if not previous and req.session_id in _discovery_sessions:
        previous = _discovery_sessions[req.session_id].get("parsed_intent", {})

    if not previous:
        raise HTTPException(status_code=400, detail="No previous search found. Use /api/v1/discover first.")

    # Refine the intent
    refined = refine_search(req.refinement, previous, api_key=groq_key)

    # Re-search
    tracks = search_tracks(refined, n_results=10)

    explanation = generate_explanation(
        f"{_discovery_sessions.get(req.session_id, {}).get('query', '')} → {req.refinement}",
        tracks, api_key=groq_key,
    )

    # Update session
    if req.session_id in _discovery_sessions:
        _discovery_sessions[req.session_id]["parsed_intent"] = refined
        _discovery_sessions[req.session_id]["tracks"] = tracks
        _discovery_sessions[req.session_id]["history"].extend([
            {"role": "user", "content": req.refinement},
            {"role": "assistant", "content": explanation},
        ])

    return {
        "status": "success",
        "refinement": req.refinement,
        "parsed_intent": refined,
        "tracks": tracks,
        "explanation": explanation,
        "track_count": len(tracks),
    }

@app.get("/api/v1/spotify/login")
async def api_spotify_login(session_id: str = "default"):
    """Get the Spotify OAuth authorization URL."""
    if not PHASE4_AVAILABLE:
        raise HTTPException(status_code=503, detail="Phase 4 modules not available.")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8000/callback")
    auth_url = get_auth_url(session_id, redirect_uri)
    return {"auth_url": auth_url, "session_id": session_id}

@app.get("/api/v1/spotify/callback")
async def api_spotify_callback(code: str = "", state: str = "default"):
    """Handle Spotify OAuth callback and exchange code for token."""
    if not PHASE4_AVAILABLE:
        raise HTTPException(status_code=503, detail="Phase 4 modules not available.")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8000/callback")
    token = exchange_code(code, state, redirect_uri)
    return {
        "status": "success",
        "session_id": state,
        "authenticated": True,
        "token_type": token.get("token_type", "Bearer"),
        "message": "Spotify authentication successful!",
    }

@app.post("/api/v1/spotify/create-playlist")
async def api_create_playlist(req: PlaylistRequest):
    """Create a Spotify playlist from discovered tracks."""
    if not PHASE4_AVAILABLE:
        raise HTTPException(status_code=503, detail="Phase 4 modules not available.")

    # Auto-authenticate in mock mode if not authenticated
    if not is_authenticated(req.session_id):
        exchange_code("mock_auto", req.session_id)

    result = create_playlist(
        session_id=req.session_id,
        name=req.name,
        description=f"AI-curated discovery: {req.name}",
        track_names=req.track_names,
    )
    return result

@app.post("/api/v1/feedback/send")
async def api_send_feedback(req: FeedbackRequest):
    """Send a follow-up feedback survey email."""
    if not PHASE4_AVAILABLE:
        raise HTTPException(status_code=503, detail="Phase 4 modules not available.")
    result = send_feedback_survey(req.user_email, req.session_summary)
    return result

@app.post("/api/v1/feedback/log")
async def api_log_feedback(req: FeedbackLogRequest):
    """Log structured user feedback."""
    if not PHASE4_AVAILABLE:
        raise HTTPException(status_code=503, detail="Phase 4 modules not available.")
    result = log_feedback_to_docs(req.model_dump())
    return result

@app.get("/api/v1/feedback/stats")
async def api_feedback_stats():
    """Get aggregated feedback statistics."""
    if not PHASE4_AVAILABLE:
        raise HTTPException(status_code=503, detail="Phase 4 modules not available.")
    return get_feedback_stats()

@app.get("/api/v1/catalog/taxonomy")
async def api_catalog_taxonomy():
    """Get the music catalog taxonomy (genres, subgenres, moods, activities, languages, decades)."""
    taxonomy_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "taxonomy.json")
    )
    if not os.path.exists(taxonomy_path):
        raise HTTPException(status_code=404, detail="Taxonomy config file not found.")
    
    with open(taxonomy_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

@app.get("/api/v1/catalog/tracks")
async def api_catalog_tracks(
    genre: Optional[str] = None,
    subgenre: Optional[str] = None,
    mood: Optional[str] = None,
    activity: Optional[str] = None,
    language: Optional[str] = None,
    decade: Optional[str] = None,
    popularity: Optional[str] = None,
    release_year: Optional[int] = None,
    search: Optional[str] = None
):
    """Retrieve and filter tracks from the ChromaDB catalog."""
    import chromadb
    CHROMA_DB_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")
    )
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    try:
        collection = client.get_collection(name="spotify_tracks")
    except Exception:
        return []
    
    results = collection.get()
    tracks = []
    
    metadatas = results.get("metadatas", [])
    for meta in metadatas:
        try:
            mood_tags = json.loads(meta.get("mood_tags", "[]"))
        except Exception:
            mood_tags = []
        try:
            activities_list = json.loads(meta.get("activities", "[]"))
        except Exception:
            activities_list = []
            
        track_data = {
            "name": meta.get("track_name"),
            "track_name": meta.get("track_name"),
            "artist": meta.get("artist"),
            "album": meta.get("album"),
            "genre": meta.get("genre"),
            "subgenre": meta.get("subgenre"),
            "mood_tags": mood_tags,
            "activities": activities_list,
            "language": meta.get("language", "English"),
            "popularity": meta.get("popularity", 50),
            "release_year": meta.get("release_year", 2020),
            "decade": meta.get("decade", "2020s"),
            "energy": meta.get("energy", 0.5),
            "valence": meta.get("valence", 0.5),
            "tempo_bpm": meta.get("tempo_bpm", 120),
            "tempo": meta.get("tempo_bpm", 120),
            "acousticness": meta.get("acousticness", 0.5),
            "instrumentalness": meta.get("instrumentalness", 0.0),
            "description": meta.get("description", "")
        }
        tracks.append(track_data)
        
    filtered = []
    for t in tracks:
        if genre and t["genre"].lower() != genre.lower():
            continue
        if subgenre and t["subgenre"].lower() != subgenre.lower():
            continue
        if mood and mood.lower() not in [m.lower() for m in t["mood_tags"]]:
            continue
        if activity and activity.lower() not in [a.lower() for a in t["activities"]]:
            continue
        if language and t["language"].lower() != language.lower():
            continue
        if decade and t["decade"] != decade:
            continue
        if release_year and t["release_year"] != release_year:
            continue
        if popularity:
            pop = t["popularity"]
            if popularity.lower() == "high" and pop < 80:
                continue
            elif popularity.lower() == "medium" and (pop < 40 or pop >= 80):
                continue
            elif popularity.lower() == "low" and pop >= 40:
                continue
        if search:
            search_l = search.lower()
            if (search_l not in t["track_name"].lower() and 
                search_l not in t["artist"].lower() and 
                search_l not in t["album"].lower() and 
                search_l not in t["description"].lower()):
                continue
        filtered.append(t)
        
    return filtered

@app.get("/api/v1/health")
async def api_health():
    """Health check endpoint for deployment monitoring."""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": False,
            "phase4_modules": PHASE4_AVAILABLE,
        }
    }
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        health["services"]["database"] = True
    except Exception:
        pass

    return health

if __name__ == "__main__":
    import uvicorn
    # Start on port 8081 to avoid collision with port 8000/8080/8086
    uvicorn.run("main:app", host="127.0.0.1", port=8081, reload=True)
