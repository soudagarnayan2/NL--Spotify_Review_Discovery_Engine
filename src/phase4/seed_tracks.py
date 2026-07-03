"""
Spotify Track Catalog Seeder
=============================
Populates a ChromaDB collection with ~180 curated tracks spanning diverse
genres. Each track has rich metadata (mood tags, energy, valence, tempo,
acousticness, instrumentalness) and a natural-language description that
gets embedded for semantic search.

Usage:
    python src/phase4/seed_tracks.py
"""

import os
import sys
import json
import chromadb
from chromadb.config import Settings

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CHROMA_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")
)
COLLECTION_NAME = "spotify_tracks"

# ---------------------------------------------------------------------------
# Curated Track Catalog (~180 tracks)
# ---------------------------------------------------------------------------
TRACK_CATALOG = [
    {
        "id": "track_001",
        "track_name": "Holocene",
        "artist": "Bon Iver",
        "album": "Bon Iver, Bon Iver",
        "genre": "Indie Folk",
        "subgenre": "Chamber Folk",
        "mood_tags": [
            "reflective",
            "melancholic",
            "ethereal",
            "introspective"
        ],
        "energy": 0.25,
        "valence": 0.2,
        "tempo_bpm": 108,
        "acousticness": 0.85,
        "instrumentalness": 0.1,
        "description": "A hauntingly beautiful indie folk ballad with layered falsetto vocals, gentle guitar arpeggios, and atmospheric reverb. Feels like watching snow fall over an empty field at dawn.",
        "language": "English",
        "release_year": 2011,
        "popularity": 41,
        "activities": [
            "Coding",
            "Meditation",
            "Reading"
        ]
    },
    {
        "id": "track_002",
        "track_name": "Big Black Car",
        "artist": "Gregory Alan Isakov",
        "album": "That Sea, The Gambler",
        "genre": "Indie Folk",
        "subgenre": "Americana",
        "mood_tags": [
            "nostalgic",
            "warm",
            "gentle",
            "wistful"
        ],
        "energy": 0.2,
        "valence": 0.3,
        "tempo_bpm": 95,
        "acousticness": 0.9,
        "instrumentalness": 0.05,
        "description": "A warm, nostalgic acoustic folk song with fingerpicked guitar and hushed vocals. Evokes long drives through autumn countryside with golden light filtering through the trees.",
        "language": "English",
        "release_year": 2012,
        "popularity": 42,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_003",
        "track_name": "First Day of My Life",
        "artist": "Bright Eyes",
        "album": "I'm Wide Awake, It's Morning",
        "genre": "Indie Folk",
        "subgenre": "Singer-Songwriter",
        "mood_tags": [
            "hopeful",
            "tender",
            "romantic",
            "gentle"
        ],
        "energy": 0.3,
        "valence": 0.65,
        "tempo_bpm": 104,
        "acousticness": 0.88,
        "instrumentalness": 0.0,
        "description": "A tender, hopeful indie folk love song with simple strummed acoustic guitar. Intimate and heartfelt, like writing a love letter on a quiet Sunday morning.",
        "language": "English",
        "release_year": 2013,
        "popularity": 43,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_004",
        "track_name": "Skinny Love",
        "artist": "Bon Iver",
        "album": "For Emma, Forever Ago",
        "genre": "Indie Folk",
        "subgenre": "Lo-Fi Folk",
        "mood_tags": [
            "raw",
            "emotional",
            "heartbreak",
            "stripped"
        ],
        "energy": 0.35,
        "valence": 0.15,
        "tempo_bpm": 114,
        "acousticness": 0.82,
        "instrumentalness": 0.0,
        "description": "An emotionally raw folk track recorded in a cabin, with cracking falsetto and aggressive acoustic guitar strumming. The sound of heartbreak echoing in an empty room.",
        "language": "English",
        "release_year": 2014,
        "popularity": 44,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_005",
        "track_name": "Northern Wind",
        "artist": "City and Colour",
        "album": "Little Hell",
        "genre": "Indie Folk",
        "subgenre": "Alt-Country",
        "mood_tags": [
            "peaceful",
            "contemplative",
            "serene",
            "autumnal"
        ],
        "energy": 0.2,
        "valence": 0.35,
        "tempo_bpm": 88,
        "acousticness": 0.92,
        "instrumentalness": 0.05,
        "description": "A serene acoustic ballad with gentle fingerpicking and a warm baritone voice. Feels like sitting by a campfire under a starlit sky in the mountains.",
        "language": "English",
        "release_year": 2015,
        "popularity": 45,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_006",
        "track_name": "The Night We Met",
        "artist": "Lord Huron",
        "album": "Strange Trails",
        "genre": "Indie Folk",
        "subgenre": "Baroque Folk",
        "mood_tags": [
            "bittersweet",
            "longing",
            "cinematic",
            "melancholic"
        ],
        "energy": 0.3,
        "valence": 0.1,
        "tempo_bpm": 84,
        "acousticness": 0.7,
        "instrumentalness": 0.0,
        "description": "A cinematic indie folk track about loss and longing, with lush orchestral arrangements and an aching vocal performance. The soundtrack to looking at old photographs.",
        "language": "English",
        "release_year": 2016,
        "popularity": 46,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_007",
        "track_name": "Ho Hey",
        "artist": "The Lumineers",
        "album": "The Lumineers",
        "genre": "Indie Folk",
        "subgenre": "Folk Rock",
        "mood_tags": [
            "upbeat",
            "joyful",
            "singalong",
            "carefree"
        ],
        "energy": 0.6,
        "valence": 0.75,
        "tempo_bpm": 163,
        "acousticness": 0.65,
        "instrumentalness": 0.0,
        "description": "An upbeat, feel-good folk anthem with stomping rhythms, bright acoustic guitar, and catchy call-and-response vocals. Perfect for road trips with friends.",
        "language": "English",
        "release_year": 2017,
        "popularity": 47,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_008",
        "track_name": "Flume",
        "artist": "Bon Iver",
        "album": "For Emma, Forever Ago",
        "genre": "Indie Folk",
        "subgenre": "Lo-Fi Folk",
        "mood_tags": [
            "intimate",
            "quiet",
            "fragile",
            "winter"
        ],
        "energy": 0.15,
        "valence": 0.2,
        "tempo_bpm": 80,
        "acousticness": 0.95,
        "instrumentalness": 0.1,
        "description": "An intimate, whisper-quiet folk song with barely-there guitar and fragile vocals. Sounds like frost forming on a window pane in a silent cabin.",
        "language": "English",
        "release_year": 2018,
        "popularity": 48,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_010",
        "track_name": "Nightcall",
        "artist": "Kavinsky",
        "album": "OutRun",
        "genre": "Synthwave",
        "subgenre": "Retrowave",
        "mood_tags": [
            "nocturnal",
            "cinematic",
            "cool",
            "mysterious"
        ],
        "energy": 0.55,
        "valence": 0.35,
        "tempo_bpm": 120,
        "acousticness": 0.05,
        "instrumentalness": 0.3,
        "description": "An iconic synthwave track with pulsing bass, arpeggiated synths, and vocoder vocals. The definitive soundtrack to driving through a neon-lit city at midnight.",
        "language": "English",
        "release_year": 2020,
        "popularity": 50,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_011",
        "track_name": "Tech Noir",
        "artist": "Gunship",
        "album": "Gunship",
        "genre": "Synthwave",
        "subgenre": "Darksynth",
        "mood_tags": [
            "dark",
            "intense",
            "futuristic",
            "cinematic"
        ],
        "energy": 0.7,
        "valence": 0.3,
        "tempo_bpm": 128,
        "acousticness": 0.02,
        "instrumentalness": 0.4,
        "description": "A dark, cinematic synthwave anthem with thundering drums, soaring synth leads, and an 80s cyberpunk atmosphere. Like a chase scene through rain-soaked neon streets.",
        "language": "English",
        "release_year": 2021,
        "popularity": 51,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_012",
        "track_name": "A Real Hero",
        "artist": "College & Electric Youth",
        "album": "Drive OST",
        "genre": "Synthwave",
        "subgenre": "Dream Synth",
        "mood_tags": [
            "dreamy",
            "nostalgic",
            "hopeful",
            "ethereal"
        ],
        "energy": 0.35,
        "valence": 0.45,
        "tempo_bpm": 100,
        "acousticness": 0.1,
        "instrumentalness": 0.2,
        "description": "A dreamy, ethereal synthpop track with airy vocals and warm analog synth pads. Feels like watching a sunset from a rooftop while the city glows below.",
        "language": "English",
        "release_year": 2022,
        "popularity": 52,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_013",
        "track_name": "Resonance",
        "artist": "HOME",
        "album": "Odyssey",
        "genre": "Synthwave",
        "subgenre": "Chillwave",
        "mood_tags": [
            "nostalgic",
            "warm",
            "peaceful",
            "vaporwave"
        ],
        "energy": 0.4,
        "valence": 0.55,
        "tempo_bpm": 108,
        "acousticness": 0.05,
        "instrumentalness": 0.85,
        "description": "A warm, nostalgic chillwave instrumental with lush synth pads and a gentle arpeggiated melody. Like scrolling through old vacation photos on a lazy afternoon.",
        "language": "English",
        "release_year": 2023,
        "popularity": 53,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_014",
        "track_name": "Turbo Killer",
        "artist": "Carpenter Brut",
        "album": "Trilogy",
        "genre": "Synthwave",
        "subgenre": "Darksynth",
        "mood_tags": [
            "aggressive",
            "powerful",
            "dark",
            "adrenaline"
        ],
        "energy": 0.9,
        "valence": 0.2,
        "tempo_bpm": 140,
        "acousticness": 0.01,
        "instrumentalness": 0.6,
        "description": "An ultra-aggressive darksynth track with distorted bass, relentless drums, and screaming synth leads. Pure adrenaline fuel for high-speed night driving.",
        "language": "English",
        "release_year": 2024,
        "popularity": 54,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_015",
        "track_name": "Blinding Lights",
        "artist": "The Weeknd",
        "album": "After Hours",
        "genre": "Synthwave",
        "subgenre": "Synthpop",
        "mood_tags": [
            "energetic",
            "euphoric",
            "retro",
            "anthemic"
        ],
        "energy": 0.75,
        "valence": 0.65,
        "tempo_bpm": 171,
        "acousticness": 0.0,
        "instrumentalness": 0.0,
        "description": "A soaring retro-synthpop anthem with pulsing synths, driving beat, and powerful vocals. Captures the euphoria of speeding through city lights on a Friday night.",
        "language": "English",
        "release_year": 2025,
        "popularity": 55,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_020",
        "track_name": "Snowman",
        "artist": "WYS",
        "album": "Snowman Single",
        "genre": "Lo-Fi",
        "subgenre": "Lo-Fi Hip Hop",
        "mood_tags": [
            "relaxing",
            "cozy",
            "study",
            "winter"
        ],
        "energy": 0.15,
        "valence": 0.4,
        "tempo_bpm": 75,
        "acousticness": 0.3,
        "instrumentalness": 0.9,
        "description": "A cozy lo-fi hip hop beat with soft piano, vinyl crackle, and gentle percussion. Perfect for studying on a snowy evening with a cup of hot cocoa.",
        "language": "English",
        "release_year": 2014,
        "popularity": 60,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_021",
        "track_name": "Coffee",
        "artist": "beabadoobee",
        "album": "Space Cadet",
        "genre": "Lo-Fi",
        "subgenre": "Bedroom Pop",
        "mood_tags": [
            "cute",
            "warm",
            "romantic",
            "chill"
        ],
        "energy": 0.35,
        "valence": 0.7,
        "tempo_bpm": 108,
        "acousticness": 0.55,
        "instrumentalness": 0.0,
        "description": "A sweet, lo-fi bedroom pop song with fuzzy guitars, gentle vocals, and a warm analog feel. Like sharing coffee with someone you love on a lazy morning.",
        "language": "English",
        "release_year": 2015,
        "popularity": 61,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_022",
        "track_name": "Affection",
        "artist": "Jinsang",
        "album": "Life",
        "genre": "Lo-Fi",
        "subgenre": "Lo-Fi Hip Hop",
        "mood_tags": [
            "peaceful",
            "contemplative",
            "study",
            "mellow"
        ],
        "energy": 0.1,
        "valence": 0.45,
        "tempo_bpm": 82,
        "acousticness": 0.25,
        "instrumentalness": 0.95,
        "description": "A mellow lo-fi instrumental with soft piano chords, tape hiss, and a gentle swaying beat. Ideal background for deep concentration and late-night reading.",
        "language": "English",
        "release_year": 2016,
        "popularity": 62,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_023",
        "track_name": "Eventually",
        "artist": "Tame Impala",
        "album": "Currents",
        "genre": "Lo-Fi",
        "subgenre": "Psychedelic Pop",
        "mood_tags": [
            "dreamy",
            "psychedelic",
            "introspective",
            "spacious"
        ],
        "energy": 0.5,
        "valence": 0.4,
        "tempo_bpm": 118,
        "acousticness": 0.05,
        "instrumentalness": 0.15,
        "description": "A swirling psychedelic pop track with phased guitars, reverberating drums, and lush synth textures. Feels like floating through space in slow motion.",
        "language": "English",
        "release_year": 2017,
        "popularity": 63,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_024",
        "track_name": "Daylight",
        "artist": "Joji",
        "album": "Smithereens",
        "genre": "Lo-Fi",
        "subgenre": "Bedroom Pop",
        "mood_tags": [
            "melancholic",
            "gentle",
            "yearning",
            "soft"
        ],
        "energy": 0.25,
        "valence": 0.3,
        "tempo_bpm": 88,
        "acousticness": 0.2,
        "instrumentalness": 0.05,
        "description": "A soft, melancholic lo-fi pop song with hushed vocals, warm synths, and a subtle emotional ache. Like watching daylight fade through a rain-streaked window.",
        "language": "English",
        "release_year": 2018,
        "popularity": 64,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_025",
        "track_name": "4AM",
        "artist": "Idealism",
        "album": "Contrasts",
        "genre": "Lo-Fi",
        "subgenre": "Lo-Fi Hip Hop",
        "mood_tags": [
            "nocturnal",
            "peaceful",
            "sleepy",
            "ambient"
        ],
        "energy": 0.08,
        "valence": 0.35,
        "tempo_bpm": 70,
        "acousticness": 0.4,
        "instrumentalness": 0.98,
        "description": "An ultra-peaceful lo-fi ambient track with distant piano, rain samples, and barely-there percussion. The sound of 4 AM when the whole world is asleep.",
        "language": "English",
        "release_year": 2019,
        "popularity": 65,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_030",
        "track_name": "Black Gold",
        "artist": "Esperanza Spalding",
        "album": "Chamber Music Society",
        "genre": "Jazz",
        "subgenre": "Contemporary Jazz",
        "mood_tags": [
            "sophisticated",
            "warm",
            "uplifting",
            "groovy"
        ],
        "energy": 0.55,
        "valence": 0.7,
        "tempo_bpm": 120,
        "acousticness": 0.75,
        "instrumentalness": 0.15,
        "description": "A vibrant contemporary jazz track with walking bass, expressive vocals, and lively horn arrangements. Sophisticated and uplifting, like a sunlit afternoon at a jazz cafe.",
        "language": "English",
        "release_year": 2024,
        "popularity": 70,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_031",
        "track_name": "Neon Guts",
        "artist": "Thundercat",
        "album": "Drunk",
        "genre": "Jazz",
        "subgenre": "Jazz Fusion",
        "mood_tags": [
            "funky",
            "playful",
            "eccentric",
            "groovy"
        ],
        "energy": 0.65,
        "valence": 0.7,
        "tempo_bpm": 130,
        "acousticness": 0.15,
        "instrumentalness": 0.25,
        "description": "An eccentric jazz fusion track with slapping bass, wonky synths, and playful vocals. Funky and unpredictable, like a neon-lit carnival in outer space.",
        "language": "English",
        "release_year": 2025,
        "popularity": 71,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_032",
        "track_name": "Put It In A Zine",
        "artist": "Tom Misch",
        "album": "Geography",
        "genre": "Jazz",
        "subgenre": "Nu Jazz",
        "mood_tags": [
            "smooth",
            "sunny",
            "upbeat",
            "breezy"
        ],
        "energy": 0.5,
        "valence": 0.75,
        "tempo_bpm": 116,
        "acousticness": 0.45,
        "instrumentalness": 0.3,
        "description": "A sunny, breezy nu-jazz track with clean guitar, smooth grooves, and a carefree summer vibe. Like biking through a park on a perfect spring day.",
        "language": "English",
        "release_year": 2010,
        "popularity": 72,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_033",
        "track_name": "So What",
        "artist": "Miles Davis",
        "album": "Kind of Blue",
        "genre": "Jazz",
        "subgenre": "Modal Jazz",
        "mood_tags": [
            "cool",
            "classic",
            "sophisticated",
            "contemplative"
        ],
        "energy": 0.35,
        "valence": 0.45,
        "tempo_bpm": 136,
        "acousticness": 0.9,
        "instrumentalness": 0.7,
        "description": "The quintessential cool jazz masterpiece with iconic modal harmonies, breathy trumpet, and walking bass. Timeless sophistication in every note.",
        "language": "English",
        "release_year": 2011,
        "popularity": 73,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_034",
        "track_name": "On & On",
        "artist": "Erykah Badu",
        "album": "Baduizm",
        "genre": "Jazz",
        "subgenre": "Neo-Soul",
        "mood_tags": [
            "soulful",
            "smooth",
            "spiritual",
            "warm"
        ],
        "energy": 0.4,
        "valence": 0.55,
        "tempo_bpm": 96,
        "acousticness": 0.5,
        "instrumentalness": 0.1,
        "description": "A smooth, soulful neo-soul track with warm bass, jazzy Rhodes piano, and Badu's hypnotic vocals. Feels like incense smoke curling in a candlelit room.",
        "language": "English",
        "release_year": 2012,
        "popularity": 74,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_035",
        "track_name": "Moon River",
        "artist": "Jacob Collier",
        "album": "Djesse Vol. 2",
        "genre": "Jazz",
        "subgenre": "Vocal Jazz",
        "mood_tags": [
            "ethereal",
            "beautiful",
            "layered",
            "magical"
        ],
        "energy": 0.2,
        "valence": 0.5,
        "tempo_bpm": 72,
        "acousticness": 0.85,
        "instrumentalness": 0.1,
        "description": "A breathtaking reimagining of the classic with stacked vocal harmonies, lush arrangements, and pure magic. Like moonlight reflecting off still water.",
        "language": "English",
        "release_year": 2013,
        "popularity": 75,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_040",
        "track_name": "Alright",
        "artist": "Kendrick Lamar",
        "album": "To Pimp a Butterfly",
        "genre": "Hip-Hop",
        "subgenre": "Conscious Hip-Hop",
        "mood_tags": [
            "empowering",
            "resilient",
            "triumphant",
            "energetic"
        ],
        "energy": 0.75,
        "valence": 0.6,
        "tempo_bpm": 132,
        "acousticness": 0.05,
        "instrumentalness": 0.0,
        "description": "A triumphant, empowering hip-hop anthem with jazz-infused production, defiant lyrics, and an infectious hook. The sound of resilience and hope.",
        "language": "English",
        "release_year": 2018,
        "popularity": 80,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_041",
        "track_name": "Self Care",
        "artist": "Mac Miller",
        "album": "Swimming",
        "genre": "Hip-Hop",
        "subgenre": "Alternative Hip-Hop",
        "mood_tags": [
            "introspective",
            "mellow",
            "therapeutic",
            "chill"
        ],
        "energy": 0.4,
        "valence": 0.35,
        "tempo_bpm": 84,
        "acousticness": 0.1,
        "instrumentalness": 0.05,
        "description": "A mellow, introspective hip-hop track with dreamy production, soft vocals, and a therapeutic quality. Like a deep breath after a long day.",
        "language": "English",
        "release_year": 2019,
        "popularity": 81,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_042",
        "track_name": "Ivy",
        "artist": "Frank Ocean",
        "album": "Blonde",
        "genre": "R&B",
        "subgenre": "Alternative R&B",
        "mood_tags": [
            "nostalgic",
            "bittersweet",
            "ethereal",
            "emotional"
        ],
        "energy": 0.35,
        "valence": 0.25,
        "tempo_bpm": 98,
        "acousticness": 0.4,
        "instrumentalness": 0.05,
        "description": "An ethereal, emotionally raw R&B track with distorted guitars, layered vocals, and a sense of bittersweet nostalgia. Memories dissolving like watercolors in rain.",
        "language": "English",
        "release_year": 2020,
        "popularity": 82,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_043",
        "track_name": "Best Part",
        "artist": "Daniel Caesar ft. H.E.R.",
        "album": "Freudian",
        "genre": "R&B",
        "subgenre": "Contemporary R&B",
        "mood_tags": [
            "romantic",
            "smooth",
            "tender",
            "intimate"
        ],
        "energy": 0.25,
        "valence": 0.65,
        "tempo_bpm": 68,
        "acousticness": 0.6,
        "instrumentalness": 0.0,
        "description": "A silky smooth R&B duet with warm guitar, tender vocals, and effortless chemistry. Pure romantic bliss, like slow dancing in the living room.",
        "language": "English",
        "release_year": 2021,
        "popularity": 83,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_044",
        "track_name": "Pink + White",
        "artist": "Frank Ocean",
        "album": "Blonde",
        "genre": "R&B",
        "subgenre": "Art Pop",
        "mood_tags": [
            "dreamy",
            "nostalgic",
            "warm",
            "luminous"
        ],
        "energy": 0.45,
        "valence": 0.55,
        "tempo_bpm": 80,
        "acousticness": 0.25,
        "instrumentalness": 0.1,
        "description": "A luminous, dreamy track with Pharrell's warm drums, layered choir vocals, and Frank's reflective storytelling. Summer memories crystallized in sound.",
        "language": "English",
        "release_year": 2022,
        "popularity": 84,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_045",
        "track_name": "HUMBLE.",
        "artist": "Kendrick Lamar",
        "album": "DAMN.",
        "genre": "Hip-Hop",
        "subgenre": "Trap",
        "mood_tags": [
            "aggressive",
            "confident",
            "hard-hitting",
            "powerful"
        ],
        "energy": 0.9,
        "valence": 0.4,
        "tempo_bpm": 150,
        "acousticness": 0.0,
        "instrumentalness": 0.0,
        "description": "A hard-hitting trap banger with minimalist piano stabs, thunderous 808s, and ruthlessly confident lyrics. Pure dominance and swagger.",
        "language": "English",
        "release_year": 2023,
        "popularity": 85,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_050",
        "track_name": "Midnight City",
        "artist": "M83",
        "album": "Hurry Up, We're Dreaming",
        "genre": "Electronic",
        "subgenre": "Dream Pop",
        "mood_tags": [
            "euphoric",
            "anthemic",
            "nocturnal",
            "shimmering"
        ],
        "energy": 0.7,
        "valence": 0.65,
        "tempo_bpm": 105,
        "acousticness": 0.02,
        "instrumentalness": 0.3,
        "description": "An anthemic dream pop masterpiece with soaring synths, driving beat, and euphoric saxophone solo. The sound of a city skyline glittering at midnight.",
        "language": "English",
        "release_year": 2012,
        "popularity": 90,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_051",
        "track_name": "Strobe",
        "artist": "deadmau5",
        "album": "For Lack of a Better Name",
        "genre": "Electronic",
        "subgenre": "Progressive House",
        "mood_tags": [
            "epic",
            "building",
            "transcendent",
            "emotional"
        ],
        "energy": 0.6,
        "valence": 0.5,
        "tempo_bpm": 128,
        "acousticness": 0.0,
        "instrumentalness": 0.95,
        "description": "A legendary progressive house epic that builds from a delicate piano intro into layers of emotional synths and a transcendent climax. A 10-minute journey through sound.",
        "language": "English",
        "release_year": 2013,
        "popularity": 91,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_052",
        "track_name": "Tadow",
        "artist": "Masego & FKJ",
        "album": "Tadow Single",
        "genre": "Electronic",
        "subgenre": "Future Jazz",
        "mood_tags": [
            "groovy",
            "smooth",
            "sensual",
            "jazzy"
        ],
        "energy": 0.5,
        "valence": 0.65,
        "tempo_bpm": 100,
        "acousticness": 0.35,
        "instrumentalness": 0.4,
        "description": "A sultry fusion of jazz, electronic, and R&B with live saxophone, looped beats, and a hypnotic groove. Effortlessly cool and impossibly smooth.",
        "language": "English",
        "release_year": 2014,
        "popularity": 92,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_053",
        "track_name": "Flickers",
        "artist": "London Grammar",
        "album": "If You Wait",
        "genre": "Electronic",
        "subgenre": "Downtempo",
        "mood_tags": [
            "haunting",
            "atmospheric",
            "delicate",
            "nocturnal"
        ],
        "energy": 0.2,
        "valence": 0.2,
        "tempo_bpm": 76,
        "acousticness": 0.15,
        "instrumentalness": 0.2,
        "description": "A haunting downtempo track with sparse electronic production, fingerpicked guitar, and an otherworldly vocal performance. Like candlelight flickering in the dark.",
        "language": "English",
        "release_year": 2015,
        "popularity": 93,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_054",
        "track_name": "Innerbloom",
        "artist": "R\u00dcF\u00dcS DU SOL",
        "album": "Bloom",
        "genre": "Electronic",
        "subgenre": "Deep House",
        "mood_tags": [
            "transcendent",
            "emotional",
            "building",
            "hypnotic"
        ],
        "energy": 0.55,
        "valence": 0.4,
        "tempo_bpm": 122,
        "acousticness": 0.0,
        "instrumentalness": 0.45,
        "description": "A transcendent deep house journey that slowly unfolds over 9 minutes with warm synths, emotive vocals, and a mesmerizing climax. Like watching the sunrise from a mountaintop.",
        "language": "English",
        "release_year": 2016,
        "popularity": 94,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_055",
        "track_name": "Something About Us",
        "artist": "Daft Punk",
        "album": "Discovery",
        "genre": "Electronic",
        "subgenre": "French House",
        "mood_tags": [
            "romantic",
            "smooth",
            "futuristic",
            "tender"
        ],
        "energy": 0.3,
        "valence": 0.6,
        "tempo_bpm": 100,
        "acousticness": 0.0,
        "instrumentalness": 0.35,
        "description": "A tender, futuristic love song with vocoder vocals, warm analog synths, and a gentle groove. Robot love at its most human and beautiful.",
        "language": "English",
        "release_year": 2017,
        "popularity": 40,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_060",
        "track_name": "Avril 14th",
        "artist": "Aphex Twin",
        "album": "Drukqs",
        "genre": "Ambient",
        "subgenre": "Ambient Piano",
        "mood_tags": [
            "peaceful",
            "delicate",
            "contemplative",
            "minimal"
        ],
        "energy": 0.05,
        "valence": 0.4,
        "tempo_bpm": 68,
        "acousticness": 0.95,
        "instrumentalness": 1.0,
        "description": "A delicate, crystalline solo piano piece with gentle dynamics and a serene, contemplative quality. Like sunlight filtering through a prism onto a white wall.",
        "language": "English",
        "release_year": 2022,
        "popularity": 45,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_061",
        "track_name": "An Ending (Ascent)",
        "artist": "Brian Eno",
        "album": "Apollo: Atmospheres and Soundtracks",
        "genre": "Ambient",
        "subgenre": "Space Ambient",
        "mood_tags": [
            "transcendent",
            "celestial",
            "peaceful",
            "vast"
        ],
        "energy": 0.1,
        "valence": 0.5,
        "tempo_bpm": 60,
        "acousticness": 0.1,
        "instrumentalness": 1.0,
        "description": "A transcendent ambient piece with slowly evolving synth pads that feel absolutely celestial. The sensation of floating weightlessly in space, watching Earth from orbit.",
        "language": "English",
        "release_year": 2023,
        "popularity": 46,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_062",
        "track_name": "Experience",
        "artist": "Ludovico Einaudi",
        "album": "In a Time Lapse",
        "genre": "Classical",
        "subgenre": "Neoclassical",
        "mood_tags": [
            "emotional",
            "building",
            "cinematic",
            "powerful"
        ],
        "energy": 0.45,
        "valence": 0.3,
        "tempo_bpm": 74,
        "acousticness": 0.9,
        "instrumentalness": 0.95,
        "description": "A breathtaking neoclassical piece that builds from a simple piano motif into a full orchestral climax. Every note carries emotional weight, like watching a life flash before your eyes.",
        "language": "English",
        "release_year": 2024,
        "popularity": 47,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_063",
        "track_name": "Nuvole Bianche",
        "artist": "Ludovico Einaudi",
        "album": "Una Mattina",
        "genre": "Classical",
        "subgenre": "Neoclassical",
        "mood_tags": [
            "ethereal",
            "flowing",
            "romantic",
            "contemplative"
        ],
        "energy": 0.3,
        "valence": 0.45,
        "tempo_bpm": 68,
        "acousticness": 0.95,
        "instrumentalness": 1.0,
        "description": "A flowing, ethereal piano piece with cascading arpeggios and a hauntingly romantic melody. Like watching white clouds drift across a summer sky.",
        "language": "English",
        "release_year": 2025,
        "popularity": 48,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_064",
        "track_name": "Weightless",
        "artist": "Marconi Union",
        "album": "Weightless",
        "genre": "Ambient",
        "subgenre": "Therapeutic Ambient",
        "mood_tags": [
            "calming",
            "therapeutic",
            "sleepy",
            "meditative"
        ],
        "energy": 0.02,
        "valence": 0.35,
        "tempo_bpm": 60,
        "acousticness": 0.1,
        "instrumentalness": 1.0,
        "description": "Scientifically designed to reduce anxiety, this ambient piece uses carefully tuned harmonics, gradually slowing tempo, and spatial sound design. The most relaxing song ever recorded.",
        "language": "English",
        "release_year": 2010,
        "popularity": 49,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_065",
        "track_name": "Divenire",
        "artist": "Ludovico Einaudi",
        "album": "Divenire",
        "genre": "Classical",
        "subgenre": "Neoclassical",
        "mood_tags": [
            "majestic",
            "cinematic",
            "powerful",
            "soaring"
        ],
        "energy": 0.55,
        "valence": 0.5,
        "tempo_bpm": 80,
        "acousticness": 0.85,
        "instrumentalness": 0.9,
        "description": "A majestic neoclassical composition with dramatic piano, sweeping strings, and electronic textures. Like standing on a cliff edge watching the ocean during a storm.",
        "language": "English",
        "release_year": 2011,
        "popularity": 50,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_070",
        "track_name": "Do I Wanna Know?",
        "artist": "Arctic Monkeys",
        "album": "AM",
        "genre": "Rock",
        "subgenre": "Indie Rock",
        "mood_tags": [
            "sultry",
            "dark",
            "groovy",
            "cool"
        ],
        "energy": 0.55,
        "valence": 0.3,
        "tempo_bpm": 85,
        "acousticness": 0.05,
        "instrumentalness": 0.1,
        "description": "A sultry, dark indie rock track with a hypnotic riff, rumbling bass, and Alex Turner's brooding vocals. Late-night confidence and magnetic cool.",
        "language": "English",
        "release_year": 2016,
        "popularity": 55,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_071",
        "track_name": "Creep",
        "artist": "Radiohead",
        "album": "Pablo Honey",
        "genre": "Rock",
        "subgenre": "Alternative Rock",
        "mood_tags": [
            "angsty",
            "vulnerable",
            "explosive",
            "raw"
        ],
        "energy": 0.55,
        "valence": 0.15,
        "tempo_bpm": 92,
        "acousticness": 0.15,
        "instrumentalness": 0.0,
        "description": "A raw, vulnerable alt-rock anthem that explodes from quiet desperation into cathartic distortion. The universal feeling of not belonging, distilled into song.",
        "language": "English",
        "release_year": 2017,
        "popularity": 56,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_072",
        "track_name": "Under the Bridge",
        "artist": "Red Hot Chili Peppers",
        "album": "Blood Sugar Sex Magik",
        "genre": "Rock",
        "subgenre": "Alternative Rock",
        "mood_tags": [
            "melancholic",
            "reflective",
            "warm",
            "bittersweet"
        ],
        "energy": 0.4,
        "valence": 0.3,
        "tempo_bpm": 86,
        "acousticness": 0.3,
        "instrumentalness": 0.05,
        "description": "A melancholic rock ballad about loneliness and belonging with warm guitar tones and Anthony Kiedis's reflective vocals. The city at twilight, beautiful but lonely.",
        "language": "English",
        "release_year": 2018,
        "popularity": 57,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_073",
        "track_name": "Everlong",
        "artist": "Foo Fighters",
        "album": "The Colour and the Shape",
        "genre": "Rock",
        "subgenre": "Alt-Rock",
        "mood_tags": [
            "passionate",
            "driving",
            "anthemic",
            "romantic"
        ],
        "energy": 0.8,
        "valence": 0.55,
        "tempo_bpm": 158,
        "acousticness": 0.0,
        "instrumentalness": 0.05,
        "description": "A passionate, driving rock anthem with surging guitars, pounding drums, and an irresistible melodic hook. The sound of breathless, all-consuming devotion.",
        "language": "English",
        "release_year": 2019,
        "popularity": 58,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_074",
        "track_name": "Karma Police",
        "artist": "Radiohead",
        "album": "OK Computer",
        "genre": "Rock",
        "subgenre": "Art Rock",
        "mood_tags": [
            "paranoid",
            "dystopian",
            "contemplative",
            "haunting"
        ],
        "energy": 0.45,
        "valence": 0.2,
        "tempo_bpm": 74,
        "acousticness": 0.35,
        "instrumentalness": 0.1,
        "description": "A haunting art-rock masterpiece with cinematic piano, swelling guitars, and Thom Yorke's eerie falsetto. A creeping sense of existential dread wrapped in beautiful melody.",
        "language": "English",
        "release_year": 2020,
        "popularity": 59,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_075",
        "track_name": "Hysteria",
        "artist": "Muse",
        "album": "Absolution",
        "genre": "Rock",
        "subgenre": "Alternative Rock",
        "mood_tags": [
            "intense",
            "powerful",
            "driving",
            "dramatic"
        ],
        "energy": 0.85,
        "valence": 0.35,
        "tempo_bpm": 94,
        "acousticness": 0.0,
        "instrumentalness": 0.1,
        "description": "An intense, powerful rock track with one of the most iconic bass riffs in modern rock, thunderous drums, and operatic drama. Pure adrenaline and musical fury.",
        "language": "English",
        "release_year": 2021,
        "popularity": 60,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_076",
        "track_name": "Electric Feel",
        "artist": "MGMT",
        "album": "Oracular Spectacular",
        "genre": "Rock",
        "subgenre": "Psychedelic Pop",
        "mood_tags": [
            "groovy",
            "psychedelic",
            "summery",
            "euphoric"
        ],
        "energy": 0.65,
        "valence": 0.75,
        "tempo_bpm": 120,
        "acousticness": 0.05,
        "instrumentalness": 0.2,
        "description": "A groovy psychedelic pop track with funky bass, shimmering synths, and a sun-drenched euphoric atmosphere. Dancing barefoot on a warm summer night.",
        "language": "English",
        "release_year": 2022,
        "popularity": 61,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_080",
        "track_name": "Cruel Summer",
        "artist": "Taylor Swift",
        "album": "Lover",
        "genre": "Pop",
        "subgenre": "Synth Pop",
        "mood_tags": [
            "euphoric",
            "anthemic",
            "summery",
            "passionate"
        ],
        "energy": 0.7,
        "valence": 0.55,
        "tempo_bpm": 170,
        "acousticness": 0.0,
        "instrumentalness": 0.0,
        "description": "An explosive synth-pop anthem with soaring hooks, pulsing production, and impassioned vocals. The intensity of a summer love that burns too bright.",
        "language": "English",
        "release_year": 2010,
        "popularity": 65,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_081",
        "track_name": "Motion Sickness",
        "artist": "Phoebe Bridgers",
        "album": "Stranger in the Alps",
        "genre": "Pop",
        "subgenre": "Indie Pop",
        "mood_tags": [
            "sardonic",
            "melancholic",
            "witty",
            "intimate"
        ],
        "energy": 0.4,
        "valence": 0.25,
        "tempo_bpm": 100,
        "acousticness": 0.35,
        "instrumentalness": 0.0,
        "description": "A darkly witty indie pop song with shimmering guitars, sardonic lyrics, and an undercurrent of real pain. Humor as a defense mechanism against heartbreak.",
        "language": "English",
        "release_year": 2011,
        "popularity": 66,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_082",
        "track_name": "Heat Waves",
        "artist": "Glass Animals",
        "album": "Dreamland",
        "genre": "Pop",
        "subgenre": "Psychedelic Pop",
        "mood_tags": [
            "dreamy",
            "melancholic",
            "summery",
            "hazy"
        ],
        "energy": 0.5,
        "valence": 0.35,
        "tempo_bpm": 80,
        "acousticness": 0.05,
        "instrumentalness": 0.1,
        "description": "A dreamy, hazy pop track with woozy synths, a hypnotic beat, and vocals that float between melancholy and warmth. Late summer heat shimmering on the asphalt.",
        "language": "English",
        "release_year": 2012,
        "popularity": 67,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_083",
        "track_name": "Bags",
        "artist": "Clairo",
        "album": "Immunity",
        "genre": "Pop",
        "subgenre": "Bedroom Pop",
        "mood_tags": [
            "tender",
            "nervous",
            "romantic",
            "vulnerable"
        ],
        "energy": 0.35,
        "valence": 0.4,
        "tempo_bpm": 112,
        "acousticness": 0.2,
        "instrumentalness": 0.05,
        "description": "A tender bedroom pop song about unspoken romantic tension with jangly guitars and earnest, slightly nervous vocals. Butterflies in the stomach, put to music.",
        "language": "English",
        "release_year": 2013,
        "popularity": 68,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_084",
        "track_name": "Levitating",
        "artist": "Dua Lipa",
        "album": "Future Nostalgia",
        "genre": "Pop",
        "subgenre": "Disco Pop",
        "mood_tags": [
            "joyful",
            "energetic",
            "danceable",
            "retro"
        ],
        "energy": 0.8,
        "valence": 0.85,
        "tempo_bpm": 103,
        "acousticness": 0.0,
        "instrumentalness": 0.0,
        "description": "A high-energy disco-pop banger with funky bass, retro synths, and an unstoppable groove. Pure joy distilled into three and a half minutes of dance floor bliss.",
        "language": "English",
        "release_year": 2014,
        "popularity": 69,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_085",
        "track_name": "Ceilings",
        "artist": "Lizzy McAlpine",
        "album": "Five Seconds Flat",
        "genre": "Pop",
        "subgenre": "Indie Pop",
        "mood_tags": [
            "bittersweet",
            "dreamy",
            "yearning",
            "intimate"
        ],
        "energy": 0.35,
        "valence": 0.3,
        "tempo_bpm": 130,
        "acousticness": 0.4,
        "instrumentalness": 0.0,
        "description": "A bittersweet indie pop track about the gap between daydreams and reality, with delicate production and an emotionally devastating bridge. Hope dissolving into waking life.",
        "language": "English",
        "release_year": 2015,
        "popularity": 70,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_086",
        "track_name": "Tongue Tied",
        "artist": "Grouplove",
        "album": "Never Trust a Happy Song",
        "genre": "Pop",
        "subgenre": "Indie Pop",
        "mood_tags": [
            "upbeat",
            "carefree",
            "energetic",
            "singalong"
        ],
        "energy": 0.75,
        "valence": 0.8,
        "tempo_bpm": 148,
        "acousticness": 0.05,
        "instrumentalness": 0.0,
        "description": "An explosively upbeat indie pop anthem with shout-along vocals, crunchy guitars, and infectious energy. The feeling of running through a field on the last day of school.",
        "language": "English",
        "release_year": 2016,
        "popularity": 71,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_090",
        "track_name": "Ojuelegba",
        "artist": "Wizkid",
        "album": "Ayo",
        "genre": "Afrobeats",
        "subgenre": "Afropop",
        "mood_tags": [
            "uplifting",
            "rhythmic",
            "warm",
            "celebratory"
        ],
        "energy": 0.6,
        "valence": 0.7,
        "tempo_bpm": 105,
        "acousticness": 0.1,
        "instrumentalness": 0.1,
        "description": "A warm, uplifting Afropop anthem with infectious rhythms, bright percussion, and soulful vocals. The soundtrack to a vibrant Lagos street celebration.",
        "language": "English",
        "release_year": 2020,
        "popularity": 75,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_091",
        "track_name": "Despacito",
        "artist": "Luis Fonsi ft. Daddy Yankee",
        "album": "Vida",
        "genre": "Latin",
        "subgenre": "Reggaeton",
        "mood_tags": [
            "sensual",
            "danceable",
            "tropical",
            "rhythmic"
        ],
        "energy": 0.7,
        "valence": 0.75,
        "tempo_bpm": 89,
        "acousticness": 0.2,
        "instrumentalness": 0.0,
        "description": "A sensual Latin pop-reggaeton fusion with acoustic guitar, tropical percussion, and an irresistible rhythm. Warm Caribbean nights and salsa dancing.",
        "language": "English",
        "release_year": 2021,
        "popularity": 76,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_092",
        "track_name": "Bambaataa",
        "artist": "Burna Boy",
        "album": "African Giant",
        "genre": "Afrobeats",
        "subgenre": "Afro-Fusion",
        "mood_tags": [
            "powerful",
            "rhythmic",
            "anthemic",
            "cultural"
        ],
        "energy": 0.65,
        "valence": 0.6,
        "tempo_bpm": 110,
        "acousticness": 0.15,
        "instrumentalness": 0.1,
        "description": "A powerful Afro-fusion anthem with layered percussion, horn stabs, and Burna Boy's commanding vocals. Cultural pride and musical innovation colliding.",
        "language": "English",
        "release_year": 2022,
        "popularity": 77,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_095",
        "track_name": "Master of Puppets",
        "artist": "Metallica",
        "album": "Master of Puppets",
        "genre": "Metal",
        "subgenre": "Thrash Metal",
        "mood_tags": [
            "aggressive",
            "powerful",
            "dark",
            "relentless"
        ],
        "energy": 0.95,
        "valence": 0.15,
        "tempo_bpm": 212,
        "acousticness": 0.0,
        "instrumentalness": 0.2,
        "description": "A legendary thrash metal masterpiece with blistering guitar riffs, machine-gun drumming, and a relentless, dark intensity. Eight minutes of pure controlled fury.",
        "language": "English",
        "release_year": 2025,
        "popularity": 80,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_096",
        "track_name": "Schism",
        "artist": "Tool",
        "album": "Lateralus",
        "genre": "Metal",
        "subgenre": "Progressive Metal",
        "mood_tags": [
            "complex",
            "hypnotic",
            "cerebral",
            "dark"
        ],
        "energy": 0.65,
        "valence": 0.2,
        "tempo_bpm": 96,
        "acousticness": 0.0,
        "instrumentalness": 0.25,
        "description": "A cerebral progressive metal track with polyrhythmic drumming, hypnotic bass, and shifting time signatures. Music as mathematical precision meets primal emotion.",
        "language": "English",
        "release_year": 2010,
        "popularity": 81,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_097",
        "track_name": "Tennessee Whiskey",
        "artist": "Chris Stapleton",
        "album": "Traveller",
        "genre": "Country",
        "subgenre": "Blues Country",
        "mood_tags": [
            "soulful",
            "warm",
            "smooth",
            "romantic"
        ],
        "energy": 0.4,
        "valence": 0.6,
        "tempo_bpm": 84,
        "acousticness": 0.45,
        "instrumentalness": 0.0,
        "description": "A soulful country blues masterpiece with honey-smooth vocals, warm guitar, and a timeless romantic quality. Like aged whiskey by a fireplace on a cold night.",
        "language": "English",
        "release_year": 2011,
        "popularity": 82,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_098",
        "track_name": "Fast Car",
        "artist": "Tracy Chapman",
        "album": "Tracy Chapman",
        "genre": "Country",
        "subgenre": "Folk Rock",
        "mood_tags": [
            "hopeful",
            "bittersweet",
            "storytelling",
            "driving"
        ],
        "energy": 0.45,
        "valence": 0.4,
        "tempo_bpm": 104,
        "acousticness": 0.65,
        "instrumentalness": 0.0,
        "description": "A poignant folk-rock story-song with propulsive acoustic guitar and a voice that carries the weight of dreams deferred. Hope and heartbreak on the open road.",
        "language": "English",
        "release_year": 2012,
        "popularity": 83,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_099",
        "track_name": "Three Little Birds",
        "artist": "Bob Marley",
        "album": "Exodus",
        "genre": "Reggae",
        "subgenre": "Roots Reggae",
        "mood_tags": [
            "positive",
            "peaceful",
            "reassuring",
            "sunny"
        ],
        "energy": 0.45,
        "valence": 0.85,
        "tempo_bpm": 76,
        "acousticness": 0.35,
        "instrumentalness": 0.05,
        "description": "An eternally reassuring reggae classic with gentle skanking rhythm, warm vocals, and an unshakeable positivity. Every little thing is gonna be alright.",
        "language": "English",
        "release_year": 2013,
        "popularity": 84,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_100",
        "track_name": "Is This Love",
        "artist": "Bob Marley",
        "album": "Kaya",
        "genre": "Reggae",
        "subgenre": "Lover's Rock",
        "mood_tags": [
            "romantic",
            "warm",
            "peaceful",
            "groovy"
        ],
        "energy": 0.4,
        "valence": 0.7,
        "tempo_bpm": 82,
        "acousticness": 0.3,
        "instrumentalness": 0.05,
        "description": "A warm, romantic reggae love song with an irresistible groove, sweet harmonies, and Bob's tender vocal delivery. Island breezes and endless summer evenings.",
        "language": "English",
        "release_year": 2014,
        "popularity": 85,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_101",
        "track_name": "Apsara Aali",
        "artist": "Ajay-Atul, Bela Shende",
        "album": "Natarang",
        "genre": "Marathi",
        "subgenre": "Lavani",
        "mood_tags": [
            "energetic",
            "festive",
            "dance",
            "playful"
        ],
        "energy": 0.75,
        "valence": 0.8,
        "tempo_bpm": 125,
        "acousticness": 0.4,
        "instrumentalness": 0.0,
        "description": "A vibrant and high-energy Marathi dance track featuring traditional dholki beats and powerful vocals. The sound of a celebration.",
        "language": "Marathi",
        "release_year": 2015,
        "popularity": 86,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_102",
        "track_name": "Sairat Zaala Ji",
        "artist": "Ajay-Atul, Chinmayi Sripada",
        "album": "Sairat",
        "genre": "Marathi",
        "subgenre": "Romantic",
        "mood_tags": [
            "romantic",
            "passionate",
            "dreamy",
            "melodic"
        ],
        "energy": 0.55,
        "valence": 0.6,
        "tempo_bpm": 98,
        "acousticness": 0.5,
        "instrumentalness": 0.0,
        "description": "A sweeping Marathi romantic ballad with grand orchestral arrangements, lush string sections, and heartfelt vocals. Evokes the feeling of first love.",
        "language": "Marathi",
        "release_year": 2016,
        "popularity": 87,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_103",
        "track_name": "Yad Lagla",
        "artist": "Ajay-Atul",
        "album": "Sairat",
        "genre": "Marathi",
        "subgenre": "Romantic",
        "mood_tags": [
            "romantic",
            "emotional",
            "epic",
            "dramatic"
        ],
        "energy": 0.5,
        "valence": 0.4,
        "tempo_bpm": 90,
        "acousticness": 0.6,
        "instrumentalness": 0.0,
        "description": "An emotionally intense, symphonic Marathi ballad with dramatic orchestral builds and raw, vulnerable vocals depicting the obsession of love.",
        "language": "Marathi",
        "release_year": 2017,
        "popularity": 88,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_104",
        "track_name": "Jiv Rangala",
        "artist": "Hariharan, Shreya Ghoshal",
        "album": "Jogwa",
        "genre": "Marathi",
        "subgenre": "Romantic",
        "mood_tags": [
            "romantic",
            "melodic",
            "serene",
            "emotional"
        ],
        "energy": 0.4,
        "valence": 0.5,
        "tempo_bpm": 85,
        "acousticness": 0.7,
        "instrumentalness": 0.0,
        "description": "A soothing, classical-infused Marathi love song with tender flute melodies, soft acoustic backing, and flawless duet vocals.",
        "language": "Marathi",
        "release_year": 2018,
        "popularity": 89,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_105",
        "track_name": "Kombdi Palali",
        "artist": "Anand Shinde, Vaishali Samant",
        "album": "Jatra",
        "genre": "Marathi",
        "subgenre": "Folk",
        "mood_tags": [
            "energetic",
            "upbeat",
            "dance",
            "festive"
        ],
        "energy": 0.85,
        "valence": 0.9,
        "tempo_bpm": 135,
        "acousticness": 0.2,
        "instrumentalness": 0.0,
        "description": "A fast-paced, highly energetic Marathi folk-dance track with a driving rhythm and infectious hook. Guaranteed to make everyone dance.",
        "language": "Marathi",
        "release_year": 2019,
        "popularity": 90,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_106",
        "track_name": "Baharla Ha Madhumas",
        "artist": "Shreya Ghoshal, Ajay-Atul",
        "album": "Maharashtra Shahir",
        "genre": "Marathi",
        "subgenre": "Romantic",
        "mood_tags": [
            "joyful",
            "romantic",
            "cheerful",
            "upbeat"
        ],
        "energy": 0.65,
        "valence": 0.75,
        "tempo_bpm": 112,
        "acousticness": 0.45,
        "instrumentalness": 0.0,
        "description": "A playful and joyful Marathi romantic track with cheerful acoustic arrangements, catchy rhythms, and lighthearted vocals expressing the arrival of spring.",
        "language": "Marathi",
        "release_year": 2020,
        "popularity": 91,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_107",
        "track_name": "Mee Raat Takali",
        "artist": "Lata Mangeshkar",
        "album": "Jait Re Jait",
        "genre": "Marathi",
        "subgenre": "Bhavgeet",
        "mood_tags": [
            "melancholic",
            "reflective",
            "poetic",
            "acoustic"
        ],
        "energy": 0.25,
        "valence": 0.3,
        "tempo_bpm": 80,
        "acousticness": 0.9,
        "instrumentalness": 0.05,
        "description": "A legendary, poetic Marathi song with acoustic percussion, beautiful flute interludes, and soulful, clean vocals expressing longing in the night.",
        "language": "Marathi",
        "release_year": 2021,
        "popularity": 92,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_108",
        "track_name": "Tujhe Dekha Toh",
        "artist": "Kumar Sanu, Lata Mangeshkar",
        "album": "Dilwale Dulhania Le Jayenge",
        "genre": "Bollywood 90s",
        "subgenre": "Romantic",
        "mood_tags": [
            "romantic",
            "nostalgic",
            "tender",
            "melodic"
        ],
        "energy": 0.5,
        "valence": 0.65,
        "tempo_bpm": 92,
        "acousticness": 0.55,
        "instrumentalness": 0.0,
        "description": "The quintessential 90s Bollywood love anthem featuring lush acoustic guitar, mandolin, and nostalgic vocals. Pure romance in the mustard fields.",
        "language": "Hindi",
        "release_year": 1992,
        "popularity": 93,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_109",
        "track_name": "Chaiyya Chaiyya",
        "artist": "Sukhwinder Singh, Sapna Awasthi",
        "album": "Dil Se..",
        "genre": "Bollywood 90s",
        "subgenre": "Dance",
        "mood_tags": [
            "energetic",
            "upbeat",
            "rhythmic",
            "festive"
        ],
        "energy": 0.88,
        "valence": 0.85,
        "tempo_bpm": 120,
        "acousticness": 0.15,
        "instrumentalness": 0.0,
        "description": "An iconic, high-energy 90s Bollywood dance song with a driving folk-fusion beat, powerful vocals, and energetic train-top rhythm.",
        "language": "Hindi",
        "release_year": 1992,
        "popularity": 94,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_110",
        "track_name": "Pehla Nasha",
        "artist": "Udit Narayan, Sadhana Sargam",
        "album": "Jo Jeeta Wohi Sikandar",
        "genre": "Bollywood 90s",
        "subgenre": "Romantic",
        "mood_tags": [
            "dreamy",
            "romantic",
            "tender",
            "youthful"
        ],
        "energy": 0.45,
        "valence": 0.7,
        "tempo_bpm": 88,
        "acousticness": 0.6,
        "instrumentalness": 0.0,
        "description": "A dreamy, floating 90s romantic song featuring piano chords, light percussion, and airy vocals capturing the sweet feeling of first love.",
        "language": "Hindi",
        "release_year": 1992,
        "popularity": 40,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_111",
        "track_name": "Dheere Dheere Se",
        "artist": "Kumar Sanu, Anuradha Paudwal",
        "album": "Aashiqui",
        "genre": "Bollywood 90s",
        "subgenre": "Romantic",
        "mood_tags": [
            "romantic",
            "nostalgic",
            "gentle",
            "melancholic"
        ],
        "energy": 0.4,
        "valence": 0.5,
        "tempo_bpm": 84,
        "acousticness": 0.5,
        "instrumentalness": 0.0,
        "description": "A classic 90s romantic ballad with gentle rhythms, melodious violin arrangements, and nostalgic vocals that define the golden era of love songs.",
        "language": "Hindi",
        "release_year": 1992,
        "popularity": 41,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_112",
        "track_name": "Chura Ke Dil Mera",
        "artist": "Kumar Sanu, Alka Yagnik",
        "album": "Main Khiladi Tu Anari",
        "genre": "Bollywood 90s",
        "subgenre": "Romantic",
        "mood_tags": [
            "playful",
            "romantic",
            "groovy",
            "catchy"
        ],
        "energy": 0.68,
        "valence": 0.8,
        "tempo_bpm": 105,
        "acousticness": 0.3,
        "instrumentalness": 0.0,
        "description": "A playful and groovy 90s Bollywood romantic hit with a catchy bassline, tropical conga beats, and flirtatious vocal delivery.",
        "language": "Hindi",
        "release_year": 1992,
        "popularity": 42,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_113",
        "track_name": "Dil To Pagal Hai",
        "artist": "Udit Narayan, Lata Mangeshkar",
        "album": "Dil To Pagal Hai",
        "genre": "Bollywood 90s",
        "subgenre": "Romantic",
        "mood_tags": [
            "romantic",
            "joyful",
            "dreamy",
            "melodic"
        ],
        "energy": 0.55,
        "valence": 0.7,
        "tempo_bpm": 96,
        "acousticness": 0.4,
        "instrumentalness": 0.0,
        "description": "A joyful and dreamy 90s Bollywood song filled with melodic keyboard chords, rhythmic acoustic drums, and soaring romantic vocals.",
        "language": "Hindi",
        "release_year": 1992,
        "popularity": 43,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_114",
        "track_name": "Tum Mile Dil Khile",
        "artist": "Kumar Sanu, Alka Yagnik",
        "album": "Criminal",
        "genre": "Bollywood 90s",
        "subgenre": "Romantic",
        "mood_tags": [
            "romantic",
            "tender",
            "melancholic",
            "intense"
        ],
        "energy": 0.48,
        "valence": 0.45,
        "tempo_bpm": 86,
        "acousticness": 0.5,
        "instrumentalness": 0.0,
        "description": "An intense and atmospheric 90s romantic track with a blending electronic keyboard pad, soft beats, and deeply emotional vocals.",
        "language": "Hindi",
        "release_year": 1992,
        "popularity": 44,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_115",
        "track_name": "Udd Gaye",
        "artist": "Ritviz",
        "album": "DEV",
        "genre": "Hindi Pop",
        "subgenre": "Electronic Pop",
        "mood_tags": [
            "energetic",
            "upbeat",
            "playful",
            "joyful"
        ],
        "energy": 0.72,
        "valence": 0.85,
        "tempo_bpm": 118,
        "acousticness": 0.15,
        "instrumentalness": 0.05,
        "description": "A quirky and highly infectious Hindi electro-pop track with catchy vocal chops, upbeat rhythms, and a joyful festival vibe.",
        "language": "English",
        "release_year": 2013,
        "popularity": 45,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_116",
        "track_name": "Baarishein",
        "artist": "Anuv Jain",
        "album": "Baarishein Single",
        "genre": "Hindi Pop",
        "subgenre": "Acoustic Pop",
        "mood_tags": [
            "romantic",
            "tender",
            "gentle",
            "melancholic"
        ],
        "energy": 0.3,
        "valence": 0.45,
        "tempo_bpm": 95,
        "acousticness": 0.85,
        "instrumentalness": 0.0,
        "description": "A soulful, stripped-back acoustic Hindi song featuring gentle ukulele strumming and vulnerable vocals about love and rain.",
        "language": "English",
        "release_year": 2014,
        "popularity": 46,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_117",
        "track_name": "Kasoor",
        "artist": "Prateek Kuhad",
        "album": "Kasoor Single",
        "genre": "Hindi Pop",
        "subgenre": "Singer-Songwriter",
        "mood_tags": [
            "dreamy",
            "romantic",
            "peaceful",
            "tender"
        ],
        "energy": 0.35,
        "valence": 0.6,
        "tempo_bpm": 102,
        "acousticness": 0.75,
        "instrumentalness": 0.0,
        "description": "An intimate, dreamy indie pop song in Hindi with soft piano chords, light acoustic guitars, and sweet, whispering vocals.",
        "language": "English",
        "release_year": 2015,
        "popularity": 47,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_118",
        "track_name": "Lollipop Lagelu",
        "artist": "Pawan Singh",
        "album": "Lolipop Lagelu Album",
        "genre": "Bhojpuri",
        "subgenre": "Folk Pop",
        "mood_tags": [
            "energetic",
            "upbeat",
            "dance",
            "festive"
        ],
        "energy": 0.85,
        "valence": 0.9,
        "tempo_bpm": 130,
        "acousticness": 0.1,
        "instrumentalness": 0.0,
        "description": "An iconic, high-octane Bhojpuri dance anthem featuring pumping electronic beats, local shehnai hooks, and highly energetic vocals.",
        "language": "Bhojpuri",
        "release_year": 2016,
        "popularity": 48,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_119",
        "track_name": "Raja Ji",
        "artist": "Khesari Lal Yadav",
        "album": "Raja Ji Single",
        "genre": "Bhojpuri",
        "subgenre": "Dance",
        "mood_tags": [
            "energetic",
            "festive",
            "dance",
            "playful"
        ],
        "energy": 0.8,
        "valence": 0.85,
        "tempo_bpm": 125,
        "acousticness": 0.2,
        "instrumentalness": 0.0,
        "description": "A fast-paced Bhojpuri track with heavy local percussion, celebratory brass sections, and playful duet singing perfect for weddings and festivals.",
        "language": "Bhojpuri",
        "release_year": 2017,
        "popularity": 49,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_120",
        "track_name": "Kashi Hile Patna Hile",
        "artist": "Manoj Tiwari",
        "album": "Patna Hile Album",
        "genre": "Bhojpuri",
        "subgenre": "Traditional Folk",
        "mood_tags": [
            "energetic",
            "upbeat",
            "traditional",
            "cultural"
        ],
        "energy": 0.75,
        "valence": 0.8,
        "tempo_bpm": 120,
        "acousticness": 0.3,
        "instrumentalness": 0.0,
        "description": "A legendary, rhythmic Bhojpuri traditional folk song celebrating local heritage with traditional drums, dholak beats, and resonant vocals.",
        "language": "Bhojpuri",
        "release_year": 2018,
        "popularity": 50,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_121",
        "track_name": "Rowdy Baby",
        "artist": "Dhanush, Dhee",
        "album": "Maari 2",
        "genre": "Tamil",
        "subgenre": "Kuthu Fusion",
        "mood_tags": [
            "energetic",
            "upbeat",
            "dance",
            "playful"
        ],
        "energy": 0.88,
        "valence": 0.85,
        "tempo_bpm": 124,
        "acousticness": 0.2,
        "instrumentalness": 0.0,
        "description": "An explosive, high-energy Tamil dance track featuring a blend of traditional Kuthu percussion, jazzy guitar riffs, and fun, playful vocals.",
        "language": "Tamil",
        "release_year": 2019,
        "popularity": 51,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_122",
        "track_name": "Tum Tum",
        "artist": "Sri Vardhini, Aditi, Ananya",
        "album": "Enemy",
        "genre": "Tamil",
        "subgenre": "Wedding Folk",
        "mood_tags": [
            "joyful",
            "upbeat",
            "festive",
            "cheerful"
        ],
        "energy": 0.72,
        "valence": 0.8,
        "tempo_bpm": 110,
        "acousticness": 0.4,
        "instrumentalness": 0.0,
        "description": "A bright, cheerful Tamil wedding folk-pop song with sweet female vocal harmonies, acoustic instruments, and a catchy, celebratory rhythm.",
        "language": "Tamil",
        "release_year": 2020,
        "popularity": 52,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_123",
        "track_name": "Kaadhal Konjam",
        "artist": "Anirudh Ravichander",
        "album": "3",
        "genre": "Tamil",
        "subgenre": "Romantic",
        "mood_tags": [
            "romantic",
            "tender",
            "melodic",
            "dreamy"
        ],
        "energy": 0.45,
        "valence": 0.5,
        "tempo_bpm": 88,
        "acousticness": 0.6,
        "instrumentalness": 0.0,
        "description": "A melodious, contemporary Tamil love song with acoustic guitar, clean piano notes, and a soulful, emotional vocal performance.",
        "language": "Tamil",
        "release_year": 2021,
        "popularity": 53,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_124",
        "track_name": "Singara Siriye",
        "artist": "Vijay Prakash, Ananya Bhat",
        "album": "Kantara",
        "genre": "Kannada",
        "subgenre": "Folk Fusion",
        "mood_tags": [
            "energetic",
            "festive",
            "traditional",
            "passionate"
        ],
        "energy": 0.78,
        "valence": 0.7,
        "tempo_bpm": 115,
        "acousticness": 0.5,
        "instrumentalness": 0.0,
        "description": "A majestic Kannada folk-fusion track with driving local drums, haunting traditional wind instruments, and powerful, passionate vocals.",
        "language": "Kannada",
        "release_year": 2022,
        "popularity": 54,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_125",
        "track_name": "Belageddu",
        "artist": "Vijay Prakash",
        "album": "Kirik Party",
        "genre": "Kannada",
        "subgenre": "Romantic",
        "mood_tags": [
            "joyful",
            "cheerful",
            "romantic",
            "upbeat"
        ],
        "energy": 0.68,
        "valence": 0.75,
        "tempo_bpm": 108,
        "acousticness": 0.4,
        "instrumentalness": 0.0,
        "description": "A breezy, lighthearted Kannada romantic song with cheerful acoustic guitars, bright whistles, and an upbeat, feel-good vocal delivery.",
        "language": "Kannada",
        "release_year": 2023,
        "popularity": 55,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_126",
        "track_name": "Raajakumara",
        "artist": "Vijay Prakash",
        "album": "Raajakumara",
        "genre": "Kannada",
        "subgenre": "Inspirational",
        "mood_tags": [
            "warm",
            "emotional",
            "inspirational",
            "uplifting"
        ],
        "energy": 0.6,
        "valence": 0.65,
        "tempo_bpm": 92,
        "acousticness": 0.35,
        "instrumentalness": 0.0,
        "description": "A heart-touching and uplifting Kannada anthem with sweeping orchestral strings, warm acoustic backings, and powerful, emotionally resonant vocals.",
        "language": "Kannada",
        "release_year": 2024,
        "popularity": 56,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_127",
        "track_name": "Kesariya",
        "artist": "Arijit Singh",
        "album": "Brahmastra",
        "genre": "Bollywood",
        "subgenre": "Romantic",
        "mood_tags": [
            "romantic",
            "melodic",
            "tender",
            "dreamy"
        ],
        "energy": 0.58,
        "valence": 0.62,
        "tempo_bpm": 94,
        "acousticness": 0.5,
        "instrumentalness": 0.0,
        "description": "A sweeping Bollywood romantic ballad with acoustic guitars, soaring violin pads, and Arijit's signature emotive vocals.",
        "language": "Hindi",
        "release_year": 2025,
        "popularity": 57,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_128",
        "track_name": "Apna Bana Le",
        "artist": "Arijit Singh, Sachin-Jigar",
        "album": "Bhediya",
        "genre": "Bollywood",
        "subgenre": "Romantic",
        "mood_tags": [
            "romantic",
            "emotional",
            "intense",
            "soulful"
        ],
        "energy": 0.52,
        "valence": 0.4,
        "tempo_bpm": 88,
        "acousticness": 0.6,
        "instrumentalness": 0.0,
        "description": "A deeply emotional and intense Bollywood love song featuring soft harmonium notes, acoustic guitar, and highly soulful vocals.",
        "language": "Hindi",
        "release_year": 2010,
        "popularity": 58,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_129",
        "track_name": "Kar Gayi Chull",
        "artist": "Badshah, Fazilpuria, Sukriti Kakar, Neha Kakkar",
        "album": "Kapoor & Sons",
        "genre": "Bollywood",
        "subgenre": "Party",
        "mood_tags": [
            "energetic",
            "upbeat",
            "dance",
            "euphoric"
        ],
        "energy": 0.88,
        "valence": 0.82,
        "tempo_bpm": 122,
        "acousticness": 0.08,
        "instrumentalness": 0.0,
        "description": "A highly energetic Bollywood party banger with heavy electronic synth loops, trap-infused beats, and a catchy danceable hook.",
        "language": "Hindi",
        "release_year": 2011,
        "popularity": 59,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_130",
        "track_name": "Lag Jaa Gale",
        "artist": "Lata Mangeshkar",
        "album": "Woh Kaun Thi?",
        "genre": "Old Classic",
        "subgenre": "Retro Romantic",
        "mood_tags": [
            "melancholic",
            "romantic",
            "nostalgic",
            "tender"
        ],
        "energy": 0.22,
        "valence": 0.35,
        "tempo_bpm": 78,
        "acousticness": 0.85,
        "instrumentalness": 0.0,
        "description": "A legendary, hauntingly beautiful Hindi retro ballad featuring clean acoustic guitar, traditional sitar/flute touches, and Lata's iconic, velvety vocals of longing.",
        "language": "Hindi",
        "release_year": 2012,
        "popularity": 60,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_131",
        "track_name": "Pal Pal Dil Ke Paas",
        "artist": "Kishore Kumar",
        "album": "Blackmail",
        "genre": "Old Classic",
        "subgenre": "Retro Romantic",
        "mood_tags": [
            "romantic",
            "nostalgic",
            "warm",
            "gentle"
        ],
        "energy": 0.38,
        "valence": 0.55,
        "tempo_bpm": 84,
        "acousticness": 0.7,
        "instrumentalness": 0.0,
        "description": "A warm and soothing 70s Hindi romantic classic with gentle acoustic guitars, melodic flute arrangements, and Kishore's comforting voice.",
        "language": "Hindi",
        "release_year": 2013,
        "popularity": 61,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_132",
        "track_name": "Pyaar Karne Waale",
        "artist": "Asha Bhosle",
        "album": "Shaan",
        "genre": "Old Classic",
        "subgenre": "Retro Dance",
        "mood_tags": [
            "energetic",
            "upbeat",
            "retro",
            "playful"
        ],
        "energy": 0.65,
        "valence": 0.72,
        "tempo_bpm": 115,
        "acousticness": 0.3,
        "instrumentalness": 0.0,
        "description": "A groovy and energetic late-70s Bollywood disco classic featuring retro horns, funk guitar strumming, and a playful, upbeat vocal delivery.",
        "language": "Hindi",
        "release_year": 2014,
        "popularity": 62,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_133",
        "track_name": "Pasoori",
        "artist": "Ali Sethi, Shae Gill",
        "album": "Pasoori Single",
        "genre": "Hindi Pop",
        "subgenre": "Folk Pop Fusion",
        "mood_tags": [
            "upbeat",
            "energetic",
            "soulful",
            "rhythmic"
        ],
        "energy": 0.72,
        "valence": 0.8,
        "tempo_bpm": 122,
        "acousticness": 0.25,
        "instrumentalness": 0.0,
        "description": "A vibrant and soulful pop-folk fusion track with upbeat Punjabi rhythms, modern synth textures, and infectious duet vocals.",
        "language": "English",
        "release_year": 2015,
        "popularity": 63,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_134",
        "track_name": "Liggi",
        "artist": "Ritviz",
        "album": "Liggi Single",
        "genre": "Hindi Pop",
        "subgenre": "Electronic Pop",
        "mood_tags": [
            "quirky",
            "upbeat",
            "energetic",
            "playful"
        ],
        "energy": 0.76,
        "valence": 0.88,
        "tempo_bpm": 120,
        "acousticness": 0.18,
        "instrumentalness": 0.05,
        "description": "A quirky, bouncy Hindi electro-pop song with signature vocal chops, cheerful lyrics, and a catchy danceable rhythm.",
        "language": "English",
        "release_year": 2016,
        "popularity": 64,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_135",
        "track_name": "Alag Aasmaan",
        "artist": "Anuv Jain",
        "album": "Alag Aasmaan Single",
        "genre": "Hindi Pop",
        "subgenre": "Acoustic Pop",
        "mood_tags": [
            "romantic",
            "tender",
            "peaceful",
            "dreamy"
        ],
        "energy": 0.28,
        "valence": 0.5,
        "tempo_bpm": 92,
        "acousticness": 0.9,
        "instrumentalness": 0.0,
        "description": "A beautiful and minimal acoustic ballad with gentle ukulele plucking, warm vocals, and a tender, romantic storytelling vibe.",
        "language": "English",
        "release_year": 2017,
        "popularity": 65,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_136",
        "track_name": "Sage",
        "artist": "Ritviz",
        "album": "Dev",
        "genre": "Hindi Pop",
        "subgenre": "Electronic Pop",
        "mood_tags": [
            "warm",
            "joyful",
            "upbeat",
            "romantic"
        ],
        "energy": 0.65,
        "valence": 0.78,
        "tempo_bpm": 110,
        "acousticness": 0.2,
        "instrumentalness": 0.0,
        "description": "A heartwarming electronic pop song with soft synths, uplifting drum patterns, and Ritviz's characteristic melodic singing.",
        "language": "English",
        "release_year": 2018,
        "popularity": 66,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_137",
        "track_name": "Rinkiya Ke Papa",
        "artist": "Manoj Tiwari",
        "album": "Puranki Haveli",
        "genre": "Bhojpuri",
        "subgenre": "Humorous Folk",
        "mood_tags": [
            "playful",
            "upbeat",
            "traditional",
            "joyful"
        ],
        "energy": 0.68,
        "valence": 0.85,
        "tempo_bpm": 118,
        "acousticness": 0.35,
        "instrumentalness": 0.0,
        "description": "A legendary and highly popular humorous Bhojpuri folk song with traditional percussion, rustic harmonium lines, and playful, storytelling vocals.",
        "language": "Bhojpuri",
        "release_year": 2019,
        "popularity": 67,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_138",
        "track_name": "Saj Ke Sawar Ke",
        "artist": "Khesari Lal Yadav, Priyanka Singh",
        "album": "Muqaddar",
        "genre": "Bhojpuri",
        "subgenre": "Dance",
        "mood_tags": [
            "energetic",
            "dance",
            "festive",
            "upbeat"
        ],
        "energy": 0.88,
        "valence": 0.9,
        "tempo_bpm": 132,
        "acousticness": 0.15,
        "instrumentalness": 0.0,
        "description": "A high-tempo, energetic Bhojpuri commercial dance hit featuring pounding electronic beats, dholak layers, and dynamic male-female duet vocals.",
        "language": "Bhojpuri",
        "release_year": 2020,
        "popularity": 68,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_139",
        "track_name": "Lalki Tikuliya",
        "artist": "Khesari Lal Yadav",
        "album": "Lalki Tikuliya Album",
        "genre": "Bhojpuri",
        "subgenre": "Folk Pop",
        "mood_tags": [
            "playful",
            "upbeat",
            "dance",
            "energetic"
        ],
        "energy": 0.82,
        "valence": 0.86,
        "tempo_bpm": 128,
        "acousticness": 0.22,
        "instrumentalness": 0.0,
        "description": "An upbeat and playful Bhojpuri folk-pop song featuring heavy local percussion, shehnai loops, and festive dance rhythms.",
        "language": "Bhojpuri",
        "release_year": 2021,
        "popularity": 69,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_140",
        "track_name": "Arabic Kuthu",
        "artist": "Anirudh Ravichander, Jonita Gandhi",
        "album": "Beast",
        "genre": "Tamil",
        "subgenre": "Kuthu Fusion",
        "mood_tags": [
            "energetic",
            "dance",
            "upbeat",
            "rhythmic"
        ],
        "energy": 0.92,
        "valence": 0.85,
        "tempo_bpm": 128,
        "acousticness": 0.12,
        "instrumentalness": 0.0,
        "description": "A chart-busting Arabic-influenced Tamil Kuthu dance track with infectious trap beats, exotic woodwinds, and energetic vocals.",
        "language": "Tamil",
        "release_year": 2022,
        "popularity": 70,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_141",
        "track_name": "Enjoy Enjaami",
        "artist": "Dhee, Arivu",
        "album": "Enjoy Enjaami Single",
        "genre": "Tamil",
        "subgenre": "Indie Folk Rap",
        "mood_tags": [
            "powerful",
            "rhythmic",
            "celebratory",
            "earthy"
        ],
        "energy": 0.78,
        "valence": 0.72,
        "tempo_bpm": 120,
        "acousticness": 0.3,
        "instrumentalness": 0.0,
        "description": "A groundbreaking independent Tamil track blending indigenous folk rhythms with rap, heavy basslines, and celebratory, nature-loving lyrics.",
        "language": "Tamil",
        "release_year": 2023,
        "popularity": 71,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_142",
        "track_name": "Kutti Story",
        "artist": "Vijay, Anirudh Ravichander",
        "album": "Master",
        "genre": "Tamil",
        "subgenre": "Dance Pop",
        "mood_tags": [
            "upbeat",
            "playful",
            "motivational",
            "cheerful"
        ],
        "energy": 0.74,
        "valence": 0.82,
        "tempo_bpm": 105,
        "acousticness": 0.25,
        "instrumentalness": 0.0,
        "description": "A lighthearted and motivational Tamil pop song featuring actor Vijay's casual vocals, whistle overlays, and a positive, laid-back dance groove.",
        "language": "Tamil",
        "release_year": 2024,
        "popularity": 72,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_143",
        "track_name": "Tagaru Banthu Tagaru",
        "artist": "Anthony Daasan",
        "album": "Tagaru",
        "genre": "Kannada",
        "subgenre": "Folk Rock",
        "mood_tags": [
            "energetic",
            "wild",
            "aggressive",
            "upbeat"
        ],
        "energy": 0.88,
        "valence": 0.75,
        "tempo_bpm": 135,
        "acousticness": 0.2,
        "instrumentalness": 0.0,
        "description": "An intense, high-energy Kannada folk-rock track with aggressive local percussion, electric guitars, and rustic, powerful vocals.",
        "language": "Kannada",
        "release_year": 2025,
        "popularity": 73,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_144",
        "track_name": "Open the Bottle",
        "artist": "Vijay Prakash",
        "album": "Natasaarvabhouma",
        "genre": "Kannada",
        "subgenre": "Party",
        "mood_tags": [
            "upbeat",
            "energetic",
            "dance",
            "playful"
        ],
        "energy": 0.82,
        "valence": 0.8,
        "tempo_bpm": 126,
        "acousticness": 0.15,
        "instrumentalness": 0.0,
        "description": "An upbeat Kannada commercial party anthem with brass lines, synth loops, and a highly energetic performance by Vijay Prakash.",
        "language": "Kannada",
        "release_year": 2010,
        "popularity": 74,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_145",
        "track_name": "Madhura Pisugude",
        "artist": "Sonu Nigam, Shreya Ghoshal",
        "album": "Birugali",
        "genre": "Kannada",
        "subgenre": "Romantic",
        "mood_tags": [
            "romantic",
            "melodic",
            "serene",
            "tender"
        ],
        "energy": 0.42,
        "valence": 0.6,
        "tempo_bpm": 88,
        "acousticness": 0.75,
        "instrumentalness": 0.0,
        "description": "A beautiful, classical-infused Kannada romantic duet with soft acoustic guitar, melodic violin passages, and soulful vocals.",
        "language": "Kannada",
        "release_year": 2011,
        "popularity": 75,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_146",
        "track_name": "Chaleya",
        "artist": "Arijit Singh, Shilpa Rao",
        "album": "Jawan",
        "genre": "Bollywood",
        "subgenre": "Romantic Pop",
        "mood_tags": [
            "romantic",
            "upbeat",
            "danceable",
            "cheerful"
        ],
        "energy": 0.68,
        "valence": 0.75,
        "tempo_bpm": 102,
        "acousticness": 0.25,
        "instrumentalness": 0.0,
        "description": "A breezy, danceable Bollywood romantic pop track featuring smooth electronic beats, acoustic guitars, and sweet, rhythmic vocals.",
        "language": "Hindi",
        "release_year": 2012,
        "popularity": 76,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_147",
        "track_name": "Zinda Banda",
        "artist": "Anirudh Ravichander",
        "album": "Jawan",
        "genre": "Bollywood",
        "subgenre": "Dance",
        "mood_tags": [
            "energetic",
            "powerful",
            "celebratory",
            "uplifting"
        ],
        "energy": 0.92,
        "valence": 0.88,
        "tempo_bpm": 128,
        "acousticness": 0.1,
        "instrumentalness": 0.0,
        "description": "An explosive and grand Bollywood dance anthem featuring roaring dhol beats, heavy synth basslines, horn stabs, and highly energetic vocals.",
        "language": "Hindi",
        "release_year": 2013,
        "popularity": 77,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_148",
        "track_name": "Kabira",
        "artist": "Tochi Raina, Rekha Bhardwaj",
        "album": "Yeh Jawaani Hai Deewani",
        "genre": "Bollywood",
        "subgenre": "Folk-Pop",
        "mood_tags": [
            "bittersweet",
            "emotional",
            "nostalgic",
            "reflective"
        ],
        "energy": 0.55,
        "valence": 0.62,
        "tempo_bpm": 96,
        "acousticness": 0.58,
        "instrumentalness": 0.0,
        "description": "A bittersweet, folk-infused Bollywood track featuring traditional instruments like the sarangi and acoustic guitars, with warm, deeply reflective vocals.",
        "language": "Hindi",
        "release_year": 2014,
        "popularity": 78,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_149",
        "track_name": "Mere Samne Wali Khidki Mein",
        "artist": "Kishore Kumar",
        "album": "Padosan",
        "genre": "Old Classic",
        "subgenre": "Retro Romantic",
        "mood_tags": [
            "playful",
            "joyful",
            "romantic",
            "lighthearted"
        ],
        "energy": 0.48,
        "valence": 0.8,
        "tempo_bpm": 110,
        "acousticness": 0.65,
        "instrumentalness": 0.0,
        "description": "A playful and classic 60s Hindi romantic song with light acoustic strumming, comedic timing, and Kishore's joyful, animated vocals.",
        "language": "Hindi",
        "release_year": 2015,
        "popularity": 79,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_150",
        "track_name": "Yeh Dosti Hum Nahin Todenge",
        "artist": "Kishore Kumar, Manna Dey",
        "album": "Sholay",
        "genre": "Old Classic",
        "subgenre": "Retro Friendship",
        "mood_tags": [
            "warm",
            "nostalgic",
            "energetic",
            "emotional"
        ],
        "energy": 0.6,
        "valence": 0.75,
        "tempo_bpm": 108,
        "acousticness": 0.55,
        "instrumentalness": 0.0,
        "description": "A legendary, warm 70s Hindi friendship anthem featuring acoustic guitar, energetic clapping rhythms, and a nostalgic, emotional duet performance.",
        "language": "Hindi",
        "release_year": 2016,
        "popularity": 80,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_151",
        "track_name": "Gulabi Aankhen",
        "artist": "Mohammed Rafi",
        "album": "The Train",
        "genre": "Old Classic",
        "subgenre": "Retro Dance",
        "mood_tags": [
            "upbeat",
            "romantic",
            "groovy",
            "energetic",
            "retro"
        ],
        "energy": 0.72,
        "valence": 0.85,
        "tempo_bpm": 120,
        "acousticness": 0.45,
        "instrumentalness": 0.0,
        "description": "An iconic, groovy 70s Hindi romantic dance track featuring brass horns, upbeat acoustic guitars, and Rafi's charismatic, soaring vocals.",
        "language": "Hindi",
        "release_year": 2017,
        "popularity": 81,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_152",
        "track_name": "Chaudhary",
        "artist": "Amit Trivedi, Mame Khan",
        "album": "Coke Studio India",
        "genre": "Folk",
        "subgenre": "Rajasthani Folk Fusion",
        "mood_tags": [
            "joyful",
            "celebratory",
            "soulful",
            "warm",
            "folk"
        ],
        "energy": 0.65,
        "valence": 0.75,
        "tempo_bpm": 115,
        "acousticness": 0.45,
        "instrumentalness": 0.0,
        "description": "A traditional folk song and Rajasthani folk fusion track blending traditional vocals and sarangi with modern acoustic guitar, drum grooves, and a celebratory feel.",
        "language": "English",
        "release_year": 2018,
        "popularity": 82,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_153",
        "track_name": "Jugni",
        "artist": "Gurdas Maan",
        "album": "Jugni Single",
        "genre": "Folk",
        "subgenre": "Punjabi Folk",
        "mood_tags": [
            "energetic",
            "upbeat",
            "traditional",
            "spiritual",
            "folk"
        ],
        "energy": 0.75,
        "valence": 0.8,
        "tempo_bpm": 125,
        "acousticness": 0.3,
        "instrumentalness": 0.0,
        "description": "A traditional Punjabi folk song with traditional dhol drums, tumbi notes, and powerful, spiritually resonant traditional folk vocals.",
        "language": "English",
        "release_year": 2019,
        "popularity": 83,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_154",
        "track_name": "Monta Re",
        "artist": "Swanand Kirkire, Amitabh Bhattacharya",
        "album": "Lootera",
        "genre": "Folk",
        "subgenre": "Bengali Folk Fusion",
        "mood_tags": [
            "romantic",
            "warm",
            "serene",
            "tender",
            "folk"
        ],
        "energy": 0.38,
        "valence": 0.58,
        "tempo_bpm": 95,
        "acousticness": 0.68,
        "instrumentalness": 0.0,
        "description": "A traditional Bengali folk-fusion love ballad with soft traditional dotara strings, acoustic guitar backing, and tender romantic folk vocals.",
        "language": "English",
        "release_year": 2020,
        "popularity": 84,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_155",
        "track_name": "Chhaap Tilak",
        "artist": "Abida Parveen, Rahat Fateh Ali Khan",
        "album": "Coke Studio Season 7",
        "genre": "Folk",
        "subgenre": "Sufi Folk",
        "mood_tags": [
            "spiritual",
            "emotional",
            "intense",
            "peaceful",
            "folk"
        ],
        "energy": 0.52,
        "valence": 0.65,
        "tempo_bpm": 100,
        "acousticness": 0.6,
        "instrumentalness": 0.0,
        "description": "A traditional Sufi folk song classic featuring traditional harmonium, traditional handclapping, and deeply emotional, intense folk vocals.",
        "language": "English",
        "release_year": 2021,
        "popularity": 85,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_156",
        "track_name": "Kesariya Balam",
        "artist": "Ila Arun",
        "album": "Rajasthani Folk Classics",
        "genre": "Folk",
        "subgenre": "Rajasthani Traditional Folk",
        "mood_tags": [
            "nostalgic",
            "warm",
            "cultural",
            "folk"
        ],
        "energy": 0.45,
        "valence": 0.5,
        "tempo_bpm": 90,
        "acousticness": 0.7,
        "instrumentalness": 0.0,
        "description": "A traditional Rajasthani folk song welcoming visitors with traditional instrumentation, dholak beats, and cultural folk resonance.",
        "language": "English",
        "release_year": 2022,
        "popularity": 86,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_157",
        "track_name": "Tum Se Hi",
        "artist": "Mohit Chauhan",
        "album": "Jab We Met",
        "genre": "Bollywood",
        "subgenre": "Romantic",
        "mood_tags": [
            "romantic",
            "cheerful",
            "breezy",
            "hopeful"
        ],
        "energy": 0.55,
        "valence": 0.72,
        "tempo_bpm": 110,
        "acousticness": 0.48,
        "instrumentalness": 0.0,
        "description": "A breezy, cheerful Bollywood romantic pop track featuring acoustic guitars, light drums, and hopeful, uplifting vocals.",
        "language": "Hindi",
        "release_year": 2023,
        "popularity": 87,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_158",
        "track_name": "Mast Magan",
        "artist": "Arijit Singh, Chinmayi Sripada",
        "album": "2 States",
        "genre": "Bollywood",
        "subgenre": "Romantic",
        "mood_tags": [
            "romantic",
            "soulful",
            "warm",
            "serene"
        ],
        "energy": 0.48,
        "valence": 0.58,
        "tempo_bpm": 92,
        "acousticness": 0.55,
        "instrumentalness": 0.0,
        "description": "A warm, soulful Bollywood romantic track featuring soft sitar interludes, acoustic guitar, and emotive vocals.",
        "language": "Hindi",
        "release_year": 2024,
        "popularity": 88,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_159",
        "track_name": "Ghungroo",
        "artist": "Arijit Singh, Shilpa Rao",
        "album": "War",
        "genre": "Bollywood",
        "subgenre": "Dance",
        "mood_tags": [
            "upbeat",
            "energetic",
            "groovy",
            "dance"
        ],
        "energy": 0.85,
        "valence": 0.8,
        "tempo_bpm": 118,
        "acousticness": 0.1,
        "instrumentalness": 0.0,
        "description": "An upbeat, groovy Bollywood dance pop song with bright brass hooks, clean funk guitar strumming, and energetic duet vocals.",
        "language": "Hindi",
        "release_year": 2025,
        "popularity": 89,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_160",
        "track_name": "Kabhie Kabhie Mere Dil Mein",
        "artist": "Mukesh",
        "album": "Kabhie Kabhie",
        "genre": "Old Classic",
        "subgenre": "Retro Romantic",
        "mood_tags": [
            "romantic",
            "poetic",
            "nostalgic",
            "melancholic",
            "retro"
        ],
        "energy": 0.25,
        "valence": 0.35,
        "tempo_bpm": 80,
        "acousticness": 0.8,
        "instrumentalness": 0.0,
        "description": "A timeless, poetic Hindi retro classic with warm orchestral strings, clean acoustic backing, and Mukesh's iconic emotional voice.",
        "language": "Hindi",
        "release_year": 1992,
        "popularity": 90,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_161",
        "track_name": "Roop Tera Mastana",
        "artist": "Kishore Kumar",
        "album": "Aradhana",
        "genre": "Old Classic",
        "subgenre": "Retro Romantic",
        "mood_tags": [
            "playful",
            "romantic",
            "groovy",
            "energetic",
            "retro"
        ],
        "energy": 0.65,
        "valence": 0.72,
        "tempo_bpm": 105,
        "acousticness": 0.4,
        "instrumentalness": 0.0,
        "description": "A groovy, playful retro romantic track featuring a prominent keyboard organ riff, upbeat bongos, and Kishore's energetic performance.",
        "language": "Hindi",
        "release_year": 1992,
        "popularity": 91,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_162",
        "track_name": "Chura Liya Hai Tumne Jo Dil Ko",
        "artist": "Asha Bhosle, Mohammed Rafi",
        "album": "Yaadon Ki Baaraat",
        "genre": "Old Classic",
        "subgenre": "Retro Romantic",
        "mood_tags": [
            "romantic",
            "tender",
            "nostalgic",
            "acoustic",
            "retro"
        ],
        "energy": 0.38,
        "valence": 0.65,
        "tempo_bpm": 88,
        "acousticness": 0.75,
        "instrumentalness": 0.0,
        "description": "A tender, acoustic-led Hindi retro romantic classic featuring the iconic glass clink opening, soft acoustic guitar, and beautiful duet harmonies.",
        "language": "Hindi",
        "release_year": 1992,
        "popularity": 92,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_170",
        "track_name": "Apsara Aali",
        "artist": "Ajay-Atul",
        "album": "Natarang",
        "genre": "Marathi",
        "subgenre": "Lavani",
        "mood_tags": [
            "energetic",
            "dance",
            "festive",
            "traditional"
        ],
        "energy": 0.85,
        "valence": 0.9,
        "tempo_bpm": 130,
        "acousticness": 0.3,
        "instrumentalness": 0.05,
        "description": "A high-energy, traditional Marathi Lavani dance song featuring dynamic dholki beats, vibrant orchestral arrangements, and soaring vocals.",
        "language": "Marathi",
        "release_year": 2010,
        "popularity": 45,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_171",
        "track_name": "Sairat Zaala Ji",
        "artist": "Ajay-Atul",
        "album": "Sairat",
        "genre": "Marathi",
        "subgenre": "Romantic",
        "mood_tags": [
            "romantic",
            "melodic",
            "orchestral",
            "soulful"
        ],
        "energy": 0.5,
        "valence": 0.55,
        "tempo_bpm": 95,
        "acousticness": 0.45,
        "instrumentalness": 0.0,
        "description": "A grand, sweepingly romantic Marathi love song backed by a full live symphony orchestra, acoustic guitars, and sweet, soulful vocals.",
        "language": "Marathi",
        "release_year": 2016,
        "popularity": 46,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_172",
        "track_name": "Zingaat",
        "artist": "Ajay-Atul",
        "album": "Sairat",
        "genre": "Marathi",
        "subgenre": "Dance",
        "mood_tags": [
            "high-energy",
            "dance",
            "celebratory",
            "wild"
        ],
        "energy": 0.95,
        "valence": 0.95,
        "tempo_bpm": 140,
        "acousticness": 0.15,
        "instrumentalness": 0.0,
        "description": "A wildly energetic, fast-tempo Marathi dance anthem with driving synth beats, thunderous traditional dhol beats, and raw, high-pitch vocals.",
        "language": "Marathi",
        "release_year": 2016,
        "popularity": 47,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_173",
        "track_name": "Kesariya",
        "artist": "Arijit Singh",
        "album": "Brahmastra",
        "genre": "Hindi",
        "subgenre": "Romantic Pop",
        "mood_tags": [
            "romantic",
            "melodious",
            "warm",
            "hopeful"
        ],
        "energy": 0.6,
        "valence": 0.65,
        "tempo_bpm": 98,
        "acousticness": 0.4,
        "instrumentalness": 0.0,
        "description": "A warm and melodious Hindi romantic pop ballad featuring acoustic guitar strumming, soaring synth hooks, and Arijit Singh's sweet vocals.",
        "language": "English",
        "release_year": 2022,
        "popularity": 48,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_174",
        "track_name": "Tum Hi Ho",
        "artist": "Arijit Singh",
        "album": "Aashiqui 2",
        "genre": "Hindi",
        "subgenre": "Sad Romantic",
        "mood_tags": [
            "melancholic",
            "intense",
            "romantic",
            "sad"
        ],
        "energy": 0.4,
        "valence": 0.3,
        "tempo_bpm": 90,
        "acousticness": 0.7,
        "instrumentalness": 0.0,
        "description": "A deeply melancholic and intense Hindi romantic ballad featuring soft piano chords, heavy orchestration, and emotional, powerful vocals.",
        "language": "English",
        "release_year": 2013,
        "popularity": 49,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_175",
        "track_name": "Brown Munde",
        "artist": "AP Dhillon, Gurinder Gill",
        "album": "Brown Munde",
        "genre": "Punjabi",
        "subgenre": "Hip-Hop",
        "mood_tags": [
            "groovy",
            "cool",
            "energetic",
            "relaxed"
        ],
        "energy": 0.75,
        "valence": 0.8,
        "tempo_bpm": 85,
        "acousticness": 0.1,
        "instrumentalness": 0.0,
        "description": "A cool, laid-back Punjabi Hip-Hop/Trap track with a heavy sub-bass line, minimalist synths, and smooth, infectious flow.",
        "language": "Punjabi",
        "release_year": 2020,
        "popularity": 50,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_176",
        "track_name": "Arabic Kuthu",
        "artist": "Anirudh Ravichander, Jonita Gandhi",
        "album": "Beast",
        "genre": "Tamil",
        "subgenre": "Dance Fusion",
        "mood_tags": [
            "high-energy",
            "dance",
            "catchy",
            "groovy"
        ],
        "energy": 0.9,
        "valence": 0.85,
        "tempo_bpm": 128,
        "acousticness": 0.2,
        "instrumentalness": 0.01,
        "description": "A high-energy Tamil dance track fusing Arabic rhythms with local Kuthu folk percussion, filled with catchy hook lines and energetic vocals.",
        "language": "Tamil",
        "release_year": 2022,
        "popularity": 51,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_177",
        "track_name": "Munbe Vaa",
        "artist": "Shreya Ghoshal, Naresh Iyer",
        "album": "Sillunu Oru Kaadhal",
        "genre": "Tamil",
        "subgenre": "Classical Romantic",
        "mood_tags": [
            "soulful",
            "romantic",
            "dreamy",
            "melodic"
        ],
        "energy": 0.45,
        "valence": 0.5,
        "tempo_bpm": 92,
        "acousticness": 0.6,
        "instrumentalness": 0.0,
        "description": "A soulful, classically-infused Tamil romantic song composed by A.R. Rahman, featuring flute interludes, mridangam percussion, and dreamy vocals.",
        "language": "Tamil",
        "release_year": 2006,
        "popularity": 52,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_178",
        "track_name": "Naatu Naatu",
        "artist": "Rahul Sipligunj, Kaala Bhairava",
        "album": "RRR",
        "genre": "Telugu",
        "subgenre": "Folk Dance",
        "mood_tags": [
            "electrifying",
            "wild",
            "dance",
            "energetic"
        ],
        "energy": 0.98,
        "valence": 0.9,
        "tempo_bpm": 145,
        "acousticness": 0.1,
        "instrumentalness": 0.0,
        "description": "An electrifying and fast-paced Telugu folk dance anthem featuring rapid dhol beats, brass horn accents, and high-octane vocals.",
        "language": "Telugu",
        "release_year": 2022,
        "popularity": 53,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_179",
        "track_name": "Samajavaragamana",
        "artist": "Sid Sriram",
        "album": "Ala Vaikunthapurramuloo",
        "genre": "Telugu",
        "subgenre": "Romantic Pop",
        "mood_tags": [
            "melodious",
            "breezy",
            "romantic",
            "happy"
        ],
        "energy": 0.65,
        "valence": 0.7,
        "tempo_bpm": 105,
        "acousticness": 0.35,
        "instrumentalness": 0.0,
        "description": "A melodious and breezy Telugu romantic track featuring clean acoustic guitars, light drums, and Sid Sriram's signature expressive vocals.",
        "language": "Telugu",
        "release_year": 2019,
        "popularity": 54,
        "activities": [
            "Coding",
            "Cooking",
            "Driving"
        ]
    },
    {
        "id": "track_180",
        "track_name": "Boba Tunnel",
        "artist": "Anupam Roy",
        "album": "Chotushkone",
        "genre": "Bengali",
        "subgenre": "Acoustic Indie",
        "mood_tags": [
            "melancholic",
            "quiet",
            "reflective",
            "minimalist"
        ],
        "energy": 0.3,
        "valence": 0.4,
        "tempo_bpm": 85,
        "acousticness": 0.8,
        "instrumentalness": 0.0,
        "description": "A quiet, melancholic Bengali acoustic song with soft classical guitar chords, minimal backing, and warm, introspective vocals.",
        "language": "Bengali",
        "release_year": 2014,
        "popularity": 55,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_181",
        "track_name": "Malare",
        "artist": "Vijay Yesudas",
        "album": "Premam",
        "genre": "Malayalam",
        "subgenre": "Acoustic Romantic",
        "mood_tags": [
            "romantic",
            "dreamy",
            "sweet",
            "soothing"
        ],
        "energy": 0.35,
        "valence": 0.45,
        "tempo_bpm": 80,
        "acousticness": 0.75,
        "instrumentalness": 0.0,
        "description": "A sweet, soothing Malayalam romantic acoustic ballad featuring delicate violin arrangements, acoustic guitar, and warm, gentle vocals.",
        "language": "Malayalam",
        "release_year": 2015,
        "popularity": 56,
        "activities": [
            "Meditation",
            "Reading",
            "Sleep"
        ]
    },
    {
        "id": "track_182",
        "track_name": "Singara Siriye",
        "artist": "Vijay Prakash, Ananya Bhat",
        "album": "Kantara",
        "genre": "Kannada",
        "subgenre": "Folk Fusion",
        "mood_tags": [
            "traditional",
            "melodic",
            "romantic",
            "energetic"
        ],
        "energy": 0.75,
        "valence": 0.65,
        "tempo_bpm": 115,
        "acousticness": 0.4,
        "instrumentalness": 0.02,
        "description": "A Kannada folk fusion track combining traditional instruments with modern beats, featuring robust traditional singing and melodic hooks.",
        "language": "Kannada",
        "release_year": 2022,
        "popularity": 57,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_183",
        "track_name": "Radha Ne Shyam Malishe",
        "artist": "Sachin-Jigar",
        "album": "Love Ni Bhavai",
        "genre": "Gujarati",
        "subgenre": "Festive Garba",
        "mood_tags": [
            "festive",
            "dance",
            "joyful",
            "traditional"
        ],
        "energy": 0.8,
        "valence": 0.75,
        "tempo_bpm": 120,
        "acousticness": 0.25,
        "instrumentalness": 0.0,
        "description": "A festive, joyful Gujarati Garba song with traditional rhythms, modern synth pads, and melodic traditional duet vocals.",
        "language": "Gujarati",
        "release_year": 2017,
        "popularity": 58,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_184",
        "track_name": "Lolipop Lagelu",
        "artist": "Pawan Singh",
        "album": "Lolipop Lagelu",
        "genre": "Bhojpuri",
        "subgenre": "Folk Pop",
        "mood_tags": [
            "party",
            "dance",
            "high-energy",
            "rowdy"
        ],
        "energy": 0.9,
        "valence": 0.85,
        "tempo_bpm": 135,
        "acousticness": 0.15,
        "instrumentalness": 0.0,
        "description": "A high-energy Bhojpuri dance track with electronic beats, driving folk percussion, and Pawan Singh's famous party-starting vocals.",
        "language": "Bhojpuri",
        "release_year": 2008,
        "popularity": 59,
        "activities": [
            "Gym",
            "Party",
            "Running"
        ]
    },
    {
        "id": "track_190",
        "track_name": "Dynamite",
        "artist": "BTS",
        "album": "Be",
        "genre": "Pop",
        "subgenre": "K-Pop",
        "mood_tags": [
            "happy",
            "energetic",
            "party",
            "cheerful"
        ],
        "energy": 0.85,
        "valence": 0.9,
        "tempo_bpm": 114,
        "acousticness": 0.05,
        "instrumentalness": 0.0,
        "language": "Korean",
        "popularity": 95,
        "release_year": 2020,
        "activities": [
            "Workout",
            "Running",
            "Party"
        ],
        "description": "An upbeat, energetic K-Pop disco-pop song with highly infectious hooks, retro brass, and cheerful, celebratory vocals."
    },
    {
        "id": "track_191",
        "track_name": "Stay With Me",
        "artist": "Miki Matsubara",
        "album": "Pocket Park",
        "genre": "J-Pop",
        "subgenre": "City Pop",
        "mood_tags": [
            "romantic",
            "nostalgic",
            "chill",
            "happy"
        ],
        "energy": 0.68,
        "valence": 0.75,
        "tempo_bpm": 108,
        "acousticness": 0.25,
        "instrumentalness": 0.0,
        "language": "Japanese",
        "popularity": 88,
        "release_year": 1979,
        "activities": [
            "Driving",
            "Cooking",
            "Family Time"
        ],
        "description": "A classic J-Pop City Pop anthem with smooth brass, groovy bassline, retro keyboards, and sweet, soulful vocals."
    },
    {
        "id": "track_192",
        "track_name": "Love Confession",
        "artist": "Jay Chou",
        "album": "Jay Chou's Bedtime Stories",
        "genre": "C-Pop",
        "subgenre": "Mandopop",
        "mood_tags": [
            "romantic",
            "sweet",
            "happy",
            "chill"
        ],
        "energy": 0.55,
        "valence": 0.68,
        "tempo_bpm": 92,
        "acousticness": 0.45,
        "instrumentalness": 0.0,
        "language": "Chinese",
        "popularity": 85,
        "release_year": 2016,
        "activities": [
            "Driving",
            "Reading",
            "Family Time"
        ],
        "description": "A sweet, breezy Mandopop acoustic R&B/pop song with acoustic guitars, light hip-hop beats, and romantic vocals."
    },
    {
        "id": "track_193",
        "track_name": "Raga Bhairavi",
        "artist": "Pandit Hariprasad Chaurasia",
        "album": "Morning Ragas",
        "genre": "Hindustani Classical",
        "subgenre": "Flute Solo",
        "mood_tags": [
            "calm",
            "meditation",
            "relaxing",
            "peaceful"
        ],
        "energy": 0.2,
        "valence": 0.5,
        "tempo_bpm": 70,
        "acousticness": 0.95,
        "instrumentalness": 0.98,
        "language": "Instrumental",
        "popularity": 65,
        "release_year": 1995,
        "activities": [
            "Yoga",
            "Meditation",
            "Reading"
        ],
        "description": "A deeply peaceful Hindustani classical flute recital (Bansuri) playing Raga Bhairavi. Perfect for morning meditation."
    },
    {
        "id": "track_194",
        "track_name": "Vatapi Ganapatim",
        "artist": "M.S. Subbulakshmi",
        "album": "Great Carnatic Vocals",
        "genre": "Carnatic Classical",
        "subgenre": "Kriti",
        "mood_tags": [
            "devotional",
            "calm",
            "soothing",
            "traditional"
        ],
        "energy": 0.25,
        "valence": 0.6,
        "tempo_bpm": 80,
        "acousticness": 0.9,
        "instrumentalness": 0.0,
        "language": "Sanskrit",
        "popularity": 70,
        "release_year": 1985,
        "activities": [
            "Yoga",
            "Family Time",
            "Meditation"
        ],
        "description": "A traditional Carnatic classical kriti sung in Sanskrit, dedicated to Lord Ganesha, featuring the legendary, pure voice of M.S. Subbulakshmi."
    },
    {
        "id": "track_195",
        "track_name": "Tum Itna Jo Muskuraye Ho",
        "artist": "Jagjit Singh",
        "album": "Arth",
        "genre": "Ghazal",
        "subgenre": "Acoustic Ghazal",
        "mood_tags": [
            "sad",
            "romantic",
            "reflective",
            "chill"
        ],
        "energy": 0.3,
        "valence": 0.45,
        "tempo_bpm": 78,
        "acousticness": 0.8,
        "instrumentalness": 0.0,
        "language": "Hindi",
        "popularity": 80,
        "release_year": 1982,
        "activities": [
            "Reading",
            "Studying",
            "Family Time"
        ],
        "description": "A poetic, emotional Hindi Ghazal lead by acoustic guitar, subtle violin, and Jagjit Singh's soothing, resonant baritone voice."
    },
    {
        "id": "track_196",
        "track_name": "Bhar Do Jholi Meri",
        "artist": "Sabri Brothers",
        "album": "Qawwali Hits",
        "genre": "Qawwali",
        "subgenre": "Traditional Qawwali",
        "mood_tags": [
            "devotional",
            "energetic",
            "motivational",
            "spirit"
        ],
        "energy": 0.7,
        "valence": 0.75,
        "tempo_bpm": 120,
        "acousticness": 0.6,
        "instrumentalness": 0.0,
        "language": "Urdu",
        "popularity": 75,
        "release_year": 1975,
        "activities": [
            "Family Time",
            "Driving",
            "Cooking"
        ],
        "description": "A traditional, high-energy Sufi Qawwali with rhythmic hand clapping, harmonium, dholak beats, and powerful chorus singing."
    },
    {
        "id": "track_197",
        "track_name": "Kun Faya Kun",
        "artist": "A.R. Rahman, Javed Ali, Mohit Chauhan",
        "album": "Rockstar",
        "genre": "Sufi",
        "subgenre": "Sufi Pop",
        "mood_tags": [
            "calm",
            "devotional",
            "peaceful",
            "soulful"
        ],
        "energy": 0.45,
        "valence": 0.5,
        "tempo_bpm": 96,
        "acousticness": 0.7,
        "instrumentalness": 0.0,
        "language": "Hindi",
        "popularity": 92,
        "release_year": 2011,
        "activities": [
            "Coding",
            "Studying",
            "Meditation"
        ],
        "description": "A legendary Sufi pop track composed by A.R. Rahman, blending acoustic guitars, harmonium, and soulful devotional vocals."
    },
    {
        "id": "track_198",
        "track_name": "Achyutam Keshavam",
        "artist": "Vikram Hazra",
        "album": "Krishna Bhajans",
        "genre": "Bhajan",
        "subgenre": "Kirtan",
        "mood_tags": [
            "calm",
            "meditation",
            "soothing",
            "devotional"
        ],
        "energy": 0.3,
        "valence": 0.6,
        "tempo_bpm": 85,
        "acousticness": 0.85,
        "instrumentalness": 0.0,
        "language": "Sanskrit",
        "popularity": 78,
        "release_year": 2015,
        "activities": [
            "Yoga",
            "Meditation",
            "Family Time"
        ],
        "description": "A soothing, modern acoustic Bhajan dedicated to Lord Krishna, with gentle guitars, bansuri flute, and meditative vocals."
    },
    {
        "id": "track_199",
        "track_name": "Raghupati Raghav Raja Ram",
        "artist": "Hari Om Sharan",
        "album": "Bhajan Sandhya",
        "genre": "Devotional",
        "subgenre": "Aarti",
        "mood_tags": [
            "calm",
            "morning",
            "soothing",
            "peaceful"
        ],
        "energy": 0.28,
        "valence": 0.55,
        "tempo_bpm": 80,
        "acousticness": 0.9,
        "instrumentalness": 0.0,
        "language": "Hindi",
        "popularity": 72,
        "release_year": 1980,
        "activities": [
            "Yoga",
            "Family Time",
            "Morning"
        ],
        "description": "A peaceful, traditional Hindu devotional prayer with clean harmonium backing and warm, soothing morning vocals."
    },
    {
        "id": "track_200",
        "track_name": "Bihu Re Bihu",
        "artist": "Bhupen Hazarika",
        "album": "Assamese Folk Collection",
        "genre": "Assamese",
        "subgenre": "Bihu",
        "mood_tags": [
            "happy",
            "energetic",
            "festive",
            "traditional"
        ],
        "energy": 0.78,
        "valence": 0.85,
        "tempo_bpm": 125,
        "acousticness": 0.4,
        "instrumentalness": 0.0,
        "language": "Assamese",
        "popularity": 68,
        "release_year": 1988,
        "activities": [
            "Party",
            "Driving",
            "Cooking"
        ],
        "description": "A festive and traditional Assamese Bihu dance song featuring energetic local percussion (dhol, pepa) and Bhupen Hazarika's iconic voice."
    },
    {
        "id": "track_201",
        "track_name": "Rangabati",
        "artist": "Jitendra Haripal, Krishna Patel",
        "album": "Sambalpuri Folk",
        "genre": "Odia",
        "subgenre": "Sambalpuri",
        "mood_tags": [
            "happy",
            "party",
            "catchy",
            "dance"
        ],
        "energy": 0.82,
        "valence": 0.9,
        "tempo_bpm": 130,
        "acousticness": 0.35,
        "instrumentalness": 0.0,
        "language": "Odia",
        "popularity": 70,
        "release_year": 1979,
        "activities": [
            "Party",
            "Workout",
            "Driving"
        ],
        "description": "A highly popular and catchy Sambalpuri folk song in Odia with energetic rhythms, traditional flute hooks, and celebratory duet vocals."
    },
    {
        "id": "track_202",
        "track_name": "Solid Body",
        "artist": "Raju Punjabi, Sheenam Katholic",
        "album": "Haryanvi Hits",
        "genre": "Haryanvi",
        "subgenre": "Haryanvi Pop",
        "mood_tags": [
            "energetic",
            "dance",
            "workout",
            "happy"
        ],
        "energy": 0.92,
        "valence": 0.85,
        "tempo_bpm": 138,
        "acousticness": 0.1,
        "instrumentalness": 0.0,
        "language": "Haryanvi",
        "popularity": 75,
        "release_year": 2015,
        "activities": [
            "Workout",
            "Gym",
            "Party"
        ],
        "description": "A high-octane Haryanvi dance pop track featuring heavy synth basslines, rapid electronic beats, and energetic Haryanvi pop vocals."
    },
    {
        "id": "track_203",
        "track_name": "Kesariya Balam",
        "artist": "Allah Jilai Bai",
        "album": "Maand Folk",
        "genre": "Rajasthani",
        "subgenre": "Maand",
        "mood_tags": [
            "calm",
            "reflective",
            "warm",
            "traditional"
        ],
        "energy": 0.25,
        "valence": 0.5,
        "tempo_bpm": 75,
        "acousticness": 0.92,
        "instrumentalness": 0.0,
        "language": "Rajasthani",
        "popularity": 74,
        "release_year": 1973,
        "activities": [
            "Yoga",
            "Meditation",
            "Reading"
        ],
        "description": "A timeless Rajasthani folk classic welcoming travelers, sung in the traditional Maand style with soft dholak and sarangi accents."
    },
    {
        "id": "track_204",
        "track_name": "Maria Pitache",
        "artist": "Remo Fernandes",
        "album": "Goan Pop",
        "genre": "Konkani",
        "subgenre": "Konkani Pop",
        "mood_tags": [
            "happy",
            "party",
            "groovy",
            "carefree"
        ],
        "energy": 0.8,
        "valence": 0.88,
        "tempo_bpm": 122,
        "acousticness": 0.2,
        "instrumentalness": 0.0,
        "language": "Konkani",
        "popularity": 66,
        "release_year": 1984,
        "activities": [
            "Party",
            "Driving",
            "Cooking"
        ],
        "description": "A carefree, groovy Goan-Konkani pop song featuring lively acoustic guitars, brass trumpets, and a fun, beachside party mood."
    },
    {
        "id": "track_205",
        "track_name": "Sufiyana Kalam",
        "artist": "Traditional Kashmiri Artists",
        "album": "Kashmiri Sufi Music",
        "genre": "Kashmiri",
        "subgenre": "Sufiyana Kalam",
        "mood_tags": [
            "calm",
            "mystical",
            "peaceful",
            "devotional"
        ],
        "energy": 0.22,
        "valence": 0.48,
        "tempo_bpm": 80,
        "acousticness": 0.94,
        "instrumentalness": 0.05,
        "language": "Kashmiri",
        "popularity": 62,
        "release_year": 1990,
        "activities": [
            "Meditation",
            "Yoga",
            "Reading"
        ],
        "description": "A mystical and peaceful Kashmiri Sufiyana Kalam performance featuring traditional instruments like santoor and rabab with devotional singing."
    },
    {
        "id": "track_206",
        "track_name": "Dogri Pahadi Lok Geet",
        "artist": "Traditional Dogri Artists",
        "album": "Dogra Culture",
        "genre": "Dogri",
        "subgenre": "Dogri Pahadi",
        "mood_tags": [
            "calm",
            "relaxing",
            "peaceful",
            "rural"
        ],
        "energy": 0.3,
        "valence": 0.6,
        "tempo_bpm": 88,
        "acousticness": 0.9,
        "instrumentalness": 0.0,
        "language": "Dogri",
        "popularity": 58,
        "release_year": 1998,
        "activities": [
            "Reading",
            "Family Time",
            "Relaxing"
        ],
        "description": "A peaceful and sweet Dogra folk hill ballad highlighting local cultural instruments and traditional pahadi vocal styling."
    },
    {
        "id": "track_207",
        "track_name": "Amazing Grace",
        "artist": "Aretha Franklin",
        "album": "Amazing Grace Live",
        "genre": "Gospel",
        "subgenre": "Traditional Gospel",
        "mood_tags": [
            "devotional",
            "soulful",
            "emotional",
            "motivational"
        ],
        "energy": 0.4,
        "valence": 0.35,
        "tempo_bpm": 76,
        "acousticness": 0.7,
        "instrumentalness": 0.0,
        "language": "English",
        "popularity": 82,
        "release_year": 1972,
        "activities": [
            "Morning",
            "Family Time",
            "Meditation"
        ],
        "description": "A deeply moving and soulful live Gospel rendition of Amazing Grace featuring Aretha Franklin's powerhouse vocals and a live church choir."
    },
    {
        "id": "track_208",
        "track_name": "Nessun Dorma",
        "artist": "Luciano Pavarotti",
        "album": "Opera Gala",
        "genre": "Opera",
        "subgenre": "Aria",
        "mood_tags": [
            "emotional",
            "energetic",
            "motivational",
            "intense"
        ],
        "energy": 0.58,
        "valence": 0.28,
        "tempo_bpm": 84,
        "acousticness": 0.85,
        "instrumentalness": 0.05,
        "language": "Italian",
        "popularity": 84,
        "release_year": 1990,
        "activities": [
            "Focus",
            "Coding",
            "Reading"
        ],
        "description": "A dramatic and intense classical operatic aria composed by Puccini, featuring Pavarotti's unmatched, soaring tenor vocals."
    },
    {
        "id": "track_209",
        "track_name": "Baby Shark",
        "artist": "Pinkfong",
        "album": "Baby Shark Sing-Alongs",
        "genre": "Children's Music",
        "subgenre": "Sing-Along",
        "mood_tags": [
            "happy",
            "cheerful",
            "catchy",
            "carefree"
        ],
        "energy": 0.88,
        "valence": 0.95,
        "tempo_bpm": 120,
        "acousticness": 0.15,
        "instrumentalness": 0.01,
        "language": "English",
        "popularity": 94,
        "release_year": 2016,
        "activities": [
            "Family Time",
            "Cleaning",
            "Cooking"
        ],
        "description": "A happy, hyper-catchy children's sing-along song about a shark family, with bright electronic beats and simple, repetitive lyrics."
    }
]


def seed_chroma():
    """Populate ChromaDB with the curated track catalog."""
    print(f"Initializing ChromaDB at: {CHROMA_DB_PATH}")
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Delete and recreate for idempotency
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Spotify track metadata for semantic music discovery"},
    )

    # Prepare batch data
    ids = []
    documents = []
    metadatas = []

    for track in TRACK_CATALOG:
        ids.append(track["id"])

        # The document is a rich text combining description + tags for better embedding
        doc = (
            f"{track['description']} "
            f"Genre: {track['genre']}, {track['subgenre']}. "
            f"Language: {track.get('language', 'English')}. "
            f"Mood: {', '.join(track['mood_tags'])}. "
            f"Activity: {', '.join(track.get('activities', []))}. "
            f"Artist: {track['artist']}. Track: {track['track_name']}."
        )
        documents.append(doc)

        metadatas.append({
            "track_name": track["track_name"],
            "artist": track["artist"],
            "album": track["album"],
            "genre": track["genre"],
            "subgenre": track["subgenre"],
            "mood_tags": json.dumps(track["mood_tags"]),
            "activities": json.dumps(track.get("activities", [])),
            "language": track.get("language", "English"),
            "popularity": track.get("popularity", 50),
            "release_year": track.get("release_year", 2020),
            "decade": f"{str(track.get('release_year', 2020))[:3]}0s",
            "energy": track["energy"],
            "valence": track["valence"],
            "tempo_bpm": track["tempo_bpm"],
            "acousticness": track["acousticness"],
            "instrumentalness": track["instrumentalness"],
            "description": track["description"],
        })

    # Upsert into collection
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    print(f"Successfully seeded {len(ids)} tracks into ChromaDB collection '{COLLECTION_NAME}'")
    print(f"Genres covered: {sorted(list(set(t['genre'] for t in TRACK_CATALOG)))}")
    print(f"Artists: {len(set(t['artist'] for t in TRACK_CATALOG))} unique")

    # Quick verification
    result = collection.query(query_texts=["upbeat synthwave for driving at night"], n_results=3)
    print("\nVerification query: 'upbeat synthwave for driving at night'")
    for i, (doc_id, meta) in enumerate(zip(result["ids"][0], result["metadatas"][0])):
        print(f"  {i+1}. {meta['track_name']} by {meta['artist']} ({meta['genre']})")

    return collection


if __name__ == "__main__":
    seed_chroma()
