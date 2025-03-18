"""
Integration tests for the S2Match SDK.

These tests verify the complete workflow of the SDK, from authentication to data retrieval to transformation.
They use mocked API responses but test the full chain of function calls.

NOTE: These tests require mock responses in the mock_responses directory.
"""

import pytest
from unittest.mock import patch, Mock

from s2match import S2Match


@pytest.fixture
def mocked_sdk(mock_env_vars, mock_requests_post, mock_requests_get, 
               sample_player_data, sample_match_data, sample_stats_data, 
               sample_items_data):
    """
    Create a fully mocked SDK instance with prepared responses.
    
    This fixture sets up mock responses for all API calls used in the integration tests.
    """
    # Configure post mock (for authentication)
    mock_post_response = Mock()
    mock_post_response.json.return_value = {"access_token": "test_token", "expires_in": 3600}
    mock_requests_post.return_value = mock_post_response
    
    # Configure get mocks (for API calls)
    player_response = Mock()
    player_response.json.return_value = sample_player_data
    
    match_response = Mock()
    match_response.json.return_value = {"player_matches": sample_match_data}
    
    stats_response = Mock()
    stats_response.json.return_value = sample_stats_data
    
    # Using a side_effect to return different responses for different URLs
    def get_side_effect(*args, **kwargs):
        url = args[0]
        if "/player" in url and "/match" in url:
            return match_response
        elif "/stats" in url:
            return stats_response
        else:
            return player_response
    
    mock_requests_get.side_effect = get_side_effect
    
    # Create the SDK instance and patch the _load_items_map method
    sdk = S2Match()
    
    # Mock the items loading to avoid file system dependencies
    with patch.object(sdk, '_load_items_map') as mock_load_items:
        mock_load_items.return_value = {item["Item_Id"]: item for item in sample_items_data}
        yield sdk


def test_full_player_workflow(mocked_sdk):
    """Test the complete workflow of looking up a player and getting their match history."""
    # Step 1: Lookup player by display name
    player_data = mocked_sdk.fetch_player_with_displayname(
        display_names=["TestPlayer"],
        platform="Steam"
    )
    
    # Verify player data
    assert "display_names" in player_data
    
    # Get player UUID from response
    display_names = player_data.get("display_names", [])
    player_uuid = None
    for name_dict in display_names:
        for _, players in name_dict.items():
            if players:
                player_uuid = players[0].get("player_uuid")
                break
    
    assert player_uuid is not None
    
    # Step 2: Get player stats
    stats = mocked_sdk.get_player_stats(player_uuid)
    
    # Verify stats
    assert "total_matches_played" in stats
    
    # Step 3: Get match history (with transformation)
    matches = mocked_sdk.get_matches_by_player_uuid(player_uuid, max_matches=10)
    
    # Verify transformed match data
    assert len(matches) > 0
    match = matches[0]
    assert "god_name" in match
    assert "basic_stats" in match
    assert "items" in match
    
    # Check that item data was enriched
    for _, item in match["items"].items():
        assert isinstance(item, dict)
        assert "DisplayName" in item


def test_comprehensive_player_data(mocked_sdk):
    """Test getting comprehensive player data in a single call."""
    # This test verifies the helper method that combines multiple API calls
    full_data = mocked_sdk.get_full_player_data_by_displayname(
        platform="Steam",
        display_name="TestPlayer",
        max_matches=10
    )
    
    # Verify the combined structure
    assert "PlayerInfo" in full_data
    assert "PlayerStats" in full_data
    assert "MatchHistory" in full_data
    
    # Verify match history data
    assert len(full_data["MatchHistory"]) > 0
    
    # Verify player info
    assert "display_names" in full_data["PlayerInfo"]
    
    # Verify stats
    assert len(full_data["PlayerStats"]) > 0
    assert "player_uuid" in full_data["PlayerStats"][0]
    assert "stats" in full_data["PlayerStats"][0] 