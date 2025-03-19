"""
Unit tests for S2Match SDK

This module contains tests for the S2Match SDK functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
from s2match import S2Match
import requests

class TestS2Match(unittest.TestCase):
    """Test cases for the S2Match SDK."""

    def setUp(self):
        """Set up test environment."""
        # Create a mock .env file for testing
        os.environ["CLIENT_ID"] = "test_client_id"
        os.environ["CLIENT_SECRET"] = "test_client_secret"
        os.environ["RH_BASE_URL"] = "https://test.example.com"
        
        # Create SDK instance
        self.sdk = S2Match()
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove environment variables
        del os.environ["CLIENT_ID"]
        del os.environ["CLIENT_SECRET"]
        del os.environ["RH_BASE_URL"]
    
    def test_extract_player_uuids_normal_response(self):
        """Test extracting player UUIDs from a normal response."""
        # Sample response with multiple players
        response = {
            "display_names": [
                {
                    "TestPlayer1": [
                        {"player_uuid": "uuid1", "other_field": "value1"},
                        {"player_uuid": "uuid2", "other_field": "value2"}
                    ]
                },
                {
                    "TestPlayer2": [
                        {"player_uuid": "uuid3", "other_field": "value3"}
                    ]
                }
            ]
        }
        
        uuids = self.sdk.extract_player_uuids(response)
        
        # Check that the correct UUIDs were extracted
        self.assertEqual(len(uuids), 3)
        self.assertIn("uuid1", uuids)
        self.assertIn("uuid2", uuids)
        self.assertIn("uuid3", uuids)
    
    def test_extract_player_uuids_empty_response(self):
        """Test extracting player UUIDs from an empty response."""
        # Empty response
        response = {}
        
        uuids = self.sdk.extract_player_uuids(response)
        
        # Check that no UUIDs were extracted
        self.assertEqual(len(uuids), 0)
    
    def test_extract_player_uuids_missing_uuid(self):
        """Test extracting player UUIDs from a response with missing UUIDs."""
        # Response with a player missing a UUID
        response = {
            "display_names": [
                {
                    "TestPlayer1": [
                        {"player_uuid": "uuid1", "other_field": "value1"},
                        {"other_field": "value2"}  # Missing player_uuid
                    ]
                }
            ]
        }
        
        uuids = self.sdk.extract_player_uuids(response)
        
        # Check that only the valid UUID was extracted
        self.assertEqual(len(uuids), 1)
        self.assertIn("uuid1", uuids)
        
    def test_filter_matches_no_filters(self):
        """Test filtering matches with no filters (should return all matches)."""
        # Create test matches
        matches = [
            {"god_name": "Thor", "mode": "Conquest", "match_start": "2023-05-01T12:00:00Z", 
             "basic_stats": {"Kills": 10, "Deaths": 5, "Assists": 15}},
            {"god_name": "Anubis", "mode": "Arena", "match_start": "2023-06-15T18:30:00Z", 
             "basic_stats": {"Kills": 5, "Deaths": 8, "Assists": 3}}
        ]
        
        # Filter with empty dict
        filtered = self.sdk.filter_matches(matches, {})
        
        # Should return all matches
        self.assertEqual(len(filtered), 2)
        
        # Filter with None
        filtered = self.sdk.filter_matches(matches, None)
        
        # Should return all matches
        self.assertEqual(len(filtered), 2)
    
    def test_filter_matches_by_god(self):
        """Test filtering matches by god name."""
        # Create test matches
        matches = [
            {"god_name": "Thor", "mode": "Conquest"},
            {"god_name": "Anubis", "mode": "Arena"},
            {"god_name": "Thor", "mode": "Joust"}
        ]
        
        # Filter by god name
        filtered = self.sdk.filter_matches(matches, {"god_name": "Thor"})
        
        # Should return only Thor matches
        self.assertEqual(len(filtered), 2)
        for match in filtered:
            self.assertEqual(match["god_name"], "Thor")
    
    def test_filter_matches_by_mode(self):
        """Test filtering matches by game mode."""
        # Create test matches
        matches = [
            {"god_name": "Thor", "mode": "Conquest"},
            {"god_name": "Anubis", "mode": "Arena"},
            {"god_name": "Thor", "mode": "Joust"},
            {"god_name": "Zeus", "mode": "Conquest"}
        ]
        
        # Filter by mode
        filtered = self.sdk.filter_matches(matches, {"mode": "Conquest"})
        
        # Should return only Conquest matches
        self.assertEqual(len(filtered), 2)
        for match in filtered:
            self.assertEqual(match["mode"], "Conquest")
    
    def test_filter_matches_by_date_range(self):
        """Test filtering matches by date range."""
        # Create test matches with dates
        matches = [
            {"match_id": "match1", "match_start": "2023-01-15T12:00:00Z"},
            {"match_id": "match2", "match_start": "2023-05-20T14:30:00Z"},
            {"match_id": "match3", "match_start": "2023-08-10T18:45:00Z"},
            {"match_id": "match4", "match_start": "2023-12-25T10:15:00Z"}
        ]
        
        # Filter by min date only
        filtered = self.sdk.filter_matches(matches, {"min_date": "2023-05-01"})
        
        # Should return matches from May 1 and later (May, Aug, Dec)
        self.assertEqual(len(filtered), 3)
        # Verify the right matches were included
        match_ids = [match["match_id"] for match in filtered]
        self.assertIn("match2", match_ids)  # May
        self.assertIn("match3", match_ids)  # Aug
        self.assertIn("match4", match_ids)  # Dec
        
        # Filter by max date only
        filtered = self.sdk.filter_matches(matches, {"max_date": "2023-09-01"})
        
        # Should return matches before Sep 1 (Jan, May, Aug)
        self.assertEqual(len(filtered), 3)
        # Verify the right matches were included
        match_ids = [match["match_id"] for match in filtered]
        self.assertIn("match1", match_ids)  # Jan
        self.assertIn("match2", match_ids)  # May
        self.assertIn("match3", match_ids)  # Aug
        
        # Filter by date range
        filtered = self.sdk.filter_matches(matches, {
            "min_date": "2023-02-01",
            "max_date": "2023-10-01"
        })
        
        # Should return matches between Feb 1 and Oct 1 (May, Aug)
        self.assertEqual(len(filtered), 2)
        # Verify the right matches were included
        match_ids = [match["match_id"] for match in filtered]
        self.assertIn("match2", match_ids)  # May
        self.assertIn("match3", match_ids)  # Aug
    
    def test_filter_matches_by_performance(self):
        """Test filtering matches by performance metrics."""
        # Create test matches with performance stats
        matches = [
            {"basic_stats": {"Kills": 10, "Deaths": 5, "Assists": 7}},  # KDA: 3.4
            {"basic_stats": {"Kills": 5, "Deaths": 10, "Assists": 15}},  # KDA: 2.0
            {"basic_stats": {"Kills": 20, "Deaths": 2, "Assists": 8}},  # KDA: 14.0
            {"basic_stats": {"Kills": 3, "Deaths": 15, "Assists": 2}}   # KDA: 0.33
        ]
        
        # Filter by min kills
        filtered = self.sdk.filter_matches(matches, {"min_kills": 10})
        
        # Should return matches with 10+ kills (first and third)
        self.assertEqual(len(filtered), 2)
        
        # Filter by max deaths
        filtered = self.sdk.filter_matches(matches, {"max_deaths": 5})
        
        # Should return matches with 5 or fewer deaths (first and third)
        self.assertEqual(len(filtered), 2)
        
        # Filter by min KDA
        filtered = self.sdk.filter_matches(matches, {"min_kda": 3.0})
        
        # Should return matches with KDA >= 3.0 (first and third)
        self.assertEqual(len(filtered), 2)
        
        # Filter by multiple criteria
        filtered = self.sdk.filter_matches(matches, {
            "min_kills": 10,
            "max_deaths": 5,
            "min_kda": 3.0
        })
        
        # Should return matches meeting all criteria (first and third)
        self.assertEqual(len(filtered), 2)
    
    def test_filter_matches_by_win(self):
        """Test filtering matches by win status."""
        # Create test matches with win info
        matches = [
            {"team_id": 1, "winning_team": 1},  # Win
            {"team_id": 2, "winning_team": 1},  # Loss
            {"team_id": 1, "winning_team": 2},  # Loss
            {"team_id": 2, "winning_team": 2}   # Win
        ]
        
        # Filter by wins only
        filtered = self.sdk.filter_matches(matches, {"win_only": True})
        
        # Should return only winning matches
        self.assertEqual(len(filtered), 2)
        for match in filtered:
            self.assertEqual(match["team_id"], match["winning_team"])
    
    def test_filter_matches_combined_filters(self):
        """Test filtering matches with multiple criteria."""
        # Create test matches with various attributes
        matches = [
            {
                "god_name": "Thor", 
                "mode": "Conquest", 
                "match_start": "2023-05-01T12:00:00Z",
                "team_id": 1,
                "winning_team": 1,
                "basic_stats": {"Kills": 10, "Deaths": 5, "Assists": 15}
            },
            {
                "god_name": "Anubis", 
                "mode": "Arena", 
                "match_start": "2023-06-15T18:30:00Z",
                "team_id": 2,
                "winning_team": 1,
                "basic_stats": {"Kills": 5, "Deaths": 8, "Assists": 3}
            },
            {
                "god_name": "Thor", 
                "mode": "Conquest", 
                "match_start": "2023-07-20T14:45:00Z",
                "team_id": 1,
                "winning_team": 2,
                "basic_stats": {"Kills": 3, "Deaths": 10, "Assists": 12}
            }
        ]
        
        # Filter with multiple criteria
        filtered = self.sdk.filter_matches(matches, {
            "god_name": "Thor",
            "mode": "Conquest",
            "min_date": "2023-01-01",
            "max_date": "2023-06-01",
            "win_only": True,
            "min_kills": 8
        })
        
        # Should return only matches meeting all criteria
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["god_name"], "Thor")
        self.assertEqual(filtered[0]["mode"], "Conquest")
        self.assertEqual(filtered[0]["team_id"], filtered[0]["winning_team"])
        self.assertGreaterEqual(filtered[0]["basic_stats"]["Kills"], 8)

    def test_calculate_player_performance_empty_matches(self):
        """Test calculate_player_performance with empty matches list."""
        result = self.sdk.calculate_player_performance([])
        self.assertEqual({}, result)

    def test_calculate_player_performance_normal_case(self):
        """Test calculate_player_performance with normal match data."""
        # Create mock match data
        matches = [
            {
                "player_uuid": "test-uuid-1",
                "team_id": 1,
                "winning_team": 1,  # Win
                "god_name": "Thor",
                "mode": "Conquest",
                "played_role": "Jungle",
                "basic_stats": {
                    "Kills": 10,
                    "Deaths": 5,
                    "Assists": 8,
                    "TotalDamage": 20000,
                    "TotalAllyHealing": 1000,
                    "TotalSelfHealing": 2000,
                    "TotalDamageMitigated": 5000,
                    "TotalStructureDamage": 3000,
                    "TotalMinionDamage": 15000,
                    "TotalGoldEarned": 12000,
                    "TotalWardsPlaced": 5
                }
            },
            {
                "player_uuid": "test-uuid-1",
                "team_id": 2,
                "winning_team": 1,  # Loss
                "god_name": "Anubis",
                "mode": "Arena",
                "played_role": "Mid",
                "basic_stats": {
                    "Kills": 8,
                    "Deaths": 7,
                    "Assists": 4,
                    "TotalDamage": 25000,
                    "TotalAllyHealing": 0,
                    "TotalSelfHealing": 3000,
                    "TotalDamageMitigated": 2000,
                    "TotalStructureDamage": 0,
                    "TotalMinionDamage": 18000,
                    "TotalGoldEarned": 10000,
                    "TotalWardsPlaced": 2
                }
            },
            {
                "player_uuid": "test-uuid-1",
                "team_id": 1,
                "winning_team": 1,  # Win
                "god_name": "Thor",
                "mode": "Conquest",
                "played_role": "Jungle",
                "basic_stats": {
                    "Kills": 12,
                    "Deaths": 3,
                    "Assists": 15,
                    "TotalDamage": 22000,
                    "TotalAllyHealing": 500,
                    "TotalSelfHealing": 1500,
                    "TotalDamageMitigated": 4000,
                    "TotalStructureDamage": 2000,
                    "TotalMinionDamage": 16000,
                    "TotalGoldEarned": 14000,
                    "TotalWardsPlaced": 4
                }
            }
        ]
        
        result = self.sdk.calculate_player_performance(matches)
        
        # Check basic stats
        self.assertEqual(3, result["total_matches"])
        self.assertEqual(2, result["wins"])
        self.assertEqual(1, result["losses"])
        self.assertAlmostEqual(2/3, result["win_rate"])
        
        # Check totals
        self.assertEqual(30, result["total_kills"])
        self.assertEqual(15, result["total_deaths"])
        self.assertEqual(27, result["total_assists"])
        
        # Check averages
        self.assertAlmostEqual(10.0, result["avg_kills"])
        self.assertAlmostEqual(5.0, result["avg_deaths"])
        self.assertAlmostEqual(9.0, result["avg_assists"])
        self.assertAlmostEqual((30 + 27) / 15, result["avg_kda"])
        
        # Check favorite/best metrics
        self.assertEqual("Thor", result["favorite_god"])
        self.assertEqual("Jungle", result["favorite_role"])
        self.assertEqual("Conquest", result["favorite_mode"])
        self.assertEqual("Thor", result["best_performing_god"])
        
        # Verify structure
        self.assertIn("god_stats", result)
        self.assertIn("mode_stats", result)
        self.assertIn("role_stats", result)

    def test_calculate_player_performance_no_wins(self):
        """Test calculate_player_performance with no wins."""
        # Create mock match data with no wins
        matches = [
            {
                "player_uuid": "test-uuid-1",
                "team_id": 2,
                "winning_team": 1,  # Loss
                "god_name": "Thor",
                "mode": "Conquest",
                "basic_stats": {
                    "Kills": 5,
                    "Deaths": 10,
                    "Assists": 3
                }
            },
            {
                "player_uuid": "test-uuid-1",
                "team_id": 2,
                "winning_team": 1,  # Loss
                "god_name": "Anubis",
                "mode": "Arena",
                "basic_stats": {
                    "Kills": 8,
                    "Deaths": 12,
                    "Assists": 4
                }
            }
        ]
        
        result = self.sdk.calculate_player_performance(matches)
        
        # Verify key metrics
        self.assertEqual(2, result["total_matches"])
        self.assertEqual(0, result["wins"])
        self.assertEqual(2, result["losses"])
        self.assertEqual(0, result["win_rate"])
        
        # Verify god win rates are 0
        for god, stats in result["god_stats"].items():
            self.assertEqual(0, stats["win_rate"])

    def test_calculate_player_performance_god_stats(self):
        """Test god statistics calculation."""
        # Create mock match data with the same god
        matches = [
            {
                "player_uuid": "test-uuid-1",
                "team_id": 1,
                "winning_team": 1,  # Win
                "god_name": "Thor",
                "mode": "Conquest",
                "basic_stats": {
                    "Kills": 10,
                    "Deaths": 5,
                    "Assists": 8,
                    "TotalDamage": 20000
                }
            },
            {
                "player_uuid": "test-uuid-1",
                "team_id": 1,
                "winning_team": 1,  # Win
                "god_name": "Thor",
                "mode": "Conquest",
                "basic_stats": {
                    "Kills": 12,
                    "Deaths": 3,
                    "Assists": 15,
                    "TotalDamage": 25000
                }
            }
        ]
        
        result = self.sdk.calculate_player_performance(matches)
        
        # Check Thor stats
        thor_stats = result["god_stats"]["Thor"]
        self.assertEqual(2, thor_stats["matches"])
        self.assertEqual(2, thor_stats["wins"])
        self.assertEqual(1.0, thor_stats["win_rate"])
        self.assertEqual(22, thor_stats["kills"])
        self.assertEqual(8, thor_stats["deaths"])
        self.assertEqual(23, thor_stats["assists"])
        self.assertAlmostEqual(11.0, thor_stats["avg_kills"])
        self.assertAlmostEqual(4.0, thor_stats["avg_deaths"])
        self.assertAlmostEqual(11.5, thor_stats["avg_assists"])
        self.assertAlmostEqual((22 + 23) / 8, thor_stats["avg_kda"])
        self.assertAlmostEqual(45000, thor_stats["damage"])
        self.assertAlmostEqual(22500, thor_stats["avg_damage"])

    def test_calculate_player_performance_mode_stats(self):
        """Test game mode statistics calculation."""
        # Create mock match data with different modes
        matches = [
            {
                "player_uuid": "test-uuid-1",
                "team_id": 1,
                "winning_team": 1,  # Win
                "god_name": "Thor",
                "mode": "Conquest",
                "basic_stats": {
                    "Kills": 10,
                    "Deaths": 5,
                    "Assists": 8
                }
            },
            {
                "player_uuid": "test-uuid-1",
                "team_id": 2,
                "winning_team": 1,  # Loss
                "god_name": "Anubis",
                "mode": "Arena",
                "basic_stats": {
                    "Kills": 15,
                    "Deaths": 8,
                    "Assists": 3
                }
            },
            {
                "player_uuid": "test-uuid-1",
                "team_id": 1,
                "winning_team": 1,  # Win
                "god_name": "Zeus",
                "mode": "Arena",
                "basic_stats": {
                    "Kills": 20,
                    "Deaths": 10,
                    "Assists": 5
                }
            }
        ]
        
        result = self.sdk.calculate_player_performance(matches)
        
        # Check Conquest stats
        conquest_stats = result["mode_stats"]["Conquest"]
        self.assertEqual(1, conquest_stats["matches"])
        self.assertEqual(1, conquest_stats["wins"])
        self.assertEqual(1.0, conquest_stats["win_rate"])
        self.assertEqual(10, conquest_stats["kills"])
        self.assertEqual(5, conquest_stats["deaths"])
        self.assertEqual(8, conquest_stats["assists"])
        
        # Check Arena stats
        arena_stats = result["mode_stats"]["Arena"]
        self.assertEqual(2, arena_stats["matches"])
        self.assertEqual(1, arena_stats["wins"])
        self.assertEqual(0.5, arena_stats["win_rate"])
        self.assertEqual(35, arena_stats["kills"])
        self.assertEqual(18, arena_stats["deaths"])
        self.assertEqual(8, arena_stats["assists"])
        self.assertAlmostEqual(17.5, arena_stats["avg_kills"])
        self.assertAlmostEqual(9.0, arena_stats["avg_deaths"])
        self.assertAlmostEqual(4.0, arena_stats["avg_assists"])
        self.assertAlmostEqual((35 + 8) / 18, arena_stats["avg_kda"])

    def test_flatten_player_lookup_response_normal_case(self):
        """Test flattening player lookup response with a normal response structure."""
        # Create a mock player lookup response
        response = {
            "display_names": [
                {
                    "PlayerOne": [
                        {
                            "player_uuid": "uuid-1",
                            "player_id": 12345,
                            "platform": "Steam"
                        }
                    ]
                },
                {
                    "PlayerTwo": [
                        {
                            "player_uuid": "uuid-2",
                            "player_id": 67890,
                            "platform": "XboxLive"
                        },
                        {
                            "player_uuid": "uuid-3",
                            "player_id": 54321,
                            "platform": "PSN"
                        }
                    ]
                }
            ]
        }
        
        flattened = self.sdk.flatten_player_lookup_response(response)
        
        # Verify the result
        self.assertEqual(3, len(flattened))
        
        # Check the first player
        self.assertEqual("PlayerOne", flattened[0]["display_name"])
        self.assertEqual("uuid-1", flattened[0]["player_uuid"])
        self.assertEqual(12345, flattened[0]["player_id"])
        self.assertEqual("Steam", flattened[0]["platform"])
        
        # Check the second player
        self.assertEqual("PlayerTwo", flattened[1]["display_name"])
        self.assertEqual("uuid-2", flattened[1]["player_uuid"])
        self.assertEqual("XboxLive", flattened[1]["platform"])
        
        # Check the third player
        self.assertEqual("PlayerTwo", flattened[2]["display_name"])
        self.assertEqual("uuid-3", flattened[2]["player_uuid"])
        self.assertEqual("PSN", flattened[2]["platform"])

    def test_flatten_player_lookup_response_empty_response(self):
        """Test flattening empty player lookup response."""
        flattened = self.sdk.flatten_player_lookup_response({})
        self.assertEqual([], flattened)
        
        flattened = self.sdk.flatten_player_lookup_response(None)
        self.assertEqual([], flattened)

    def test_flatten_player_lookup_response_empty_display_names(self):
        """Test flattening player lookup response with empty display_names list."""
        response = {
            "display_names": []
        }
        flattened = self.sdk.flatten_player_lookup_response(response)
        self.assertEqual([], flattened)

    def test_flatten_player_lookup_response_empty_player_list(self):
        """Test flattening player lookup response with empty player list."""
        response = {
            "display_names": [
                {
                    "EmptyPlayer": []
                },
                {
                    "PlayerWithData": [
                        {
                            "player_uuid": "uuid-1",
                            "player_id": 12345,
                            "platform": "Steam"
                        }
                    ]
                }
            ]
        }
        flattened = self.sdk.flatten_player_lookup_response(response)
        
        # Only one player should be in the result
        self.assertEqual(1, len(flattened))
        self.assertEqual("PlayerWithData", flattened[0]["display_name"])
        self.assertEqual("uuid-1", flattened[0]["player_uuid"])

    def test_calculate_backoff_delay(self):
        """Test that backoff delay calculation works as expected."""
        sdk = S2Match(
            client_id="test_id",
            client_secret="test_secret",
            base_url="https://test.example.com",
            base_retry_delay=1.0,
            max_retry_delay=60.0
        )
        
        # Test basic exponential growth
        # We can't test exact values due to random jitter, but we can test ranges
        delay0 = sdk._calculate_backoff_delay(0)
        self.assertGreaterEqual(delay0, 0.8)  # Base delay (1.0) minus max jitter
        self.assertLessEqual(delay0, 1.2)     # Base delay (1.0) plus max jitter
        
        delay1 = sdk._calculate_backoff_delay(1)
        self.assertGreaterEqual(delay1, 1.6)  # Base delay * 2 (2.0) minus max jitter
        self.assertLessEqual(delay1, 2.4)     # Base delay * 2 (2.0) plus max jitter
        
        delay2 = sdk._calculate_backoff_delay(2)
        self.assertGreaterEqual(delay2, 3.2)  # Base delay * 4 (4.0) minus max jitter
        self.assertLessEqual(delay2, 4.8)     # Base delay * 4 (4.0) plus max jitter
        
        # Test max delay cap
        delay10 = sdk._calculate_backoff_delay(10)  # 1.0 * 2^10 = 1024, which exceeds our max of 60
        self.assertLessEqual(delay10, 72.0)  # Max delay (60.0) plus max jitter
        
    def test_make_request_with_retry_success(self):
        """Test that a successful request returns normally."""
        import unittest.mock as mock
        
        # Create a mock response object
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        
        # Create a mock Requests.get that returns this response
        with mock.patch('requests.get', return_value=mock_response) as mock_get:
            sdk = S2Match(
                client_id="test_id",
                client_secret="test_secret",
                base_url="https://test.example.com"
            )
            
            # Call our method
            response = sdk._make_request_with_retry('get', 'https://test.example.com/test')
            
            # Verify we called requests.get once
            mock_get.assert_called_once_with('https://test.example.com/test')
            
            # Verify we got the expected response
            self.assertEqual(response, mock_response)
            
    def test_make_request_with_retry_rate_limit(self):
        """Test that rate limited requests are retried."""
        import unittest.mock as mock
        
        # Create mock responses
        rate_limit_response = mock.MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {}
        
        success_response = mock.MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"test": "data"}
        
        # Setup mock to return rate limit first, then success
        mock_get = mock.MagicMock(side_effect=[rate_limit_response, success_response])
        
        # Create a mock for time.sleep to avoid actual delays
        with mock.patch('requests.get', mock_get), \
             mock.patch('time.sleep', return_value=None) as mock_sleep:
            
            sdk = S2Match(
                client_id="test_id",
                client_secret="test_secret",
                base_url="https://test.example.com",
                base_retry_delay=1.0
            )
            
            # Call our method
            response = sdk._make_request_with_retry('get', 'https://test.example.com/test')
            
            # Verify we called requests.get twice
            self.assertEqual(mock_get.call_count, 2)
            
            # Verify we slept once
            mock_sleep.assert_called_once()
            
            # Verify we got the success response
            self.assertEqual(response, success_response)
            
    def test_make_request_with_retry_max_attempts(self):
        """Test that requests fail after max retry attempts."""
        import unittest.mock as mock
        
        # Create a rate limit response
        rate_limit_response = mock.MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {}
        
        # Create a HTTPError exception with a proper response attribute
        http_error = requests.exceptions.HTTPError("429 Client Error")
        http_error.response = rate_limit_response
        rate_limit_response.raise_for_status.side_effect = http_error
        
        # Setup mock to always return rate limit 
        mock_get = mock.MagicMock(return_value=rate_limit_response)
        
        # Create a mock for time.sleep to avoid actual delays
        with mock.patch('requests.get', mock_get), \
             mock.patch('time.sleep', return_value=None):
            
            sdk = S2Match(
                client_id="test_id",
                client_secret="test_secret",
                base_url="https://test.example.com",
                base_retry_delay=0.1,
                max_retries=2  # Set low for faster testing
            )
            
            # Call our method - should raise an exception
            with self.assertRaises(requests.exceptions.HTTPError):
                sdk._make_request_with_retry('get', 'https://test.example.com/test')
            
            # Verify we called requests.get the expected number of times (initial + 2 retries)
            self.assertEqual(mock_get.call_count, 3)
            
    def test_retry_after_header_respected(self):
        """Test that Retry-After header values are respected."""
        import unittest.mock as mock
        
        # Create mock responses with Retry-After header
        rate_limit_response = mock.MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {'Retry-After': '5.0'}  # 5 seconds
        
        success_response = mock.MagicMock()
        success_response.status_code = 200
        
        # Setup mock to return rate limit first, then success
        mock_get = mock.MagicMock(side_effect=[rate_limit_response, success_response])
        
        # Create a mock for time.sleep to avoid actual delays
        with mock.patch('requests.get', mock_get), \
             mock.patch('time.sleep', return_value=None) as mock_sleep:
            
            sdk = S2Match(
                client_id="test_id",
                client_secret="test_secret",
                base_url="https://test.example.com",
                base_retry_delay=1.0  # Base delay is less than Retry-After 
            )
            
            # Call our method
            sdk._make_request_with_retry('get', 'https://test.example.com/test')
            
            # Verify we slept with a delay >= 5.0 (the Retry-After value)
            # accounting for jitter
            sleep_arg = mock_sleep.call_args[0][0]
            self.assertGreaterEqual(sleep_arg, 5.0)

if __name__ == "__main__":
    unittest.main() 