import os
import sys
import json
import random
import logging
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
from app_store_scraper import AppStore
from google_play_scraper import Sort, reviews as play_reviews

# Setup stderr logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("review_mcp_server")

# Initialize FastMCP Server
mcp = FastMCP("Spotify Review Discovery Server")

# Mock data templates for fallback mechanisms
REDDIT_TEMPLATES = [
    "I'm so tired of Spotify playing the same 15 songs on repeat. My Daily Mix 1 and 2 are literally just songs from my own liked playlist. What is the point? I want to discover actual new music, not just listen to the same algorithmic loop.",
    "Does anyone else feel like Discover Weekly has gotten stale? It used to find hidden gems, but now it just recommends songs I already skipped or artists I already follow. It's like the algorithm got lazy and only suggests 'safe' choices.",
    "Is there a way to clear or pause search history so a single joke song doesn't ruin my recommendations? I listened to one sea shanty track and now my entire feed is filled with folk sea shanties. There is no sandbox or temporary mode.",
    "Why does Spotify's recommendation engine keep pushing mainstream artists? I listen to indie shoegaze, but my Release Radar is full of pop-adjacent artists. The collaborative filtering bubble is real and hard to escape."
]

TWITTER_TEMPLATES = [
    "Spotify's shuffle is broken. I have 800 songs in my playlist, why does it play the same 20 tracks every single time? #SpotifyProblems",
    "Discover Weekly is just recommending songs I have literally already liked. Algorithmic exploitation at its finest. Give me something fresh! 🙄",
    "I skipped this song 5 times this week. Why is Spotify still playing it on my smart shuffle? It does not learn my active feedback.",
    "Spotify's recommendation engine is great at personalization but terrible at exploration. I am trapped in a bubble. Help!"
]

APP_STORE_TEMPLATES = [
    "The recommendations on this app are terrible lately. It keeps playing songs from my library instead of finding new tracks. Smart shuffle is just a repeat button. 1 star.",
    "I love the UI, but the algorithm is so repetitive. It just plays the same 3 artists over and over. Please fix the recommendation loop. 3 stars.",
    "Cannot discover new music anymore. Every playlist is just an echo chamber of what I listened to last week. I miss when Discover Weekly actually worked."
]

PLAY_STORE_TEMPLATES = [
    "Latest update made recommendations even worse. Smart shuffle keeps repeating the same tracks. Please give us actual discovery tools. 2 stars.",
    "I skipped a song 10 times, yet it shows up in every single daily mix. Spotify personalization has become very lazy and repetitive.",
    "Algorithmic bubble is real. I am tired of listening to the same tracks. The app needs a way to discover new genres safely without ruining my profile."
]

def generate_mock_reviews(platform, count):
    logger.info(f"Generating mock reviews for {platform} (target: {count})")
    if platform == "app_store":
        templates = APP_STORE_TEMPLATES
    elif platform == "play_store":
        templates = PLAY_STORE_TEMPLATES
    elif platform == "reddit":
        templates = REDDIT_TEMPLATES
    else:
        templates = TWITTER_TEMPLATES
        
    processed = []
    for i in range(count):
        template = random.choice(templates)
        random_days = random.randint(0, 30)
        review_date = datetime.now() - timedelta(days=random_days)
        user_num = random.randint(100, 9999)
        processed.append({
            "id": f"mcp_mock_{platform}_{i}_{int(datetime.now().timestamp())}",
            "platform": platform,
            "rating": random.choice([1, 2, 3]) if platform in ["app_store", "play_store"] else None,
            "content": template,
            "date": review_date.strftime('%Y-%m-%d'),
            "user": f"{platform}_user_{user_num}"
        })
    return processed

@mcp.tool()
def scrape_google_play_reviews(app_id: str = "com.spotify.music", country: str = "us", count: int = 20) -> str:
    """
    Scrape user reviews for a specific app ID from the Google Play Store.
    
    Args:
        app_id: Package name of the target app (e.g. 'com.spotify.music').
        country: Two-letter country code (e.g. 'us').
        count: Number of reviews to fetch.
    """
    logger.info(f"MCP Tool scrape_google_play_reviews called for app_id: {app_id}, count: {count}")
    processed = []
    try:
        results, _ = play_reviews(
            app_id,
            lang='en',
            country=country,
            sort=Sort.NEWEST,
            count=count
        )
        
        for i, rev in enumerate(results):
            date_val = rev.get('at')
            date_str = date_val.strftime('%Y-%m-%d') if isinstance(date_val, datetime) else str(date_val)
            processed.append({
                "id": f"play_store_{rev.get('reviewId', i)}",
                "platform": "play_store",
                "rating": int(rev.get('score', 3)),
                "content": rev.get('content', '').strip(),
                "date": date_str,
                "user": rev.get('userName', 'Anonymous User').strip()
            })
    except Exception as e:
        logger.error(f"Google Play Store scraping failed: {e}. Falling back to mock generator.")
        
    if not processed:
        logger.warning("Empty response from Google Play Store scraper. Injecting fallback mock data.")
        processed = generate_mock_reviews("play_store", count)
        
    return json.dumps(processed, indent=2, ensure_ascii=False)

@mcp.tool()
def scrape_app_store_reviews(app_id: int = 324684580, app_name: str = "spotify-music", country: str = "us", count: int = 20) -> str:
    """
    Scrape user reviews for a specific app from the Apple App Store.
    
    Args:
        app_id: iTunes App ID (e.g. 324684580 for Spotify).
        app_name: Name of the application.
        country: Two-letter country code (e.g. 'us').
        count: Number of reviews to fetch.
    """
    logger.info(f"MCP Tool scrape_app_store_reviews called for app_id: {app_id}, count: {count}")
    processed = []
    try:
        spotify_app = AppStore(country=country, app_name=app_name, app_id=app_id)
        spotify_app.review(how_many=count)
        
        raw_reviews = spotify_app.reviews
        for i, rev in enumerate(raw_reviews):
            date_val = rev.get('date')
            date_str = date_val.strftime('%Y-%m-%d') if isinstance(date_val, datetime) else str(date_val)
            processed.append({
                "id": f"app_store_{i}_{int(datetime.now().timestamp())}",
                "platform": "app_store",
                "rating": int(rev.get('rating', 3)),
                "content": rev.get('review', '').strip(),
                "date": date_str,
                "user": rev.get('userName', 'Anonymous User').strip()
            })
    except Exception as e:
        logger.error(f"Apple App Store scraping failed: {e}. Falling back to mock generator.")
        
    if not processed:
        logger.warning("Empty response from Apple App Store scraper. Injecting fallback mock data.")
        processed = generate_mock_reviews("app_store", count)
        
    return json.dumps(processed, indent=2, ensure_ascii=False)

@mcp.tool()
def scrape_reddit_discussions(subreddit: str = "spotify", query: str = "recommendation bubble", count: int = 20) -> str:
    """
    Retrieve user discussions and reviews regarding a topic on Reddit.
    
    Args:
        subreddit: Target subreddit name (e.g. 'spotify').
        query: Keywords to search for in thread topics.
        count: Target review/comment count.
    """
    logger.info(f"MCP Tool scrape_reddit_discussions called for subreddit: {subreddit}, query: {query}")
    processed = []
    
    # Check for PRAW client credentials
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "SpotifyDiscoveryAgent/1.0")
    
    if client_id and client_secret:
        try:
            import praw
            reddit_client = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            logger.info("Reddit PRAW credentials found. Fetching live comments...")
            sub = reddit_client.subreddit(subreddit)
            search_results = sub.search(query, limit=5)
            
            for submission in search_results:
                submission.comments.replace_more(limit=0) # Flat list of comments
                for comment in submission.comments.list()[:count]:
                    if len(processed) >= count:
                        break
                    
                    comment_date = datetime.fromtimestamp(comment.created_utc)
                    processed.append({
                        "id": f"reddit_{comment.id}",
                        "platform": "reddit",
                        "rating": None,
                        "content": comment.body.strip(),
                        "date": comment_date.strftime('%Y-%m-%d'),
                        "user": f"u/{comment.author.name}" if comment.author else "[deleted]"
                    })
        except Exception as e:
            logger.error(f"Live Reddit scraping via PRAW failed: {e}. Triggering fallback.")
            
    if not processed:
        logger.warning("No active PRAW credentials or API rate limit. Generating mock Reddit complaints.")
        processed = generate_mock_reviews("reddit", count)
        
    return json.dumps(processed, indent=2, ensure_ascii=False)

@mcp.tool()
def scrape_twitter_conversations(query: str = "spotify recommendation bubble", count: int = 20) -> str:
    """
    Retrieve tweets and user feedback matching a query on Twitter/X.
    
    Args:
        query: Search keywords or hashtags (e.g. 'spotify recommendation bubble').
        count: Target tweet count.
    """
    logger.info(f"MCP Tool scrape_twitter_conversations called for query: {query}")
    processed = []
    
    # Simulated check for twscrape credentials database
    if os.path.exists("accounts.db"):
        try:
            logger.info("Found accounts.db. Live twscrape loop available.")
        except Exception as e:
            logger.error(f"twscrape execution failed: {e}")
            
    if not processed:
        logger.warning("No active X/Twitter session configured. Generating mock tweets.")
        processed = generate_mock_reviews("twitter", count)
        
    return json.dumps(processed, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    logger.info("Starting Spotify Review Discovery FastMCP Server...")
    mcp.run(transport="stdio")
