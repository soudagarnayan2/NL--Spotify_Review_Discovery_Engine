"""
Discovery Engine
================
Core intelligence for parsing natural language music queries into
structured search criteria and executing semantic search over ChromaDB.

Supports multi-turn refinement: users can incrementally adjust results
with follow-up instructions.
"""

import os
import sys
import json
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")
logger = logging.getLogger("discovery_engine")

# ---------------------------------------------------------------------------
# ChromaDB connection
# ---------------------------------------------------------------------------
CHROMA_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")
)
COLLECTION_NAME = "spotify_tracks"

_chroma_client = None
_collection = None


def _get_collection():
    """Lazy-load the ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        _collection = _chroma_client.get_or_create_collection(name=COLLECTION_NAME)
        logger.info("ChromaDB collection '%s' loaded (%d items)", COLLECTION_NAME, _collection.count())
    return _collection


# ---------------------------------------------------------------------------
# LLM Intent Parsing
# ---------------------------------------------------------------------------
INTENT_PROMPT = """You are a music discovery assistant. Parse the user's natural language query into structured search criteria.

User Query: "{query}"

{history_context}

Extract the following JSON structure (use null for fields not mentioned):
{{
    "genres": ["list of genres or subgenres mentioned or implied"],
    "moods": ["list of moods, feelings, or atmospheres"],
    "energy_range": [min_energy, max_energy],
    "tempo_range": [min_bpm, max_bpm],
    "acousticness_preference": "high" | "low" | "any",
    "instrumentalness_preference": "high" | "low" | "any",
    "exclude": ["things the user explicitly does NOT want"],
    "description_query": "A natural language sentence describing the ideal track"
}}

Rules:
- energy_range is 0.0 to 1.0 (0=calm, 1=intense)
- tempo_range is in BPM (60=slow, 180=fast)
- If the user says "upbeat", energy > 0.6. "Chill" = energy < 0.4.
- If the user says "fast", tempo > 130. "Slow" = tempo < 90.
- description_query should be a rich, descriptive sentence combining all the user's criteria.
- Always return valid JSON only, no extra text."""

REFINEMENT_PROMPT = """You are a music discovery assistant. The user wants to refine their previous search.

Previous search criteria:
{previous_intent}

User refinement: "{refinement}"

Produce UPDATED search criteria as JSON, merging the refinement into the previous search.
Keep fields from the previous search unless the user explicitly changes them.
Return valid JSON only matching this schema:
{{
    "genres": [...],
    "moods": [...],
    "energy_range": [min, max],
    "tempo_range": [min, max],
    "acousticness_preference": "high" | "low" | "any",
    "instrumentalness_preference": "high" | "low" | "any",
    "exclude": [...],
    "description_query": "updated description"
}}"""

EXPLANATION_PROMPT = """You are a friendly, honest music curator. The user asked: "{query}"

You found these tracks:
{tracks_text}

Write a brief, engaging 2-3 sentence explanation.
CRITICAL RULE: If the found tracks do NOT match the user's requested genre/language/origin (for example, if they asked for Marathi songs but the database returned Western ambient, rock, or pop tracks), you MUST politely and clearly clarify that the catalog does not have direct matches for their request, but explain why you are suggesting these specific tracks instead (e.g., matching a similar calm or introspective mood). Do NOT pretend or hallucinate that these Western tracks are Marathi or Marathi-inspired. Keep it honest, conversational, and helpful."""


def parse_music_intent(query: str, history: list = None, api_key: str = None) -> dict:
    """
    Parse a natural language music query into structured search criteria
    using Groq LLM (Llama 3).

    Args:
        query: The user's natural language music request.
        history: List of previous conversation messages for context.
        api_key: Groq API key (reads from env if not provided).

    Returns:
        Parsed intent dict with genres, moods, energy_range, etc.
    """
    api_key = api_key or os.getenv("GROQ_API_KEY")

    # Build history context
    history_context = ""
    if history:
        turns = []
        for msg in history[-6:]:  # Last 6 messages for context
            role = msg.get("role", "user")
            turns.append(f"{role.capitalize()}: {msg.get('content', '')}")
        history_context = "Conversation history:\n" + "\n".join(turns)

    prompt = INTENT_PROMPT.format(query=query, history_context=history_context)

    # Try LLM
    if api_key and not api_key.startswith("your_"):
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            resp = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You output only valid JSON. No markdown, no explanation."},
                    {"role": "user", "content": prompt},
                ],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            result = json.loads(resp.choices[0].message.content)
            logger.info("LLM parsed intent: %s", json.dumps(result, indent=2))
            return result
        except Exception as exc:
            logger.warning("LLM intent parsing failed: %s — using rules fallback", exc)

    # Rules-based fallback
    return _parse_intent_rules(query)


def _parse_intent_rules(query: str) -> dict:
    """Simple rules-based intent parser for when LLM is unavailable."""
    q = query.lower()
    genres, moods, exclude = [], [], []
    energy_range = [0.0, 1.0]
    tempo_range = [60, 200]
    acousticness = "any"
    instrumentalness = "any"

    genre_map = {
        "indie folk": "Indie Folk", "folk fusion": "Folk", "traditional folk": "Folk", "folk song": "Folk", "acoustic": "Indie Folk", "folk": "Folk",
        "synthwave": "Synthwave", "retro": "Synthwave", "retrowave": "Synthwave", "neon": "Synthwave", "synthpop": "Synthwave", "synth pop": "Synthwave",
        "lo-fi": "Lo-Fi", "lofi": "Lo-Fi", "chill": "Lo-Fi", "study": "Lo-Fi",
        "jazz": "Jazz", "neo-soul": "Jazz", "soul": "Jazz",
        "hip-hop": "Hip-Hop", "hip hop": "Hip-Hop", "rap": "Hip-Hop",
        "r&b": "R&B", "rnb": "R&B",
        "electronic": "Electronic", "dance": "Electronic", "edm": "Electronic", "house": "Electronic",
        "ambient": "Ambient", "meditation": "Ambient", "relaxation": "Ambient",
        "classical": "Classical", "piano": "Classical", "orchestral": "Classical",
        "rock": "Rock", "alternative": "Rock", "indie rock": "Rock",
        "pop": "Pop", "indie pop": "Pop",
        "metal": "Metal", "heavy": "Metal",
        "country": "Country", "bluegrass": "Country",
        "reggae": "Reggae",
        "afrobeats": "Afrobeats", "afro": "Afrobeats",
        "latin": "Latin", "reggaeton": "Latin",
        "marathi": "Marathi",
        "bollywood 90s": "Bollywood 90s", "bollywood 90's": "Bollywood 90s", "90s bollywood": "Bollywood 90s",
        "bollywood": "Bollywood",
        "old classic": "Old Classic", "classic": "Old Classic",
        "hindi": "Hindi Pop",
        "bhojpuri": "Bhojpuri",
        "tamil": "Tamil",
        "kannada": "Kannada",
    }
    for keyword, genre in genre_map.items():
        if keyword in q and genre not in genres:
            genres.append(genre)

    # Mood detection
    mood_keywords = {
        "happy": "joyful", "sad": "melancholic", "energetic": "energetic",
        "calm": "peaceful", "dark": "dark", "upbeat": "upbeat",
        "romantic": "romantic", "angry": "aggressive", "nostalgic": "nostalgic",
        "dreamy": "dreamy", "epic": "epic", "funky": "funky",
        "groovy": "groovy", "peaceful": "peaceful", "intense": "intense",
        "warm": "warm", "cool": "cool", "mysterious": "mysterious",
        "melancholic": "melancholic", "ethereal": "ethereal",
        "cinematic": "cinematic", "cozy": "cozy", "powerful": "powerful",
        "tender": "tender", "bittersweet": "bittersweet",
        "autumn": "autumnal", "summer": "summery", "winter": "winter",
        "night": "nocturnal", "morning": "sunny", "rain": "melancholic",
        "driving": "driving", "focus": "contemplative", "workout": "energetic",
        "sleep": "sleepy", "party": "euphoric",
    }
    for keyword, mood in mood_keywords.items():
        if keyword in q and mood not in moods:
            moods.append(mood)

    # Energy / tempo heuristics
    if any(w in q for w in ["upbeat", "energetic", "fast", "intense", "workout", "party", "pump"]):
        energy_range = [0.6, 1.0]
        tempo_range = [120, 200]
    elif any(w in q for w in ["calm", "chill", "slow", "peaceful", "relax", "sleep", "ambient", "gentle"]):
        energy_range = [0.0, 0.4]
        tempo_range = [60, 100]
    elif any(w in q for w in ["moderate", "medium", "balanced"]):
        energy_range = [0.3, 0.7]
        tempo_range = [90, 140]

    # Acousticness
    if any(w in q for w in ["acoustic", "guitar", "unplugged", "folk"]):
        acousticness = "high"
    elif any(w in q for w in ["electronic", "synth", "digital", "edm"]):
        acousticness = "low"

    # Instrumentalness
    if any(w in q for w in ["instrumental", "no vocals", "without vocals", "no singing"]):
        instrumentalness = "high"
    elif any(w in q for w in ["vocals", "singing", "lyric"]):
        instrumentalness = "low"

    # Exclusions
    if "not depressing" in q or "not sad" in q:
        exclude.append("depressing")
    if "no vocals" in q:
        exclude.append("vocals")
    if "no metal" in q or "not heavy" in q:
        exclude.append("heavy metal")

    return {
        "genres": genres or None,
        "moods": moods or ["general"],
        "energy_range": energy_range,
        "tempo_range": tempo_range,
        "acousticness_preference": acousticness,
        "instrumentalness_preference": instrumentalness,
        "exclude": exclude or None,
        "description_query": query,
    }


def refine_search(refinement: str, previous_intent: dict, api_key: str = None) -> dict:
    """
    Merge a refinement instruction into existing search criteria.

    Args:
        refinement: User's follow-up instruction (e.g., "make it slower").
        previous_intent: The previous parsed intent dict.
        api_key: Groq API key.

    Returns:
        Updated intent dict.
    """
    api_key = api_key or os.getenv("GROQ_API_KEY")

    if api_key and not api_key.startswith("your_"):
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            prompt = REFINEMENT_PROMPT.format(
                previous_intent=json.dumps(previous_intent, indent=2),
                refinement=refinement,
            )
            resp = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You output only valid JSON. No markdown, no explanation."},
                    {"role": "user", "content": prompt},
                ],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            result = json.loads(resp.choices[0].message.content)
            logger.info("LLM refined intent: %s", json.dumps(result, indent=2))
            return result
        except Exception as exc:
            logger.warning("LLM refinement failed: %s — using rules merge", exc)

    # Rules-based merge
    refined = _parse_intent_rules(refinement)
    merged = dict(previous_intent)

    # Merge non-null fields from refinement
    if refined.get("genres"):
        merged["genres"] = refined["genres"]
    if refined.get("moods") and refined["moods"] != ["general"]:
        merged["moods"] = refined["moods"]
    if refined["energy_range"] != [0.0, 1.0]:
        merged["energy_range"] = refined["energy_range"]
    if refined["tempo_range"] != [60, 200]:
        merged["tempo_range"] = refined["tempo_range"]
    if refined["acousticness_preference"] != "any":
        merged["acousticness_preference"] = refined["acousticness_preference"]
    if refined["instrumentalness_preference"] != "any":
        merged["instrumentalness_preference"] = refined["instrumentalness_preference"]
    if refined.get("exclude"):
        existing = merged.get("exclude") or []
        merged["exclude"] = list(set(existing + refined["exclude"]))

    merged["description_query"] = f"{previous_intent.get('description_query', '')} {refinement}"
    return merged


def search_tracks(parsed_intent: dict, n_results: int = 10) -> list[dict]:
    """
    Query ChromaDB using the parsed intent and apply post-filters.

    Args:
        parsed_intent: Output from parse_music_intent or refine_search.
        n_results: Number of results to return.

    Returns:
        List of track dicts sorted by relevance.
    """
    collection = _get_collection()

    if collection.count() == 0:
        logger.warning("ChromaDB collection is empty. Run seed_tracks.py first.")
        return []

    # Build the query text from description + moods + genres
    query_parts = [parsed_intent.get("description_query", "")]
    if parsed_intent.get("moods"):
        query_parts.append("Mood: " + ", ".join(parsed_intent["moods"]))
    if parsed_intent.get("genres"):
        query_parts.append("Genre: " + ", ".join(parsed_intent["genres"]))
    query_text = " ".join(query_parts)

    # Query more results than needed for post-filtering
    fetch_n = min(max(n_results * 8, 40), collection.count())
    results = collection.query(
        query_texts=[query_text],
        n_results=fetch_n,
        include=["metadatas", "distances", "documents"],
    )

    if not results["ids"][0]:
        return []

    # Build track list with metadata
    tracks = []
    for i, track_id in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i]
        distance = results["distances"][0][i] if results.get("distances") else 0

        tracks.append({
            "id": track_id,
            "track_name": meta.get("track_name", "Unknown"),
            "artist": meta.get("artist", "Unknown"),
            "album": meta.get("album", ""),
            "genre": meta.get("genre", ""),
            "subgenre": meta.get("subgenre", ""),
            "mood_tags": json.loads(meta.get("mood_tags", "[]")),
            "energy": float(meta.get("energy", 0.5)),
            "valence": float(meta.get("valence", 0.5)),
            "tempo_bpm": int(meta.get("tempo_bpm", 120)),
            "acousticness": float(meta.get("acousticness", 0.5)),
            "instrumentalness": float(meta.get("instrumentalness", 0.5)),
            "description": meta.get("description", ""),
            "relevance_score": round(1.0 / (1.0 + distance), 3),
        })

    # Apply post-filters
    filtered = _apply_filters(tracks, parsed_intent)

    # Sort by relevance, filter out low-relevance scores, and take top N
    filtered.sort(key=lambda t: t["relevance_score"], reverse=True)
    filtered = [t for t in filtered if t["relevance_score"] >= 0.53]
    return filtered[:n_results]


def _apply_filters(tracks: list[dict], intent: dict) -> list[dict]:
    """Apply energy, tempo, acousticness, instrumentalness, exclusions, and genre filters."""
    filtered = []
    energy_range = intent.get("energy_range", [0.0, 1.0])
    tempo_range = intent.get("tempo_range", [60, 200])
    acoustic_pref = intent.get("acousticness_preference", "any")
    instrumental_pref = intent.get("instrumentalness_preference", "any")
    excludes = [e.lower() for e in (intent.get("exclude") or [])]
    genres = [g.lower() for g in (intent.get("genres") or []) if g]

    for track in tracks:
        # Energy filter (with some tolerance)
        if not (energy_range[0] - 0.15 <= track["energy"] <= energy_range[1] + 0.15):
            continue

        # Tempo filter (with tolerance)
        if not (tempo_range[0] - 20 <= track["tempo_bpm"] <= tempo_range[1] + 20):
            continue

        # Acousticness preference
        if acoustic_pref == "high" and track["acousticness"] < 0.3:
            continue
        if acoustic_pref == "low" and track["acousticness"] > 0.7:
            continue

        # Instrumentalness preference
        if instrumental_pref == "high" and track["instrumentalness"] < 0.3:
            continue
        if instrumental_pref == "low" and track["instrumentalness"] > 0.7:
            continue

        # Exclusions
        excluded = False
        for ex in excludes:
            track_text = (
                f"{track['genre']} {track['subgenre']} "
                f"{' '.join(track['mood_tags'])} {track['description']}"
            ).lower()
            if ex in track_text:
                excluded = True
                break
        if excluded:
            continue

        filtered.append(track)

    # Apply genre filter if specified
    if genres:
        genre_filtered = []
        for track in filtered:
            track_genre = track["genre"].lower()
            track_subgenre = track["subgenre"].lower()
            track_desc = track["description"].lower()
            if any(g in track_genre or g in track_subgenre or g in track_desc for g in genres):
                genre_filtered.append(track)
        filtered = genre_filtered

    # If we found at least 1 track matching all filters, return them
    if len(filtered) > 0:
        return filtered

    # If we got 0 results, check if we can relax
    # If the user specified a genre, we should try to return tracks of that genre
    # by relaxing other filters (energy, tempo, acousticness, instrumentalness)
    if genres:
        relaxed_genre_tracks = []
        for track in tracks:
            track_genre = track["genre"].lower()
            track_subgenre = track["subgenre"].lower()
            track_desc = track["description"].lower()
            # Still apply exclusion filters if possible
            excluded = False
            for ex in excludes:
                track_text = (
                    f"{track['genre']} {track['subgenre']} "
                    f"{' '.join(track['mood_tags'])} {track['description']}"
                ).lower()
                if ex in track_text:
                    excluded = True
                    break
            if excluded:
                continue

            if any(g in track_genre or g in track_subgenre or g in track_desc for g in genres):
                relaxed_genre_tracks.append(track)

        if len(relaxed_genre_tracks) > 0:
            logger.info("Found %d results by relaxing audio feature filters but keeping genre constraint", len(relaxed_genre_tracks))
            return relaxed_genre_tracks

        # If genres are completely absent from catalog, return empty list
        logger.info("Requested genres %s not found in catalog, returning empty", genres)
        return []

    # If no genres were specified, and filtered is empty, we relax to semantic-only
    logger.info("Post-filters too restrictive (0 results), relaxing to semantic-only")
    return tracks


def generate_explanation(query: str, tracks: list[dict], api_key: str = None) -> str:
    """
    Generate a natural-language explanation of why these tracks match.

    Args:
        query: The original user query.
        tracks: List of matched track dicts.
        api_key: Groq API key.

    Returns:
        A conversational explanation string.
    """
    if not tracks:
        return "Unfortunately, our music catalog doesn't have direct matches for your request. Try searching for genres present in our catalog (like Lo-Fi, Folk, Indie Folk, Synthwave, Classical, Jazz, Electronic, Pop, Rock, Metal, Country, Reggae, Afrobeats, Latin, Marathi, Bollywood 90s, Hindi Pop, Bhojpuri, Tamil, Kannada, Bollywood, or Old Classic)."

    api_key = api_key or os.getenv("GROQ_API_KEY")

    tracks_text = "\n".join(
        f"- {t['track_name']} by {t['artist']} ({t['genre']}/{t['subgenre']}) — "
        f"moods: {', '.join(t['mood_tags'][:3])}, energy: {t['energy']}"
        for t in tracks[:8]
    )

    if api_key and not api_key.startswith("your_"):
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            prompt = EXPLANATION_PROMPT.format(query=query, tracks_text=tracks_text)
            resp = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a friendly, knowledgeable music curator."},
                    {"role": "user", "content": prompt},
                ],
                model="llama-3.1-8b-instant",
                temperature=0.7,
                max_tokens=200,
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            logger.warning("LLM explanation failed: %s", exc)

    # Fallback
    genres = list(set(t["genre"] for t in tracks[:5]))
    moods = list(set(m for t in tracks[:5] for m in t["mood_tags"][:2]))
    return (
        f"I found {len(tracks)} tracks that match your request! "
        f"The selection spans {', '.join(genres[:3])} with moods like {', '.join(moods[:4])}. "
        f"These tracks were chosen for their sonic qualities that align with what you described."
    )
