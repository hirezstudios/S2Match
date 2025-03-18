"""
S2Match SDK Examples

This module demonstrates common usage patterns for the S2Match SDK,
which provides access to SMITE 2 match data through the RallyHere Environment API.

Before running these examples, make sure you have:
1. Installed all requirements (pip install -r requirements.txt)
2. Set up your environment variables or created a .env file with:
   - CLIENT_ID
   - CLIENT_SECRET
   - RH_BASE_URL

Example usage:
    python s2match_examples.py
"""

import os
import json
import logging
from dotenv import load_dotenv
from s2match import S2Match

# ------------------------------------------------------------------------------
# Quick-Config Flags & Test Variables
# ------------------------------------------------------------------------------
# These flags let you toggle specific examples on/off without commenting out code.
# Set any of them to False if you don't want to run that example when you execute this file.
ENABLE_PLAYER_LOOKUP = True
ENABLE_PLAYER_STATS = False
ENABLE_MATCH_HISTORY = True
ENABLE_FULL_PLAYER_DATA = True
ENABLE_MATCH_BY_INSTANCE = False

# Load environment variables from .env file
load_dotenv()

# Configure logging - Improved setup to better handle LOG_LEVEL
log_level_str = os.getenv("LOG_LEVEL", "INFO")
log_level = getattr(logging, log_level_str.upper(), logging.INFO)
print(f"Detected LOG_LEVEL from environment: {log_level_str} (Python level: {log_level})")

# Setup logging
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("S2MatchExamples")
logger.setLevel(log_level)  # Explicitly set the logger level

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
# These values can be adjusted to change the behavior of the examples
PLAYER_DISPLAY_NAME = "Weak3n"  # Example player display name to look up
PLAYER_PLATFORM = "Steam"      # Platform to search for the player
MAX_MATCHES = 5               # Maximum number of matches to retrieve

# Instance ID for match instance example
INSTANCE_ID = "55b5f41a-0526-45fa-b992-b212fd12a849"  # Example instance ID

# This flag determines whether to save JSON responses to disk
SAVE_JSON_RESPONSES = True

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
def save_json(data, function_name):
    """
    Saves data (Python object) as JSON into a file named 
    'example_response_{function_name}.json' in the 'examples' directory.
    """
    if not SAVE_JSON_RESPONSES:
        return
        
    os.makedirs("examples", exist_ok=True)
    filename = f"example_response_{function_name}.json"
    file_path = os.path.join("examples", filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved result of {function_name} to {file_path}")

# ------------------------------------------------------------------------------
# Example Functions
# ------------------------------------------------------------------------------
def example_player_lookup():
    """
    Demonstrates how to look up a player by display name.
    """
    logger.info(f"Example: Looking up player '{PLAYER_DISPLAY_NAME}' on platform '{PLAYER_PLATFORM}'")
    logger.debug("This is a debug message in the player lookup function")
    
    sdk = S2Match()
    player_data = sdk.fetch_player_with_displayname(
        display_names=[PLAYER_DISPLAY_NAME],
        platform=PLAYER_PLATFORM,
        include_linked_portals=True
    )
    
    save_json(player_data, "player_lookup")
    
    # Display some basic information
    display_names = player_data.get("display_names", [])
    if display_names:
        for display_name_dict in display_names:
            for name, players in display_name_dict.items():
                logger.info(f"Found {len(players)} results for '{name}'")
                for player in players:
                    logger.info(f"  Player UUID: {player.get('player_uuid')}")
                    logger.info(f"  Platform: {player.get('platform')}")
                    logger.info(f"  Linked portals: {len(player.get('linked_portals', []))}")
    
    # Return the first player UUID if found
    for display_name_dict in display_names:
        for name, players in display_name_dict.items():
            if players:
                return players[0].get("player_uuid")
    
    return None

def example_player_stats(player_uuid):
    """
    Demonstrates how to fetch and display player statistics.
    """
    if not player_uuid:
        logger.error("Cannot fetch player stats: No player UUID provided")
        return
        
    logger.info(f"Example: Fetching stats for player UUID '{player_uuid}'")
    
    sdk = S2Match()
    stats_data = sdk.get_player_stats(player_uuid)
    
    save_json(stats_data, "player_stats")
    
    # Display stats information
    logger.info(f"Total matches played: {stats_data.get('total_matches_played', 'N/A')}")
    logger.info(f"Total wins: {stats_data.get('total_wins', 'N/A')}")
    
    return stats_data

def example_match_history(player_uuid):
    """
    Demonstrates how to fetch and display player match history.
    """
    if not player_uuid:
        logger.error("Cannot fetch match history: No player UUID provided")
        return
        
    logger.info(f"Example: Fetching match history for player UUID '{player_uuid}'")
    logger.debug("This is a debug message in the match history function")
    
    sdk = S2Match()
    matches = sdk.get_matches_by_player_uuid(
        player_uuid=player_uuid,
        max_matches=MAX_MATCHES
    )
    
    save_json(matches, "match_history")
    
    # Display match information
    logger.info(f"Retrieved {len(matches)} matches:")
    for i, match in enumerate(matches, 1):
        logger.info(f"Match {i}:")
        logger.info(f"  Match ID: {match.get('match_id')}")
        logger.info(f"  God: {match.get('god_name')}")
        logger.info(f"  Mode: {match.get('mode')}")
        logger.info(f"  Map: {match.get('map')}")
        if "basic_stats" in match:
            stats = match["basic_stats"]
            logger.info(f"  K/D/A: {stats.get('Kills')}/{stats.get('Deaths')}/{stats.get('Assists')}")
    
    return matches

def example_full_player_data():
    """
    Demonstrates how to fetch comprehensive player data including
    profile, stats, and match history in a single call.
    """
    logger.info(f"Example: Fetching full player data for '{PLAYER_DISPLAY_NAME}'")
    
    sdk = S2Match()
    full_data = sdk.get_full_player_data_by_displayname(
        platform=PLAYER_PLATFORM,
        display_name=PLAYER_DISPLAY_NAME,
        max_matches=MAX_MATCHES
    )
    
    save_json(full_data, "full_player_data")
    
    # Display summary information
    logger.info("Full player data retrieved:")
    logger.info(f"  Player UUIDs found: {len(full_data.get('PlayerStats', []))}")
    logger.info(f"  Rank records: {len(full_data.get('PlayerRanks', []))}")
    logger.info(f"  Match history records: {len(full_data.get('MatchHistory', []))}")
    
    return full_data

def example_match_by_instance():
    """
    Demonstrates how to fetch match data by instance ID.
    Uses a specific match ID known to be valid.
    
    Note: This example may return 0 matches even with a valid match ID from the match history.
    This can happen if:
    1. The match history endpoint (/match/v1/player/{uuid}/match) and instance-based endpoint
       (/match/v1/match) have different access permissions
    2. The match data is no longer available through the instance-based endpoint
    3. The format of the match ID differs between endpoints
    """
    logger.info(f"Example: Fetching match data for instance ID '{INSTANCE_ID}'")
    
    sdk = S2Match()
    match_data = sdk.get_matches_by_instance(instance_id=INSTANCE_ID)
    
    save_json(match_data, "match_by_instance")
    
    # Display match information
    logger.info(f"Retrieved {len(match_data)} match records:")
    if not match_data:
        logger.info("  No match data found. This may be due to access limitations or data unavailability.")
    
    for i, match in enumerate(match_data, 1):
        logger.info(f"Match {i}:")
        logger.info(f"  Match ID: {match.get('match_id')}")
        logger.info(f"  Duration: {match.get('duration_seconds')} seconds")
        logger.info(f"  Map: {match.get('map')}")
        logger.info(f"  Mode: {match.get('mode')}")
        logger.info(f"  Players: {len(match.get('final_players', []))}")
    
    return match_data

# ------------------------------------------------------------------------------
# Main Function
# ------------------------------------------------------------------------------
def main():
    """
    Run example functions based on enabled flags to demonstrate S2Match SDK usage.
    """
    logger.info("S2Match SDK Examples")
    logger.info("-" * 80)
    logger.debug("This is a debug message from the main function")
    
    player_uuid = None
    
    try:
        # Example 1: Player lookup to get UUID
        if ENABLE_PLAYER_LOOKUP:
            player_uuid = example_player_lookup()
            logger.info("-" * 80)
        
        if player_uuid:
            # Example 2: Player stats
            if ENABLE_PLAYER_STATS:
                example_player_stats(player_uuid)
                logger.info("-" * 80)
            
            # Example 3: Match history
            if ENABLE_MATCH_HISTORY:
                example_match_history(player_uuid)
                logger.info("-" * 80)
        
        # Example 4: Full player data
        if ENABLE_FULL_PLAYER_DATA:
            example_full_player_data()
            logger.info("-" * 80)
        
        # Example 5: Match by instance
        if ENABLE_MATCH_BY_INSTANCE:
            example_match_by_instance()
            logger.info("-" * 80)
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("Examples complete!")

if __name__ == "__main__":
    main() 