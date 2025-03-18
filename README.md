# S2Match - SMITE 2 Match Data SDK

A Python SDK for external partners and community websites to access SMITE 2 match data through the RallyHere Environment API.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [SDK Options](#sdk-options)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
  - [Player Lookup](#player-lookup)
  - [Match Data](#match-data)
  - [Player Statistics](#player-statistics)
  - [Comprehensive Data](#comprehensive-data)
- [Response Formats](#response-formats)
- [Examples](#examples)
  - [Player Lookup](#example-player-lookup)
  - [Match History](#example-match-history)
  - [Player Statistics](#example-player-statistics)
  - [Full Player Data](#example-full-player-data)
- [Logging](#logging)
- [Error Handling](#error-handling)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Overview

S2Match provides a streamlined interface for retrieving and transforming SMITE 2 match data, player statistics, and related information. This SDK focuses exclusively on data retrieval and presentation, making it ideal for community websites, stat tracking applications, and esports analytics.

## Features

- **Authentication**: Simple token-based authentication with automatic refresh
- **Match Data**: Fetch detailed match history for players and specific matches
- **Player Stats**: Access player statistics and performance metrics
- **Player Lookup**: Find players by display name, platform, or other identifiers
- **Data Transformation**: Convert raw API responses into SMITE 2-friendly formats
- **Item Enrichment**: Automatically populate item details from local database
- **Caching**: Built-in response caching to improve performance and respect rate limits
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Rate Limiting Support**: Configurable delays between API calls to respect rate limits

## Installation

```bash
# Clone the repository
git clone https://github.com/YourOrg/S2Match.git
cd S2Match

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Environment Variables

The SDK uses the following environment variables:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `CLIENT_ID` | Environment API client ID | Yes | None |
| `CLIENT_SECRET` | Environment API client secret | Yes | None |
| `RH_BASE_URL` | Base URL for the Environment API | Yes | None |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | No | INFO |
| `CACHE_ENABLED` | Enable/disable response caching (true/false) | No | true |
| `RATE_LIMIT_DELAY` | Delay in seconds between API calls | No | 0 |

You can set these variables in three ways:

1. **System Environment Variables**
2. **`.env` File**: Create a `.env` file in your project root (use `env.template` as a starting point)
3. **Constructor Parameters**: Pass directly to the SDK constructor

### SDK Options

When initializing the SDK, you can configure the following options:

```python
sdk = S2Match(
    client_id="your_client_id",           # Override CLIENT_ID env var
    client_secret="your_client_secret",   # Override CLIENT_SECRET env var
    base_url="your_base_url",             # Override RH_BASE_URL env var
    cache_enabled=True,                   # Enable/disable response caching
    rate_limit_delay=0.5                  # Add delay between API calls (seconds)
)
```

## Quick Start

```python
from s2match import S2Match

# Initialize the SDK (using environment variables for credentials)
sdk = S2Match()

# Look up a player by display name
player_data = sdk.fetch_player_with_displayname(
    display_names=["Weak3n"],
    platform="Steam",
    include_linked_portals=True
)

# Get player UUID from the response
player_uuid = None
for display_name_dict in player_data.get("display_names", []):
    for name, players in display_name_dict.items():
        if players:
            player_uuid = players[0].get("player_uuid")
            break

# Get player match history
if player_uuid:
    # Get player statistics
    stats = sdk.get_player_stats(player_uuid)
    print(f"Total matches played: {stats.get('total_matches_played')}")
    
    # Get match history
    matches = sdk.get_matches_by_player_uuid(
        player_uuid=player_uuid,
        max_matches=5
    )
    
    # Display match information
    for match in matches:
        print(f"Match ID: {match.get('match_id')}")
        print(f"God: {match.get('god_name')}")
        print(f"K/D/A: {match['basic_stats'].get('Kills')}/{match['basic_stats'].get('Deaths')}/{match['basic_stats'].get('Assists')}")

# Get match data for a specific match instance
instance_id = "55b5f41a-0526-45fa-b992-b212fd12a849"
match_data = sdk.get_matches_by_instance(instance_id)

# Get comprehensive player data in a single call
full_data = sdk.get_full_player_data_by_displayname(
    platform="Steam",
    display_name="Weak3n",
    max_matches=5
)
```

## API Reference

### Player Lookup

#### `fetch_player_with_displayname(display_names, platform=None, include_linked_portals=True)`

Look up players by display name, optionally filtering by platform.

**Parameters:**
- `display_names`: List of display names to find
- `platform`: (Optional) Platform to look up by (e.g., "Steam", "XboxLive", "PSN")
- `include_linked_portals`: Whether to include linked portal data (default: True)

**Returns:** Dictionary containing player information

#### `fetch_player_by_platform_user_id(platform, platform_user_id)`

Find a player by platform identity.

**Parameters:**
- `platform`: Platform to search (e.g., "Steam", "XboxLive", "PSN")
- `platform_user_id`: The user's platform-specific ID

**Returns:** Dictionary with player information

### Match Data

#### `fetch_matches_by_player_uuid(player_uuid, page_size=10, max_matches=100)`

Fetch raw match data for the specified player.

**Parameters:**
- `player_uuid`: UUID of the player to fetch matches for
- `page_size`: Number of matches to retrieve per page (default: 10)
- `max_matches`: Maximum number of matches to retrieve in total (default: 100)

**Returns:** List of match data dictionaries (raw API format)

#### `fetch_matches_by_instance(instance_id, page_size=10)`

Fetch raw match data for a specific match instance.

**Parameters:**
- `instance_id`: Instance ID to fetch matches for
- `page_size`: Number of matches to retrieve per page (default: 10)

**Returns:** List of match dictionaries (raw API format)

#### `get_matches_by_player_uuid(player_uuid, page_size=10, max_matches=100)`

Fetch and transform match data for a specific player into SMITE 2 format.

**Parameters:**
- `player_uuid`: UUID of the player to fetch matches for
- `page_size`: Number of matches to retrieve per page (default: 10)
- `max_matches`: Maximum number of matches to retrieve in total (default: 100)

**Returns:** List of transformed match data dictionaries (SMITE 2 format)

#### `get_matches_by_instance(instance_id, page_size=10)`

Fetch and transform match data for a specific instance into SMITE 2 format.

**Parameters:**
- `instance_id`: Instance ID to fetch matches for
- `page_size`: Number of matches to retrieve per page (default: 10)

**Returns:** List of transformed match dictionaries (SMITE 2 format)

### Player Statistics

#### `fetch_player_stats(player_uuid)`

Fetch raw player statistics from RallyHere.

**Parameters:**
- `player_uuid`: UUID of the player to fetch stats for

**Returns:** Dictionary containing player statistics

#### `get_player_stats(player_uuid)`

Fetch player statistics in SMITE 2 format.

**Parameters:**
- `player_uuid`: UUID of the player to fetch stats for

**Returns:** Dictionary containing player statistics

### Comprehensive Data

#### `get_full_player_data_by_displayname(platform, display_name, max_matches=100)`

Fetch comprehensive player data including profile, stats, ranks, and match history.

**Parameters:**
- `platform`: Platform to search (e.g., "Steam", "XboxLive", "PSN")
- `display_name`: Display name of the player to look up
- `max_matches`: Maximum number of matches to retrieve per player (default: 100)

**Returns:** Dictionary containing consolidated player data

#### `fetch_player_ranks_by_uuid(token, player_uuid)`

Fetch and enrich a player's ranks from the RallyHere Environment API.

**Parameters:**
- `token`: Valid access token (usually handled internally)
- `player_uuid`: UUID of the player

**Returns:** Dictionary with rank information

## Response Formats

### Player Lookup Response

```python
{
    "display_names": [
        {
            "PlayerName": [
                {
                    "player_uuid": "uuid_string",
                    "player_id": 12345,
                    "platform": "Steam",
                    "linked_portals": [
                        {
                            "player_uuid": "linked_uuid_string",
                            "platform": "XboxLive",
                            # Additional portal details
                        }
                    ]
                }
            ]
        }
    ]
}
```

### Match Data Response

```python
[
    {
        "player_uuid": "uuid_string",
        "team_id": 1,
        "god_name": "Anubis",
        "match_id": "match_id_string",
        "match_start": "timestamp",
        "match_end": "timestamp",
        "map": "Conquest",
        "mode": "Ranked",
        "basic_stats": {
            "Kills": 10,
            "Deaths": 5,
            "Assists": 7,
            "TowerKills": 2,
            "PhoenixKills": 1,
            "TitanKills": 0,
            "TotalDamage": 25000,
            # Additional stats
        },
        "items": {
            "Slot1": {
                "Item_Id": "item_id_string",
                "DisplayName": "Item Name",
                # Full item details
            },
            # Additional slots
        },
        "damage_breakdown": {
            # Detailed damage information
        }
    }
]
```

### Player Statistics Response

```python
{
    "total_matches_played": 1055,
    "total_wins": 527,
    "total_losses": 528,
    "game_mode_stats": [
        {
            "mode": "Conquest",
            "matches_played": 850,
            "wins": 425,
            "losses": 425
        }
    ],
    # Additional statistics
}
```

### Full Player Data Response

```python
{
    "PlayerInfo": {
        # Player lookup data
    },
    "PlayerStats": [
        {
            "player_uuid": "uuid_string",
            "stats": {
                # Player statistics
            }
        }
    ],
    "PlayerRanks": [
        {
            "rank_id": "rank_id_string",
            "rank_name": "Diamond",
            "rank_description": "Diamond Tier",
            # Additional rank information
        }
    ],
    "MatchHistory": [
        # Match data entries
    ]
}
```

## Examples

### Example: Player Lookup

```python
from s2match import S2Match
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize SDK
sdk = S2Match()

# Look up a player by display name
player_data = sdk.fetch_player_with_displayname(
    display_names=["Weak3n"],
    platform="Steam",
    include_linked_portals=True
)

# Display player information
display_names = player_data.get("display_names", [])
if display_names:
    for display_name_dict in display_names:
        for name, players in display_name_dict.items():
            print(f"Results for '{name}':")
            for player in players:
                print(f"  Player UUID: {player.get('player_uuid')}")
                print(f"  Platform: {player.get('platform')}")
                linked_portals = player.get("linked_portals", [])
                print(f"  Linked portals: {len(linked_portals)}")
                for portal in linked_portals:
                    print(f"    - {portal.get('platform')}: {portal.get('player_uuid')}")
```

### Example: Match History

```python
from s2match import S2Match

# Initialize SDK
sdk = S2Match()

# Player UUID to fetch matches for
player_uuid = "e3438d31-c3ee-5377-b645-5a604b0e2b0e"

# Get player's match history
matches = sdk.get_matches_by_player_uuid(
    player_uuid=player_uuid,
    max_matches=5
)

# Display match information
print(f"Retrieved {len(matches)} matches:")
for i, match in enumerate(matches, 1):
    print(f"Match {i}:")
    print(f"  Match ID: {match.get('match_id')}")
    print(f"  God: {match.get('god_name')}")
    print(f"  Mode: {match.get('mode')}")
    print(f"  Map: {match.get('map')}")
    
    # Display basic stats
    if "basic_stats" in match:
        stats = match["basic_stats"]
        print(f"  K/D/A: {stats.get('Kills')}/{stats.get('Deaths')}/{stats.get('Assists')}")
        print(f"  Damage: {stats.get('TotalDamage')}")
        print(f"  Healing: {stats.get('TotalAllyHealing')}")
    
    # Display item builds
    if "items" in match:
        print("  Items:")
        for slot, item in match["items"].items():
            if isinstance(item, dict) and "DisplayName" in item:
                print(f"    {slot}: {item['DisplayName']}")
```

### Example: Player Statistics

```python
from s2match import S2Match

# Initialize SDK
sdk = S2Match()

# Player UUID to fetch stats for
player_uuid = "e3438d31-c3ee-5377-b645-5a604b0e2b0e"

# Get player statistics
stats = sdk.get_player_stats(player_uuid)

# Display stats information
print(f"Player Statistics:")
print(f"  Total matches played: {stats.get('total_matches_played', 'N/A')}")
print(f"  Total wins: {stats.get('total_wins', 'N/A')}")
print(f"  Total losses: {stats.get('total_losses', 'N/A')}")

# Display game mode stats if available
game_mode_stats = stats.get("game_mode_stats", [])
if game_mode_stats:
    print("  Game Mode Statistics:")
    for mode_stats in game_mode_stats:
        mode = mode_stats.get("mode", "Unknown")
        matches = mode_stats.get("matches_played", 0)
        wins = mode_stats.get("wins", 0)
        losses = mode_stats.get("losses", 0)
        print(f"    {mode}: {matches} matches, {wins} wins, {losses} losses")
```

### Example: Full Player Data

```python
from s2match import S2Match

# Initialize SDK
sdk = S2Match()

# Get comprehensive player data
full_data = sdk.get_full_player_data_by_displayname(
    platform="Steam",
    display_name="Weak3n",
    max_matches=5
)

# Display summary information
print("Player Data Summary:")
print(f"  Player UUIDs found: {len(full_data.get('PlayerStats', []))}")
print(f"  Rank records: {len(full_data.get('PlayerRanks', []))}")
print(f"  Match history records: {len(full_data.get('MatchHistory', []))}")

# Display rank information
if full_data.get("PlayerRanks"):
    print("\nRank Information:")
    for rank in full_data["PlayerRanks"]:
        print(f"  {rank.get('rank_name', 'Unknown')}: {rank.get('rank_description', 'No description')}")

# Print some match history information
if full_data.get("MatchHistory"):
    print("\nRecent Matches:")
    for i, match in enumerate(full_data["MatchHistory"][:3], 1):
        print(f"  Match {i}: {match.get('god_name')} - {match.get('mode')} - K/D/A: {match.get('basic_stats', {}).get('Kills', 0)}/{match.get('basic_stats', {}).get('Deaths', 0)}/{match.get('basic_stats', {}).get('Assists', 0)}")
```

## Logging

The SDK uses Python's built-in logging module. You can configure the log level via:

1. **Environment Variable**:
   ```
   LOG_LEVEL=DEBUG
   ```

2. **Programmatically**:
   ```python
   import logging
   logging.getLogger("S2Match").setLevel(logging.DEBUG)
   ```

Available log levels (from most to least verbose):
- `DEBUG`: Detailed information for debugging
- `INFO`: General operational information (default)
- `WARNING`: Indicates potential issues
- `ERROR`: Error conditions that might still allow the application to continue
- `CRITICAL`: Serious errors that may prevent further execution

## Error Handling

The SDK raises the following exceptions:

- `ValueError`: When required parameters are missing (e.g., credentials)
- `requests.exceptions.RequestException`: For HTTP errors, network issues, etc.
- `json.JSONDecodeError`: For invalid JSON responses

Example of proper error handling:

```python
from s2match import S2Match
import requests
import json

try:
    sdk = S2Match()
    player_data = sdk.fetch_player_with_displayname(["PlayerName"])
except ValueError as e:
    print(f"Configuration error: {e}")
except requests.exceptions.RequestException as e:
    print(f"Network or API error: {e}")
except json.JSONDecodeError as e:
    print(f"Invalid JSON response: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Optimization

To optimize SDK performance:

1. **Enable Caching**: The SDK caches responses by default to reduce API calls
   ```python
   sdk = S2Match(cache_enabled=True)  # Default is True
   ```

2. **Limit Results**: Request only the data you need
   ```python
   # Get only 5 matches instead of the default 100
   matches = sdk.get_matches_by_player_uuid(player_uuid, max_matches=5)
   ```

3. **Respect Rate Limits**: Add a delay between API calls
   ```python
   sdk = S2Match(rate_limit_delay=0.5)  # 500ms delay between API calls
   ```

4. **Use Comprehensive Methods**: The `get_full_player_data_by_displayname` method batches multiple API calls efficiently

## Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Verify CLIENT_ID and CLIENT_SECRET are correct
   - Check that RH_BASE_URL is correct and accessible
   - Ensure network connectivity to the API server

2. **No Data Returned**:
   - Verify the player UUID, display name, or match ID is correct
   - Check if the player or match exists in the system
   - Ensure you have access to the requested data

3. **Rate Limiting**:
   - Add rate_limit_delay to space out API calls
   - Implement backoff strategies for API failures

4. **Performance Issues**:
   - Enable caching to reduce repeated API calls
   - Limit the number of matches requested with max_matches

### Debugging

For detailed debugging information, set the log level to DEBUG:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("S2Match").setLevel(logging.DEBUG)
```

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Create a new Pull Request

Please ensure your code follows our coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Hi-Rez Studios for SMITE 2
- RallyHere for the Environment API
- All contributors and community members 