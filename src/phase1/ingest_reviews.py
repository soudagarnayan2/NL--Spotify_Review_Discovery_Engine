import os
import sys
import json
import argparse
import random
import re
from datetime import datetime, timedelta
from app_store_scraper import AppStore
from google_play_scraper import Sort, reviews as play_reviews
from langdetect import detect

# Mock data templates for social platforms
REDDIT_TEMPLATES = [
    "I'm so tired of Spotify playing the same 15 songs on repeat. My Daily Mix 1 and 2 are literally just songs from my own liked playlist. What is the point? I want to discover actual new music, not just listen to the same algorithmic loop.",
    "Does anyone else feel like Discover Weekly has gotten stale? It used to find hidden gems, but now it just recommends songs I already skipped or artists I already follow. It's like the algorithm got lazy and only suggests 'safe' choices.",
    "Is there a way to clear or pause search history so a single joke song doesn't ruin my recommendations? I listened to one sea shanty track and now my entire feed is filled with folk sea shanties. There is no sandbox or temporary mode.",
    "Why does Spotify's recommendation engine keep pushing mainstream artists? I listen to indie shoegaze, but my Release Radar is full of pop-adjacent artists. The collaborative filtering bubble is real and hard to escape.",
    "We need a feature to adjust exploration versus exploitation. Sometimes I just want to hear completely random music in a specific genre without having to search external subreddits or blogs. Discovering music shouldn't feel like a chore.",
    "Decision paralysis is real. I spend 20 minutes scrolling through my home feed trying to find something 'new' that fits my current vibe, only to give up and play my 2-year-old road trip playlist again.",
    "I've been using Spotify since 2015. Over time, my taste expanded, but my recommendations stayed the same. It keeps pushing nostalgic tracks rather than helping me evaluate and expand my taste.",
    "The lack of context-awareness is frustrating. It plays high-energy workout songs in my focus playlist just because I listened to them yesterday. It doesn't understand the cognitive state I am in."
]

TWITTER_TEMPLATES = [
    "Spotify's shuffle is broken. I have 800 songs in my playlist, why does it play the same 20 tracks every single time? #SpotifyProblems",
    "Discover Weekly is just recommending songs I have literally already liked. Algorithmic exploitation at its finest. Give me something fresh! 🙄",
    "I skipped this song 5 times this week. Why is Spotify still playing it on my smart shuffle? It does not learn my active feedback.",
    "Desperately need a 'private listening' button that actually works so my kids' music doesn't pollute my recommendations. #spotify",
    "Too much decision overload on Spotify. I wish I could just tell an AI: 'give me songs that sound like driving in the rain at 2 AM' and get a solid list.",
    "Spotify's recommendation engine is great at personalization but terrible at exploration. I am trapped in a bubble. Help!",
    "Why is it so hard to find new indie artists on Spotify? The algorithm only suggests what's popular or what I've already heard.",
    "Spent my entire morning commute skipping songs on Spotify. Recommendation algorithm is completely out of sync with my current mood."
]

# Fallback templates for store scrapers in case of API rate limits/blocks
APP_STORE_TEMPLATES = [
    "The recommendations on this app are terrible lately. It keeps playing songs from my library instead of finding new tracks. Smart shuffle is just a repeat button. 1 star.",
    "I love the UI, but the algorithm is so repetitive. It just plays the same 3 artists over and over. Please fix the recommendation loop. 3 stars.",
    "Cannot discover new music anymore. Every playlist is just an echo chamber of what I listened to last week. I miss when Discover Weekly actually worked. 2 stars.",
    "Every single Discover Weekly update is full of songs I've skipped 100 times. Why does the app keep pushing them? Safe recommendations are boring.",
    "Decision paralysis has ruined this app for me. I spend more time scrolling for music than actually listening. Needs a better mood/context filter."
]

PLAY_STORE_TEMPLATES = [
    "Latest update made recommendations even worse. Smart shuffle keeps repeating the same tracks. Please give us actual discovery tools. 2 stars.",
    "I skipped a song 10 times, yet it shows up in every single daily mix. Spotify personalization has become very lazy and repetitive.",
    "Algorithmic bubble is real. I am tired of listening to the same tracks. The app needs a way to discover new genres safely without ruining my profile.",
    "The app has millions of tracks but I only hear the same 50. Discover weekly is just recommending my own liked songs now. 1 star.",
    "Too much clutter in the home feed. I just want to query: 'give me lofi beats for sleeping' and play it, but I get pushed podcasts and repeat playlists."
]

def clean_and_normalize_review(content):
    if not content:
        return None
        
    # 1. Remove emojis and pictographs
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
        # Simple fallback for standard English chars
        ascii_chars = sum(1 for c in cleaned if ord(c) < 128)
        if len(cleaned) > 0 and (ascii_chars / len(cleaned)) < 0.8:
            return None
            
    return cleaned

def generate_fallback_reviews(platform, count):
    templates = APP_STORE_TEMPLATES if platform == "app_store" else PLAY_STORE_TEMPLATES
    processed = []
    for i in range(count * 2): # Generate more to ensure we satisfy filtering constraints
        template = random.choice(templates)
        random_days = random.randint(0, 30)
        review_date = datetime.now() - timedelta(days=random_days)
        user_num = random.randint(100, 9999)
        processed.append({
            "id": f"mock_{platform}_{i}_{int(datetime.now().timestamp())}",
            "platform": platform,
            "rating": random.choice([1, 2, 3]),
            "content": template,
            "date": review_date.strftime('%Y-%m-%d'),
            "user": f"{platform}_user_{user_num}"
        })
    return processed

def fetch_app_store_reviews(limit=20):
    print(f"Fetching reviews from Apple App Store (target: {limit})...")
    processed = []
    try:
        # Spotify App ID: 324684580
        spotify_app = AppStore(country='us', app_name='spotify-music', app_id=324684580)
        spotify_app.review(how_many=limit * 2) # Fetch extra to account for filtering
        
        raw_reviews = spotify_app.reviews
        for i, rev in enumerate(raw_reviews):
            date_val = rev.get('date')
            if isinstance(date_val, datetime):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val)
                
            processed.append({
                "id": f"app_store_{i}_{int(datetime.now().timestamp())}",
                "platform": "app_store",
                "rating": int(rev.get('rating', 3)),
                "content": rev.get('review', '').strip(),
                "date": date_str,
                "user": rev.get('userName', 'Anonymous User').strip()
            })
    except Exception as e:
        print(f"Error fetching from Apple App Store: {e}.", file=sys.stderr)
        
    if not processed:
        print("Apple App Store scraping returned 0 reviews. Applying fallback mock generation...")
        processed = generate_fallback_reviews("app_store", limit)
        
    return processed

def fetch_google_play_reviews(limit=20):
    print(f"Fetching reviews from Google Play Store (target: {limit})...")
    processed = []
    try:
        # Spotify Package Name: com.spotify.music
        results, _ = play_reviews(
            'com.spotify.music',
            lang='en',
            country='us',
            sort=Sort.NEWEST,
            count=limit * 2 # Fetch extra to account for filtering
        )
        
        for i, rev in enumerate(results):
            date_val = rev.get('at')
            if isinstance(date_val, datetime):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val)
                
            processed.append({
                "id": f"play_store_{rev.get('reviewId', i)}",
                "platform": "play_store",
                "rating": int(rev.get('score', 3)),
                "content": rev.get('content', '').strip(),
                "date": date_str,
                "user": rev.get('userName', 'Anonymous User').strip()
            })
    except Exception as e:
        print(f"Error fetching from Google Play Store: {e}.", file=sys.stderr)
        
    if not processed:
        print("Google Play Store scraping returned 0 reviews. Applying fallback mock generation...")
        processed = generate_fallback_reviews("play_store", limit)
        
    return processed

def generate_mock_reviews(platform, count=20):
    print(f"Generating mock reviews for {platform} (target: {count})...")
    templates = REDDIT_TEMPLATES if platform == "reddit" else TWITTER_TEMPLATES
    processed = []
    
    for i in range(count * 2): # Generate more to ensure we satisfy filtering constraints
        template = random.choice(templates)
        additions = ["", " Anyone else?", " Totally frustrating.", " Let me know if you know a fix.", " SMH.", " Why?", " :("]
        content = template + random.choice(additions)
        
        random_days = random.randint(0, 30)
        review_date = datetime.now() - timedelta(days=random_days)
        
        user_num = random.randint(100, 9999)
        username = f"user_{platform}_{user_num}" if platform == "twitter" else f"u/reddit_listener_{user_num}"
        
        processed.append({
            "id": f"mock_{platform}_{i}_{int(datetime.now().timestamp())}",
            "platform": platform,
            "rating": None,
            "content": content,
            "date": review_date.strftime('%Y-%m-%d'),
            "user": username
        })
        
    return processed

def main():
    parser = argparse.ArgumentParser(description="Ingest Spotify reviews from app stores and mock social media sources.")
    parser.add_argument("--limit-scraped", type=int, default=500, help="Number of reviews to scrape per app store (default: 500)")
    parser.add_argument("--limit-mocked", type=int, default=500, help="Number of mock reviews to generate per social platform (default: 500)")
    parser.add_argument("--output", type=str, default="data/raw_reviews.json", help="Path to save the output JSON file (default: data/raw_reviews.json)")
    
    args = parser.parse_args()
    
    raw_accumulated = []
    
    # 1. Fetch Apple App Store reviews
    raw_accumulated.extend(fetch_app_store_reviews(args.limit_scraped))
    
    # 2. Fetch Google Play Store reviews
    raw_accumulated.extend(fetch_google_play_reviews(args.limit_scraped))
    
    # 3. Generate Mock Reddit reviews
    raw_accumulated.extend(generate_mock_reviews("reddit", args.limit_mocked))
    
    # 4. Generate Mock Twitter reviews
    raw_accumulated.extend(generate_mock_reviews("twitter", args.limit_mocked))
    
    # Normalization & Filtering (English, >= 6 words, no emojis)
    print("\nRunning normalization and filtering (>= 6 words, no emojis, English only)...")
    normalized_reviews = []
    skipped_count = 0
    
    # Track limits per platform to ensure we get exactly the requested counts if possible
    counts_by_platform = {"app_store": 0, "play_store": 0, "reddit": 0, "twitter": 0}
    target_limits = {
        "app_store": args.limit_scraped,
        "play_store": args.limit_scraped,
        "reddit": args.limit_mocked,
        "twitter": args.limit_mocked
    }
    
    for rev in raw_accumulated:
        platform = rev.get("platform")
        if counts_by_platform[platform] >= target_limits[platform]:
            continue
            
        cleaned_content = clean_and_normalize_review(rev.get("content", ""))
        if cleaned_content is not None:
            rev["content"] = cleaned_content
            normalized_reviews.append(rev)
            counts_by_platform[platform] += 1
        else:
            skipped_count += 1
            
    print(f"Normalization complete. Retained {len(normalized_reviews)} reviews, skipped {skipped_count} reviews.")
    print(f"Final Counts: {counts_by_platform}")
    
    # Standardize output path and create directories
    output_path = os.path.abspath(args.output)
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
        
    # Write merged reviews to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(normalized_reviews, f, indent=2, ensure_ascii=False)
        
    print(f"\nCompleted! Total normalized reviews saved: {len(normalized_reviews)}")
    print(f"Dataset successfully saved to: {output_path}")

if __name__ == "__main__":
    main()
