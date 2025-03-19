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
ENABLE_EXTRACT_PLAYER_UUIDS = True  # New flag for extract_player_uuids example
ENABLE_FILTER_MATCHES = True  # New flag for filter_matches example
ENABLE_PLAYER_PERFORMANCE = True  # New flag for player_performance example
ENABLE_FLATTEN_PLAYER_LOOKUP = True  # New flag for flatten_player_lookup example
ENABLE_RATE_LIMIT_HANDLING = True  # New flag for rate_limit_handling example

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

def example_extract_player_uuids():
    """
    Demonstrates how to use the extract_player_uuids helper method to
    quickly retrieve all player UUIDs from a player lookup response.
    """
    logger.info(f"Example: Extracting player UUIDs for '{PLAYER_DISPLAY_NAME}'")
    
    sdk = S2Match()
    # First, get the player lookup response
    player_data = sdk.fetch_player_with_displayname(
        display_names=[PLAYER_DISPLAY_NAME],
        platform=PLAYER_PLATFORM,
        include_linked_portals=True
    )
    
    # Now extract the UUIDs using the helper method
    player_uuids = sdk.extract_player_uuids(player_data)
    
    # Display the results
    logger.info(f"Found {len(player_uuids)} player UUIDs:")
    for i, uuid in enumerate(player_uuids, 1):
        logger.info(f"  UUID {i}: {uuid}")
    
    save_json({"player_uuids": player_uuids}, "extract_player_uuids")
    
    return player_uuids

def example_filter_matches(player_uuid=None):
    """
    Demonstrates how to use the filter_matches helper method to
    filter match data by various criteria.
    """
    logger.info("Example: Filtering match data with various criteria")
    
    # If no player UUID is provided, find one with player lookup
    if not player_uuid:
        sdk = S2Match()
        player_data = sdk.fetch_player_with_displayname(
            display_names=[PLAYER_DISPLAY_NAME],
            platform=PLAYER_PLATFORM
        )
        player_uuids = sdk.extract_player_uuids(player_data)
        player_uuid = player_uuids[0] if player_uuids else None
        
    if not player_uuid:
        logger.error("Cannot filter matches: No player UUID available")
        return
    
    logger.info(f"Using player UUID: {player_uuid}")
    
    # Get match history for the player
    sdk = S2Match()
    matches = sdk.get_matches_by_player_uuid(
        player_uuid=player_uuid,
        max_matches=MAX_MATCHES
    )
    
    logger.info(f"Retrieved {len(matches)} matches")
    
    # Example 1: Filter by god name
    god_name = None
    # Find the first god with multiple matches for a better example
    god_counts = {}
    for match in matches:
        god = match.get("god_name")
        god_counts[god] = god_counts.get(god, 0) + 1
        
    # Select a god with at least 2 matches if possible
    for god, count in god_counts.items():
        if count >= 2:
            god_name = god
            break
            
    # Fall back to any god if none has multiple matches
    if not god_name and matches:
        god_name = matches[0].get("god_name")
        
    if god_name:
        logger.info(f"Filtering matches by god: {god_name}")
        filtered = sdk.filter_matches(matches, {"god_name": god_name})
        logger.info(f"Found {len(filtered)} matches with {god_name}")
        
        # Save filtered results
        save_json(filtered, "filter_matches_by_god")
    
    # Example 2: Filter wins only
    logger.info("Filtering matches by wins only")
    wins = sdk.filter_matches(matches, {"win_only": True})
    logger.info(f"Found {len(wins)} winning matches out of {len(matches)}")
    
    # Save filtered results
    save_json(wins, "filter_matches_wins")
    
    # Example 3: Filter by performance (KDA)
    logger.info("Filtering matches by performance (KDA >= 3.0)")
    high_kda = sdk.filter_matches(matches, {"min_kda": 3.0})
    logger.info(f"Found {len(high_kda)} matches with KDA >= 3.0")
    
    # Save filtered results
    save_json(high_kda, "filter_matches_high_kda")
    
    # Example 4: Combined filters
    logger.info("Applying combined filters (wins with high KDA)")
    combined = sdk.filter_matches(matches, {
        "win_only": True,
        "min_kda": 3.0
    })
    logger.info(f"Found {len(combined)} winning matches with KDA >= 3.0")
    
    # Save filtered results
    save_json(combined, "filter_matches_combined")
    
    return matches

def example_player_performance(player_uuid=None):
    """
    Demonstrates how to use the calculate_player_performance helper method to
    generate comprehensive player performance metrics from match history.
    """
    logger.info("Example: Calculating player performance metrics")
    
    # If no player UUID is provided, find one with player lookup
    if not player_uuid:
        sdk = S2Match()
        player_data = sdk.fetch_player_with_displayname(
            display_names=[PLAYER_DISPLAY_NAME],
            platform=PLAYER_PLATFORM
        )
        player_uuids = sdk.extract_player_uuids(player_data)
        player_uuid = player_uuids[0] if player_uuids else None
        
    if not player_uuid:
        logger.error("Cannot calculate performance metrics: No player UUID available")
        return
    
    logger.info(f"Using player UUID: {player_uuid}")
    
    # Get match history for the player
    sdk = S2Match()
    matches = sdk.get_matches_by_player_uuid(
        player_uuid=player_uuid,
        max_matches=MAX_MATCHES
    )
    
    logger.info(f"Retrieved {len(matches)} matches for performance analysis")
    
    # Calculate player performance metrics using the helper method
    performance_stats = sdk.calculate_player_performance(matches)
    
    # Display key performance metrics
    logger.info("\nPlayer Performance Summary:")
    logger.info(f"Total Matches: {performance_stats.get('total_matches')}")
    logger.info(f"Win Rate: {performance_stats.get('win_rate', 0):.1%}")
    logger.info(f"KDA Ratio: {performance_stats.get('avg_kda', 0):.2f} ({performance_stats.get('avg_kills', 0):.1f}/{performance_stats.get('avg_deaths', 0):.1f}/{performance_stats.get('avg_assists', 0):.1f})")
    logger.info(f"Avg Damage per Match: {performance_stats.get('avg_damage_per_match', 0):,.0f}")
    logger.info(f"Favorite God: {performance_stats.get('favorite_god', 'Unknown')}")
    logger.info(f"Favorite Role: {performance_stats.get('favorite_role', 'Unknown')}")
    
    # Display god performance stats
    logger.info("\nPerformance by God:")
    god_stats = performance_stats.get("god_stats", {})
    for god, stats in sorted(god_stats.items(), key=lambda x: x[1]["matches"], reverse=True):
        logger.info(f"  {god}: {stats['matches']} matches, {stats['win_rate']:.1%} win rate, {stats['avg_kda']:.2f} KDA")
    
    # Display mode performance stats
    logger.info("\nPerformance by Game Mode:")
    mode_stats = performance_stats.get("mode_stats", {})
    for mode, stats in sorted(mode_stats.items(), key=lambda x: x[1]["matches"], reverse=True):
        logger.info(f"  {mode}: {stats['matches']} matches, {stats['win_rate']:.1%} win rate")
    
    # Save performance stats to a file
    save_json(performance_stats, "player_performance")
    
    return performance_stats

def example_flatten_player_lookup():
    """
    Demonstrates how to use the flatten_player_lookup_response helper method to
    transform the complex nested player lookup response structure into a simple flat list.
    """
    logger.info("Example: Flattening player lookup response")
    
    # First, get a player lookup response using the API
    sdk = S2Match()
    response = sdk.fetch_player_with_displayname(
        display_names=[PLAYER_DISPLAY_NAME],
        platform=PLAYER_PLATFORM,
        include_linked_portals=True
    )
    
    logger.info(f"Fetched player data for '{PLAYER_DISPLAY_NAME}'")
    
    # Save the raw response
    save_json(response, "player_lookup_raw")
    
    # Show the nested structure of the raw response
    logger.info("\nRaw Response Structure:")
    if "display_names" in response:
        found_players = 0
        for display_name_dict in response.get("display_names", []):
            for name, players in display_name_dict.items():
                found_players += len(players)
                logger.info(f"  Found {len(players)} player(s) for name '{name}'")
                
        logger.info(f"  Total players in nested structure: {found_players}")
        
        # Show a simplified view of the access pattern required
        logger.info("\nAccess Pattern for Raw Response:")
        logger.info("  for display_name_dict in response.get('display_names', []):")
        logger.info("      for name, players in display_name_dict.items():")
        logger.info("          for player in players:")
        logger.info("              # Now we can use player data")
        logger.info("              player_uuid = player.get('player_uuid')")
    else:
        logger.info("  No display_names found in response")
    
    # Now flatten the response
    flattened = sdk.flatten_player_lookup_response(response)
    
    # Save the flattened response
    save_json(flattened, "player_lookup_flattened")
    
    # Show how much simpler the flattened structure is
    logger.info("\nFlattened Response Structure:")
    logger.info(f"  Total players in flattened structure: {len(flattened)}")
    
    # Show players in the flattened list
    for i, player in enumerate(flattened, 1):
        logger.info(f"  Player {i}:")
        logger.info(f"    Display Name: {player.get('display_name')}")
        logger.info(f"    Player UUID: {player.get('player_uuid')}")
        logger.info(f"    Platform: {player.get('platform')}")
        
    # Show the simplified access pattern
    logger.info("\nSimplified Access Pattern for Flattened Response:")
    logger.info("  players = sdk.flatten_player_lookup_response(response)")
    logger.info("  for player in players:")
    logger.info("      # Directly access player data")
    logger.info("      player_uuid = player.get('player_uuid')")
    logger.info("      display_name = player.get('display_name')")
    
    return flattened

def example_rate_limit_handling():
    """
    Demonstrates the Enhanced Rate Limit Handling feature of the S2Match SDK.
    
    This example shows how to configure rate limit parameters and explains how
    exponential backoff works when encountering rate limits.
    """
    print("\n=== Enhanced Rate Limit Handling Example ===")
    
    # Initialize the SDK with custom rate limit parameters
    print("Initializing SDK with custom rate limit parameters...")
    sdk = S2Match(
        # Standard configuration parameters omitted for brevity
        
        # Rate limit configuration
        max_retries=5,              # Maximum number of retry attempts (default: 3)
        base_retry_delay=0.5,       # Initial delay in seconds (default: 1.0)
        max_retry_delay=30.0        # Maximum delay in seconds (default: 60.0)
    )
    
    print("\nRate Limit Configuration:")
    print(f"  - max_retries: {sdk.max_retries}")
    print(f"  - base_retry_delay: {sdk.base_retry_delay} seconds")
    print(f"  - max_retry_delay: {sdk.max_retry_delay} seconds")
    
    print("\nExponential Backoff Logic:")
    print("The SDK uses exponential backoff with jitter to handle rate limits.")
    print("Formula: min(base_delay * (2^retry_count), max_delay) ± jitter")
    
    print("\nExample Retry Delays:")
    for retry in range(6):
        delay = sdk.base_retry_delay * (2 ** retry)
        delay = min(delay, sdk.max_retry_delay)
        print(f"  - Retry #{retry+1}: ~{delay:.2f} seconds (before jitter)")
    
    print("\nHow it works:")
    print("1. If an API request receives a 429 (Too Many Requests) response:")
    print("   - The SDK will automatically wait using exponential backoff")
    print("   - It respects the Retry-After header if provided by the server")
    print("   - It will retry up to max_retries times before giving up")
    print("2. Requests that succeed reset the backoff counter")
    print("3. The SDK logs retry attempts with appropriate warning messages")
    
    print("\nPractical Example:")
    print("-" * 50)
    print("The following code demonstrates how rate limit handling works in practice.")
    print("Since we don't want to actually trigger rate limits on the API, this")
    print("is just a code example of how you would use the feature.")
    
    print("\n```python")
    print("# 1. Configure SDK with rate limit handling parameters")
    print("sdk = S2Match(")
    print("    max_retries=5,")
    print("    base_retry_delay=0.5,")
    print("    max_retry_delay=30.0")
    print(")")
    
    print("\n# 2. Make API requests normally - rate limit handling is automatic")
    print("try:")
    print("    # These requests will automatically retry if rate limited")
    print("    player_data = sdk.fetch_player_with_displayname(['PlayerName'])")
    print("    player_uuids = sdk.extract_player_uuids(player_data)")
    print("    if player_uuids:")
    print("        # If these requests hit rate limits, they'll use exponential backoff")
    print("        matches = sdk.get_matches_by_player_uuid(player_uuids[0])")
    print("        player_stats = sdk.get_player_stats(player_uuids[0])")
    print("except requests.exceptions.RequestException as e:")
    print("    # This exception is only raised if ALL retries failed")
    print("    print(f'Request failed after multiple retries: {e}')")
    print("```")
    
    print("\nObserving Rate Limit Handling:")
    print("-" * 50)
    print("To observe the rate limit handling in action:")
    print("1. Set the log level to DEBUG or INFO:")
    print("   ```python")
    print("   logging.getLogger('S2Match').setLevel(logging.DEBUG)")
    print("   ```")
    print("2. Make rapid requests to the API until you hit rate limits")
    print("3. Watch the logs for messages like:")
    print("   'Rate limit hit (429), retrying in 1.23 seconds. Attempt 1/5'")
    print("4. The SDK will automatically handle the retries with increasing delays")
    
    print("\nThis makes the SDK more resilient during high-volume requests.")
    
    # Advanced Monitoring (for completeness but commented out)
    # print("\nAdvanced Monitoring (Optional):")
    # print("You can access the rate limit state directly for monitoring:")
    # print("  - sdk._consecutive_rate_limits  # Number of consecutive rate limits")
    # print("  - sdk._last_retry_timestamp     # Timestamp of the last retry")

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
        
        # Example 6: Extract player UUIDs
        if ENABLE_EXTRACT_PLAYER_UUIDS:
            example_extract_player_uuids()
            logger.info("-" * 80)
        
        # Example 7: Filter matches
        if ENABLE_FILTER_MATCHES:
            example_filter_matches(player_uuid)
            logger.info("-" * 80)
        
        # Example 8: Player Performance Aggregation
        if ENABLE_PLAYER_PERFORMANCE:
            example_player_performance(player_uuid)
            logger.info("-" * 80)
        
        # Example 9: Flatten Player Lookup Response
        if ENABLE_FLATTEN_PLAYER_LOOKUP:
            example_flatten_player_lookup()
            logger.info("-" * 80)
        
        # Example 10: Rate Limit Handling
        if ENABLE_RATE_LIMIT_HANDLING:
            example_rate_limit_handling()
            logger.info("-" * 80)
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("Examples complete!")

if __name__ == "__main__":
    main() 