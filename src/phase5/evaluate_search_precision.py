"""
Search Precision Evaluator
==========================
Tests the semantic search accuracy of the AI discovery engine by running
predefined queries and checking if returned tracks match expected criteria.

Target: >= 85% semantic match accuracy.

Usage:
    python src/phase5/evaluate_search_precision.py
"""

import os
import sys
import json

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "phase4")))

from discovery_engine import parse_music_intent, search_tracks

# ---------------------------------------------------------------------------
# Test Cases: query → expected attributes
# ---------------------------------------------------------------------------
TEST_QUERIES = [
    {
        "query": "upbeat synthwave for driving at night",
        "expected_genres": ["Synthwave"],
        "expected_moods": ["nocturnal", "cinematic", "energetic", "cool"],
        "min_energy": 0.4,
    },
    {
        "query": "calm acoustic folk songs for autumn",
        "expected_genres": ["Indie Folk"],
        "expected_moods": ["nostalgic", "warm", "peaceful", "autumnal"],
        "max_energy": 0.5,
    },
    {
        "query": "lo-fi beats for studying",
        "expected_genres": ["Lo-Fi"],
        "expected_moods": ["relaxing", "study", "peaceful", "cozy"],
        "max_energy": 0.4,
    },
    {
        "query": "energetic hip-hop workout music",
        "expected_genres": ["Hip-Hop"],
        "expected_moods": ["energetic", "powerful", "aggressive"],
        "min_energy": 0.5,
    },
    {
        "query": "romantic jazz for a dinner date",
        "expected_genres": ["Jazz"],
        "expected_moods": ["romantic", "smooth", "warm", "sophisticated"],
    },
    {
        "query": "dark electronic music with heavy bass",
        "expected_genres": ["Electronic", "Synthwave"],
        "expected_moods": ["dark", "intense", "powerful"],
        "min_energy": 0.5,
    },
    {
        "query": "peaceful ambient music for meditation",
        "expected_genres": ["Ambient"],
        "expected_moods": ["peaceful", "calming", "meditative", "transcendent"],
        "max_energy": 0.3,
    },
    {
        "query": "feel-good indie pop for summer",
        "expected_genres": ["Pop"],
        "expected_moods": ["joyful", "upbeat", "summery", "carefree"],
        "min_energy": 0.4,
    },
    {
        "query": "emotional piano pieces that feel cinematic",
        "expected_genres": ["Classical", "Ambient"],
        "expected_moods": ["emotional", "cinematic", "powerful", "contemplative"],
    },
    {
        "query": "aggressive rock anthems for the gym",
        "expected_genres": ["Rock", "Metal"],
        "expected_moods": ["aggressive", "powerful", "intense", "driving"],
        "min_energy": 0.6,
    },
    {
        "query": "dreamy R&B love songs",
        "expected_genres": ["R&B"],
        "expected_moods": ["dreamy", "romantic", "tender", "ethereal"],
    },
    {
        "query": "funky groovy jazz fusion",
        "expected_genres": ["Jazz"],
        "expected_moods": ["funky", "groovy", "playful"],
    },
    {
        "query": "melancholic indie folk about heartbreak",
        "expected_genres": ["Indie Folk"],
        "expected_moods": ["melancholic", "raw", "emotional", "heartbreak"],
    },
    {
        "query": "high energy dance music for a party",
        "expected_genres": ["Electronic", "Pop"],
        "expected_moods": ["euphoric", "energetic", "danceable"],
        "min_energy": 0.65,
    },
    {
        "query": "soothing reggae music for relaxation",
        "expected_genres": ["Reggae"],
        "expected_moods": ["positive", "peaceful", "warm"],
        "max_energy": 0.5,
    },
    {
        "query": "nostalgic retro synthpop from the 80s",
        "expected_genres": ["Synthwave"],
        "expected_moods": ["nostalgic", "retro", "euphoric"],
    },
    {
        "query": "slow country ballads with soulful vocals",
        "expected_genres": ["Country"],
        "expected_moods": ["soulful", "warm", "romantic"],
        "max_energy": 0.5,
    },
    {
        "query": "afrobeats for dancing with friends",
        "expected_genres": ["Afrobeats"],
        "expected_moods": ["uplifting", "rhythmic", "celebratory"],
    },
    {
        "query": "instrumental music without vocals for focus",
        "expected_genres": [],  # Any genre, but must be instrumental
        "expected_moods": ["contemplative", "peaceful"],
        "min_instrumentalness": 0.5,
    },
    {
        "query": "psychedelic rock with a groovy vibe",
        "expected_genres": ["Rock"],
        "expected_moods": ["psychedelic", "groovy"],
    },
    {
        "query": "energetic marathi dance songs",
        "expected_genres": ["Marathi"],
        "expected_moods": ["energetic", "dance"],
        "min_energy": 0.5,
    },
    {
        "query": "romantic bollywood 90s love songs",
        "expected_genres": ["Bollywood 90s"],
        "expected_moods": ["romantic"],
    },
    {
        "query": "upbeat hindi pop songs",
        "expected_genres": ["Hindi Pop"],
        "expected_moods": ["upbeat", "energetic"],
    },
    {
        "query": "energetic bhojpuri dance music",
        "expected_genres": ["Bhojpuri"],
        "expected_moods": ["energetic", "dance"],
        "min_energy": 0.6,
    },
    {
        "query": "tamil kuthu dance tracks",
        "expected_genres": ["Tamil"],
        "expected_moods": ["dance", "energetic", "rhythmic"],
        "min_energy": 0.6,
    },
    {
        "query": "romantic kannada songs",
        "expected_genres": ["Kannada"],
        "expected_moods": ["romantic", "melodic"],
    },
    {
        "query": "modern bollywood romantic pop",
        "expected_genres": ["Bollywood"],
        "expected_moods": ["romantic", "upbeat"],
    },
    {
        "query": "old classic hindi retro songs",
        "expected_genres": ["Old Classic"],
        "expected_moods": ["romantic", "nostalgic", "retro"],
    },
    {
        "query": "traditional rajasthani and punjabi folk songs",
        "expected_genres": ["Folk"],
        "expected_moods": ["folk", "traditional", "cultural"],
    },
]


def evaluate_single(test_case: dict) -> dict:
    """Run a single test query and evaluate results."""
    query = test_case["query"]
    expected_genres = [g.lower() for g in test_case.get("expected_genres", [])]
    expected_moods = [m.lower() for m in test_case.get("expected_moods", [])]

    # Use rules-based parsing (no LLM dependency for eval)
    intent = parse_music_intent(query, api_key=None)
    tracks = search_tracks(intent, n_results=5)

    if not tracks:
        return {"query": query, "score": 0.0, "tracks_found": 0, "detail": "No tracks returned", "pass": False}

    # Score each track
    scores = []
    for track in tracks:
        track_score = 0.0
        checks = 0

        # Genre match
        if expected_genres:
            checks += 1
            if track["genre"].lower() in expected_genres or track["subgenre"].lower() in [g for g in expected_genres]:
                track_score += 1.0

        # Mood overlap
        if expected_moods:
            checks += 1
            track_moods = [m.lower() for m in track["mood_tags"]]
            overlap = len(set(track_moods) & set(expected_moods))
            if overlap > 0:
                track_score += min(1.0, overlap / 2)

        # Energy check
        if "min_energy" in test_case:
            checks += 1
            if track["energy"] >= test_case["min_energy"]:
                track_score += 1.0
        if "max_energy" in test_case:
            checks += 1
            if track["energy"] <= test_case["max_energy"]:
                track_score += 1.0

        # Instrumentalness check
        if "min_instrumentalness" in test_case:
            checks += 1
            if track["instrumentalness"] >= test_case["min_instrumentalness"]:
                track_score += 1.0

        scores.append(track_score / max(checks, 1))

    avg_score = sum(scores) / len(scores)

    return {
        "query": query,
        "score": round(avg_score, 3),
        "tracks_found": len(tracks),
        "top_track": f"{tracks[0]['track_name']} by {tracks[0]['artist']}",
        "pass": avg_score >= 0.5,
    }


def run_evaluation():
    """Run the full precision evaluation suite."""
    print("=" * 70)
    print("SEARCH PRECISION EVALUATION")
    print("=" * 70)
    print(f"Running {len(TEST_QUERIES)} test queries...\n")

    results = []
    passed = 0

    for i, tc in enumerate(TEST_QUERIES):
        result = evaluate_single(tc)
        results.append(result)
        status = "PASS" if result["pass"] else "FAIL"
        if result["pass"]:
            passed += 1
        print(f"  [{status}] Query {i+1:2d}: \"{tc['query'][:50]}...\"")
        print(f"           Score: {result['score']:.1%} | Top: {result.get('top_track', 'N/A')}")

    accuracy = passed / len(results) * 100
    avg_score = sum(r["score"] for r in results) / len(results)

    print(f"\n{'=' * 70}")
    print(f"RESULTS: {passed}/{len(results)} queries passed ({accuracy:.1f}%)")
    print(f"Average precision score: {avg_score:.1%}")
    print(f"Target: >= 85% | Status: {'PASS' if accuracy >= 85 else 'FAIL'}")
    print(f"{'=' * 70}")

    # Save report
    report_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "workspace"))
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "eval_search_precision.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "test_date": __import__("datetime").datetime.now().isoformat(),
            "total_queries": len(results),
            "passed": passed,
            "accuracy_pct": round(accuracy, 2),
            "avg_score": round(avg_score, 4),
            "target_pct": 85,
            "overall_pass": accuracy >= 85,
            "results": results,
        }, f, indent=2)
    print(f"\nReport saved: {report_path}")

    return accuracy >= 85


if __name__ == "__main__":
    success = run_evaluation()
    sys.exit(0 if success else 1)
