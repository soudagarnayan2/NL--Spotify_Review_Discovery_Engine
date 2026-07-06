import unittest
import json
import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(__file__))
import mood_service

class TestMoodCatalog(unittest.TestCase):
    def setUp(self):
        self.config = {
            "happy": {
                "name": "Happy / Upbeat",
                "valence_range": [0.55, 1.0],
                "energy_range": [0.6, 1.0],
                "tempo_range": [120, 250],
                "danceability_range": [0.4, 1.0]
            },
            "chill": {
                "name": "Chill / Relaxed",
                "valence_range": [0.3, 0.7],
                "energy_range": [0.0, 0.45],
                "tempo_range": [65, 110]
            },
            "sad": {
                "name": "Sad / Melancholic",
                "valence_range": [0.0, 0.4],
                "energy_range": [0.0, 0.4],
                "tempo_range": [40, 115]
            },
            "nostalgic": {
                "name": "Nostalgic"
            }
        }
        
    def test_closeness(self):
        # Value inside range -> closeness = 1.0
        self.assertEqual(mood_service.closeness(0.5, 0.4, 0.6, 0.1), 1.0)
        # Value below range
        self.assertAlmostEqual(mood_service.closeness(0.3, 0.4, 0.6, 0.2), 0.5)
        # Value above range
        self.assertAlmostEqual(mood_service.closeness(0.8, 0.4, 0.6, 0.2), 0.0)

    def test_classify_happy_song(self):
        # A perfect happy track
        song = {
            "id": "test_happy",
            "valence": 0.8,
            "energy": 0.85,
            "tempo": 128,
            "danceability": 0.7,
            "acousticness": 0.1,
            "instrumentalness": 0.0,
            "release_year": 2022,
            "genre": "pop",
            "description": "very upbeat happy song"
        }
        scores, tags = mood_service.classify_song(song, self.config)
        self.assertIn("happy", tags)
        self.assertGreaterEqual(scores["happy"], 0.8)
        self.assertNotIn("sad", tags)

    def test_classify_sad_song(self):
        # A perfect sad track
        song = {
            "id": "test_sad",
            "valence": 0.15,
            "energy": 0.2,
            "tempo": 75,
            "danceability": 0.3,
            "acousticness": 0.9,
            "instrumentalness": 0.1,
            "release_year": 2018,
            "genre": "indie folk",
            "description": "painful heartbreak ballad"
        }
        scores, tags = mood_service.classify_song(song, self.config)
        self.assertIn("sad", tags)
        self.assertNotIn("happy", tags)

    def test_classify_nostalgic_song(self):
        song_old = {
            "id": "test_old",
            "valence": 0.5,
            "energy": 0.5,
            "tempo": 100,
            "danceability": 0.5,
            "acousticness": 0.5,
            "instrumentalness": 0.0,
            "release_year": 1975,
            "genre": "rock",
            "description": "classic retro rock"
        }
        scores, tags = mood_service.classify_song(song_old, self.config)
        self.assertIn("nostalgic", tags)
        self.assertGreaterEqual(scores["nostalgic"], 0.9)

    def test_feedback_penalty(self):
        song = {
            "id": "test_song",
            "valence": 0.8,
            "energy": 0.85,
            "tempo": 128,
            "danceability": 0.7,
            "acousticness": 0.1,
            "instrumentalness": 0.0,
            "release_year": 2022,
            "genre": "pop"
        }
        # Initially, it's happy
        scores, tags = mood_service.classify_song(song, self.config)
        self.assertIn("happy", tags)
        
        # Apply 3 negative feedbacks
        penalties = {("test_song", "happy"): 3}
        scores_penalized, tags_penalized = mood_service.classify_song(song, self.config, penalties)
        self.assertLess(scores_penalized["happy"], scores["happy"])
        # Should drop from tags if confidence goes below 0.55
        self.assertNotIn("happy", tags_penalized)

if __name__ == "__main__":
    unittest.main()
