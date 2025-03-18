"""
Tests for the data retrieval functionality of the S2Match SDK.
"""

import pytest
from unittest.mock import Mock

from s2match import S2Match


def test_fetch_matches_by_player_uuid(sdk, mock_requests_get, sample_match_data):
    """Test fetching matches by player UUID."""
    # Configure the mock to return sample match data
    mock_response = Mock()
    mock_response.json.return_value = {"player_matches": sample_match_data}
    mock_requests_get.return_value = mock_response
    
    # Call the method
    player_uuid = "test-player-uuid-123456789"
    matches = sdk.fetch_matches_by_player_uuid(player_uuid, page_size=10, max_matches=100)
    
    # Verify the API was called correctly
    mock_requests_get.assert_called_once()
    args, kwargs = mock_requests_get.call_args
    
    # Check the URL
    assert "match/v1/player/test-player-uuid-123456789/match" in args[0]
    assert "page_size=10" in args[0]
    
    # Check the headers
    assert "Authorization" in kwargs["headers"]
    assert kwargs["headers"]["Authorization"].startswith("Bearer ")
    
    # Check the result
    assert matches == sample_match_data
    
    # Call again - should use cache
    matches2 = sdk.fetch_matches_by_player_uuid(player_uuid, page_size=10, max_matches=100)
    assert mock_requests_get.call_count == 1  # Still only one call
    assert matches2 == sample_match_data


def test_fetch_player_stats(sdk, mock_requests_get, sample_stats_data):
    """Test fetching player statistics."""
    # Configure the mock to return sample stats data
    mock_response = Mock()
    mock_response.json.return_value = sample_stats_data
    mock_requests_get.return_value = mock_response
    
    # Call the method
    player_uuid = "test-player-uuid-123456789"
    stats = sdk.fetch_player_stats(player_uuid)
    
    # Verify the API was called correctly
    mock_requests_get.assert_called_once()
    args, kwargs = mock_requests_get.call_args
    
    # Check the URL
    assert "match/v1/player/test-player-uuid-123456789/stats" in args[0]
    
    # Check the headers
    assert "Authorization" in kwargs["headers"]
    assert kwargs["headers"]["Authorization"].startswith("Bearer ")
    
    # Check the result
    assert stats == sample_stats_data
    
    # Call again - should use cache
    stats2 = sdk.fetch_player_stats(player_uuid)
    assert mock_requests_get.call_count == 1  # Still only one call
    assert stats2 == sample_stats_data


def test_fetch_matches_by_instance(sdk, mock_requests_get, sample_match_data):
    """Test fetching matches by instance ID."""
    # Configure the mock to return sample match data
    mock_response = Mock()
    mock_response.json.return_value = {"matches": sample_match_data}
    mock_requests_get.return_value = mock_response
    
    # Call the method
    instance_id = "test-instance-id-123456789"
    matches = sdk.fetch_matches_by_instance(instance_id, page_size=10)
    
    # Verify the API was called correctly
    mock_requests_get.assert_called_once()
    args, kwargs = mock_requests_get.call_args
    
    # Check the URL
    assert "match/v1/match" in args[0]
    assert "instance_id=test-instance-id-123456789" in args[0]
    assert "page_size=10" in args[0]
    
    # Check the headers
    assert "Authorization" in kwargs["headers"]
    assert kwargs["headers"]["Authorization"].startswith("Bearer ")
    
    # Check the result
    assert matches == sample_match_data


def test_fetch_player_by_platform_user_id(sdk, mock_requests_get, sample_player_data):
    """Test fetching a player by platform user ID."""
    # Configure the mock to return sample player data
    mock_response = Mock()
    mock_response.json.return_value = sample_player_data
    mock_requests_get.return_value = mock_response
    
    # Call the method
    platform = "Steam"
    platform_user_id = "test_user_id"
    player = sdk.fetch_player_by_platform_user_id(platform, platform_user_id)
    
    # Verify the API was called correctly
    mock_requests_get.assert_called_once()
    args, kwargs = mock_requests_get.call_args
    
    # Check the URL
    assert "users/v1/platform-user" in args[0]
    
    # Check the params
    assert kwargs["params"] == {"platform": "Steam", "platform_user_id": "test_user_id"}
    
    # Check the headers
    assert "Authorization" in kwargs["headers"]
    assert kwargs["headers"]["Authorization"].startswith("Bearer ")
    
    # Check the result
    assert player == sample_player_data


def test_fetch_player_with_displayname(sdk, mock_requests_get, sample_player_data):
    """Test fetching players by display name."""
    # Configure the mock to return sample player data
    mock_response = Mock()
    mock_response.json.return_value = sample_player_data
    mock_requests_get.return_value = mock_response
    
    # Call the method, without linked portals
    display_names = ["TestPlayer"]
    platform = "Steam"
    player_data = sdk.fetch_player_with_displayname(
        display_names=display_names, 
        platform=platform,
        include_linked_portals=False
    )
    
    # Verify the API was called correctly
    mock_requests_get.assert_called_once()
    args, kwargs = mock_requests_get.call_args
    
    # Check the URL
    assert "users/v1/player" in args[0]
    
    # Check the params
    assert kwargs["params"] == {"display_name": ["TestPlayer"], "platform": "Steam"}
    
    # Check the headers
    assert "Authorization" in kwargs["headers"]
    assert kwargs["headers"]["Authorization"].startswith("Bearer ")
    
    # Check the result
    assert player_data == sample_player_data 