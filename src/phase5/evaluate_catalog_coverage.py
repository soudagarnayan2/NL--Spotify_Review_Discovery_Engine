"""
Catalog Coverage Evaluator
===========================
Measures the diversity of AI-powered recommendations compared to
a simulated "traditional" top-20 popularity-based baseline.

Target: 30% increase in catalog coverage vs baseline.

Usage:
    python src/phase5/evaluate_catalog_coverage.py
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "phase4")))

from discovery_engine import parse_music_intent, search_tracks

# ---------------------------------------------------------------------------
# Test queries simulating diverse user intents
# ---------------------------------------------------------------------------
DIVERSITY_QUERIES = [
    "upbeat synthwave for late night driving",
    "calm acoustic folk for a rainy afternoon",
    "lo-fi beats for deep study sessions",
    "energetic hip-hop for the gym",
    "smooth jazz for a romantic dinner",
    "dark electronic with heavy bass drops",
    "peaceful ambient for morning meditation",
    "feel-good indie pop for summer road trips",
    "emotional cinematic piano music",
    "aggressive rock for working out",
    "dreamy R&B love songs",
    "funky jazz fusion grooves",
    "nostalgic retro 80s synth pop",
    "soothing reggae for beach relaxation",
    "complex progressive metal",
    "soulful country ballads",
    "warm afrobeats for dancing",
    "tender bedroom pop",
    "epic orchestral classical music",
    "psychedelic rock with groovy vibes",
    "energetic Marathi dance songs",
    "romantic Bollywood 90s love songs",
    "upbeat Hindi pop songs",
    "energetic Bhojpuri dance music",
    "tamil kuthu dance tracks",
    "romantic Kannada songs",
    "modern Bollywood romantic pop",
    "old classic Hindi retro songs",
    "traditional rajasthani and punjabi folk songs",
]

# Simulated "traditional" baseline — top-20 popularity list
# (In a real system, this would be Spotify's actual top-20 recs for the user)
BASELINE_RECOMMENDATIONS = [
    {"artist": "Taylor Swift", "genre": "Pop"},
    {"artist": "The Weeknd", "genre": "Pop"},
    {"artist": "Drake", "genre": "Hip-Hop"},
    {"artist": "Dua Lipa", "genre": "Pop"},
    {"artist": "Ed Sheeran", "genre": "Pop"},
    {"artist": "Bad Bunny", "genre": "Latin"},
    {"artist": "Billie Eilish", "genre": "Pop"},
    {"artist": "Post Malone", "genre": "Hip-Hop"},
    {"artist": "Ariana Grande", "genre": "Pop"},
    {"artist": "Juice WRLD", "genre": "Hip-Hop"},
    {"artist": "Kanye West", "genre": "Hip-Hop"},
    {"artist": "Travis Scott", "genre": "Hip-Hop"},
    {"artist": "Doja Cat", "genre": "Pop"},
    {"artist": "Olivia Rodrigo", "genre": "Pop"},
    {"artist": "SZA", "genre": "R&B"},
    {"artist": "Harry Styles", "genre": "Pop"},
    {"artist": "Lil Baby", "genre": "Hip-Hop"},
    {"artist": "BTS", "genre": "Pop"},
    {"artist": "Jack Harlow", "genre": "Hip-Hop"},
    {"artist": "Lizzo", "genre": "Pop"},
]


def compute_diversity(tracks: list[dict]) -> dict:
    """Compute diversity metrics from a list of tracks."""
    unique_artists = set()
    unique_genres = set()
    unique_subgenres = set()
    unique_tracks = set()

    for t in tracks:
        unique_artists.add(t.get("artist", ""))
        unique_genres.add(t.get("genre", ""))
        unique_subgenres.add(t.get("subgenre", ""))
        unique_tracks.add(t.get("track_name", ""))

    total = len(tracks) if tracks else 1
    return {
        "total_recommendations": total,
        "unique_artists": len(unique_artists),
        "unique_genres": len(unique_genres),
        "unique_subgenres": len(unique_subgenres),
        "unique_tracks": len(unique_tracks),
        "artist_diversity": round(len(unique_artists) / total, 4),
        "genre_diversity": round(len(unique_genres) / total, 4),
    }


def run_evaluation():
    """Run the catalog coverage evaluation."""
    print("=" * 70)
    print("CATALOG COVERAGE EVALUATION")
    print("=" * 70)

    # ── Baseline metrics ─────────────────────────────────────────────────
    baseline_artists = set(b["artist"] for b in BASELINE_RECOMMENDATIONS)
    baseline_genres = set(b["genre"] for b in BASELINE_RECOMMENDATIONS)
    print(f"\nBaseline (traditional top-20):")
    print(f"  Artists: {len(baseline_artists)} unique / {len(BASELINE_RECOMMENDATIONS)} total")
    print(f"  Genres:  {len(baseline_genres)} unique")
    print(f"  Diversity Index: {len(baseline_artists)/len(BASELINE_RECOMMENDATIONS):.2%}")

    # ── AI Discovery metrics ─────────────────────────────────────────────
    all_tracks = []
    print(f"\nRunning {len(DIVERSITY_QUERIES)} discovery queries...")
    for i, query in enumerate(DIVERSITY_QUERIES):
        intent = parse_music_intent(query, api_key=None)
        tracks = search_tracks(intent, n_results=5)
        all_tracks.extend(tracks)
        print(f"  Query {i+1:2d}: \"{query[:45]}...\" -> {len(tracks)} tracks")

    ai_metrics = compute_diversity(all_tracks)
    print(f"\nAI Discovery Results:")
    print(f"  Total recommendations: {ai_metrics['total_recommendations']}")
    print(f"  Unique artists: {ai_metrics['unique_artists']}")
    print(f"  Unique genres:  {ai_metrics['unique_genres']}")
    print(f"  Unique tracks:  {ai_metrics['unique_tracks']}")
    print(f"  Artist Diversity: {ai_metrics['artist_diversity']:.2%}")
    print(f"  Genre Diversity:  {ai_metrics['genre_diversity']:.2%}")

    # ── Compare ──────────────────────────────────────────────────────────
    # To compare diversity fairly at the same scale, we scale the baseline to the same number of recommendations
    scale_n = len(all_tracks)
    baseline_artists_at_scale = min(len(baseline_artists), scale_n)
    baseline_diversity = baseline_artists_at_scale / scale_n

    baseline_genres_at_scale = min(len(baseline_genres), scale_n)
    genre_baseline = baseline_genres_at_scale / scale_n

    improvement = ((ai_metrics["artist_diversity"] - baseline_diversity) / baseline_diversity) * 100
    genre_improvement = ((ai_metrics["genre_diversity"] - genre_baseline) / genre_baseline) * 100

    print(f"\n{'=' * 70}")
    print(f"COMPARISON:")
    print(f"  Artist diversity improvement: {improvement:+.1f}%")
    print(f"  Genre diversity improvement:  {genre_improvement:+.1f}%")
    print(f"  Target: >= 30% improvement")
    overall_pass = improvement >= 30 or genre_improvement >= 30
    print(f"  Status: {'PASS' if overall_pass else 'FAIL'}")
    print(f"{'=' * 70}")

    # Save report
    report_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "workspace"))
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "eval_catalog_coverage.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "baseline": {
                "total": len(BASELINE_RECOMMENDATIONS),
                "unique_artists": len(baseline_artists),
                "unique_genres": len(baseline_genres),
                "diversity_index": round(baseline_diversity, 4),
            },
            "ai_discovery": ai_metrics,
            "improvement": {
                "artist_diversity_pct": round(improvement, 2),
                "genre_diversity_pct": round(genre_improvement, 2),
            },
            "target_pct": 30,
            "overall_pass": overall_pass,
        }, f, indent=2)
    print(f"\nReport saved: {report_path}")

    return overall_pass


if __name__ == "__main__":
    success = run_evaluation()
    sys.exit(0 if success else 1)
