"""
Tests for the data transformation functionality of the S2Match SDK.
"""

import json
import pytest
from unittest.mock import patch, mock_open

from s2match import S2Match


@pytest.fixture
def raw_player_data():
    """
    Sample raw player data for testing transformations.
    """
    return {
        "player_uuid": "test-player-uuid-123456789",
        "team_id": 1,
        "placement": 1,
        "joined_match_timestamp": "2023-06-01T12:00:00Z",
        "left_match_timestamp": "2023-06-01T12:30:00Z",
        "duration_seconds": 1800,
        "custom_data": {
            "CharacterChoice": "Gods.Anubis",
            "Kills": "10",
            "Deaths": "5",
            "Assists": "7",
            "TowerKills": "2",
            "PhoenixKills": "1",
            "TitanKills": "0",
            "TotalDamage": "25000",
            "TotalNPCDamage": "15000",
            "TotalDamageTaken": "20000",
            "TotalDamageMitigated": "10000",
            "TotalGoldEarned": "12000",
            "TotalXPEarned": "15000",
            "TotalStructureDamage": "5000",
            "TotalMinionDamage": "10000",
            "TotalAllyHealing": "0",
            "TotalSelfHealing": "8000",
            "TotalWardsPlaced": "5",
            "PlayerLevel": "20",
            "AssignedRole": "Mid",
            "PlayedRole": "Mid",
            "Items": "{\"Item1\":\"00000000-0000-0000-0000-00000000008c\",\"Item2\":\"00000000-0000-0000-0000-0000000000af\"}",
            "RolePreferences": "{\"First\":\"Mid\",\"Second\":\"Solo\"}",
            "Gods.Anubis.Damage": "15000",
            "Gods.Ra.Damage": "5000",
            "Items.SomeSword.Damage": "8000",
            "NPC.Minion.Damage": "10000"
        }
    }


@pytest.fixture
def raw_match_data(raw_player_data):
    """
    Sample raw match data for testing transformations.
    """
    player_data = raw_player_data.copy()
    player_data["match"] = {
        "match_id": "test-match-id-123456789",
        "start_timestamp": "2023-06-01T12:00:00Z",
        "end_timestamp": "2023-06-01T12:30:00Z",
        "custom_data": {
            "CurrentMap": "Conquest",
            "CurrentMode": "Ranked",
            "LobbyType": "Normal",
            "WinningTeam": "1"
        }
    }
    return [player_data]


@pytest.fixture
def sample_items_data():
    """
    Sample items data for testing enrichment.
    """
    return [
        {
            "Item_Id": "00000000-0000-0000-0000-00000000008c",
            "DisplayName": "Test Sword",
            "Description": "A test sword",
            "ItemType": "Weapon",
            "Cost": 1000
        },
        {
            "Item_Id": "00000000-0000-0000-0000-0000000000af",
            "DisplayName": "Test Shield",
            "Description": "A test shield",
            "ItemType": "Armor",
            "Cost": 800
        }
    ]


def test_transform_player(sdk, raw_player_data):
    """Test transforming a raw player record to SMITE 2 format."""
    transformed = sdk.transform_player(raw_player_data)
    
    # Check basic fields were copied correctly
    assert transformed["player_uuid"] == raw_player_data["player_uuid"]
    assert transformed["team_id"] == raw_player_data["team_id"]
    assert transformed["placement"] == raw_player_data["placement"]
    assert transformed["joined_match_timestamp"] == raw_player_data["joined_match_timestamp"]
    assert transformed["left_match_timestamp"] == raw_player_data["left_match_timestamp"]
    assert transformed["duration_seconds"] == raw_player_data["duration_seconds"]
    
    # Check that the god name was extracted correctly
    assert transformed["god_name"] == "Anubis"
    
    # Check that basic stats were parsed as integers
    assert transformed["basic_stats"]["Kills"] == 10
    assert transformed["basic_stats"]["Deaths"] == 5
    assert transformed["basic_stats"]["Assists"] == 7
    assert transformed["basic_stats"]["TowerKills"] == 2
    
    # Check that role info was preserved
    assert transformed["assigned_role"] == "Mid"
    assert transformed["played_role"] == "Mid"
    
    # Check that JSON fields were parsed
    assert transformed["items"] == {
        "Item1": "00000000-0000-0000-0000-00000000008c",
        "Item2": "00000000-0000-0000-0000-0000000000af"
    }
    
    assert transformed["role_preferences"] == {
        "First": "Mid",
        "Second": "Solo"
    }
    
    # Check damage breakdown
    assert "Anubis" in transformed["damage_breakdown"]
    assert transformed["damage_breakdown"]["Anubis"]["Damage"] == 15000
    assert transformed["damage_breakdown"]["Ra"]["Damage"] == 5000
    assert "SomeSword" in transformed["damage_breakdown"]
    assert "Misc" in transformed["damage_breakdown"]


def test_transform_matches(sdk, raw_match_data):
    """Test transforming raw match data to SMITE 2 format."""
    # Patch the _enrich_matches_with_item_data method to avoid issues with items.json
    with patch.object(sdk, '_enrich_matches_with_item_data', return_value=raw_match_data):
        transformed = sdk.transform_matches(raw_match_data)
    
    # Check that we got the right number of matches
    assert len(transformed) == 1
    
    match = transformed[0]
    
    # Check match-level fields
    assert match["match_id"] == "test-match-id-123456789"
    assert match["match_start"] == "2023-06-01T12:00:00Z"
    assert match["match_end"] == "2023-06-01T12:30:00Z"
    assert match["map"] == "Conquest"
    assert match["mode"] == "Ranked"
    assert match["lobby_type"] == "Normal"
    assert match["winning_team"] == "1"
    
    # Check that player data was transformed correctly
    assert match["god_name"] == "Anubis"
    assert match["basic_stats"]["Kills"] == 10
    assert match["items"] == {
        "Item1": "00000000-0000-0000-0000-00000000008c",
        "Item2": "00000000-0000-0000-0000-0000000000af"
    }


def test_load_items_map(sdk, sample_items_data):
    """Test loading and mapping item data."""
    # Mock the open function to return our sample items data
    with patch("builtins.open", mock_open(read_data=json.dumps(sample_items_data))):
        item_map = sdk._load_items_map()
    
    # Check that the items were loaded and mapped correctly
    assert "00000000-0000-0000-0000-00000000008c" in item_map
    assert "00000000-0000-0000-0000-0000000000af" in item_map
    assert item_map["00000000-0000-0000-0000-00000000008c"]["DisplayName"] == "Test Sword"
    assert item_map["00000000-0000-0000-0000-0000000000af"]["DisplayName"] == "Test Shield"


def test_replace_item_ids(sdk, sample_items_data):
    """Test replacing item IDs with full item data."""
    # Create a player record with item IDs
    player = {
        "items": {
            "Item1": "00000000-0000-0000-0000-00000000008c",
            "Item2": "00000000-0000-0000-0000-0000000000af",
            "Item3": "unknown-item-id"
        }
    }
    
    # Create an item map from our sample data
    item_map = {item["Item_Id"]: item for item in sample_items_data}
    
    # Replace the item IDs
    sdk._replace_item_ids(player, item_map)
    
    # Check that the item IDs were replaced with full item data
    assert player["items"]["Item1"] == sample_items_data[0]
    assert player["items"]["Item2"] == sample_items_data[1]
    
    # Check that unknown items get a fallback structure
    assert player["items"]["Item3"]["Item_Id"] == "unknown-item-id"
    assert player["items"]["Item3"]["DisplayName"] == "<display name missing>"


def test_enrich_matches_with_item_data(sdk, raw_match_data, sample_items_data):
    """Test enriching matches with item data."""
    # Mock the _load_items_map method to return our sample item map
    item_map = {item["Item_Id"]: item for item in sample_items_data}
    with patch.object(sdk, '_load_items_map', return_value=item_map):
        enriched = sdk._enrich_matches_with_item_data(raw_match_data)
    
    # Check that the items were enriched
    player = enriched[0]
    assert player["items"]["Item1"] == sample_items_data[0]
    assert player["items"]["Item2"] == sample_items_data[1] 