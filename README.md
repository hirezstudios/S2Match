# S2Match - SMITE 2 Match Data SDK

A Python SDK for external partners and community websites to access SMITE 2 match data through the RallyHere Environment API.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [SDK Options](#sdk-options)
- [RallyHere API Endpoints](#rallyhere-api-endpoints)
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
- [Streamlit Companion App](#streamlit-companion-app)
- [Logging](#logging)
- [Error Handling](#error-handling)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Enhanced Rate Limit Handling](#enhanced-rate-limit-handling)
- [GitHub Integration](#github-integration)

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
- **Interactive Companion App**: Streamlit-based web application for exploring SDK features
- **Retrieve player data by platform ID or display name**
- **Fetch match history for players**
- **Get player statistics**
- **Filter match data by god, game mode, date, performance metrics, and more**
- **Perform player performance analysis across matches**
- **Flatten complex player lookup responses for easier processing**
- **Enhanced rate limit handling with exponential backoff**
- **Response caching to reduce API calls**

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
    client_id="your_client_id",             # API client ID
    client_secret="your_client_secret",     # API client secret
    base_url="https://api.example.com",     # API base URL
    cache_enabled=True,                     # Enable response caching
    rate_limit_delay=0.0,                   # Fixed delay between API calls
    
    # Rate limit handling
    max_retries=3,                          # Maximum retry attempts for rate-limited requests
    base_retry_delay=1.0,                   # Initial delay in seconds before first retry
    max_retry_delay=60.0                    # Maximum delay in seconds between retries
)
```

All parameters are optional and can be provided via environment variables instead.

### Rate Limit Handling

The SDK features enhanced rate limit handling with exponential backoff:

- When a request receives a HTTP 429 (Too Many Requests) response, the SDK will automatically retry
- Retries use exponential backoff with jitter to space out requests
- The SDK respects the `Retry-After` header if provided by the server
- After `max_retries` attempts, the SDK will give up and raise an exception

The backoff delay is calculated as:
```
delay = min(base_retry_delay * (2^retry_count), max_retry_delay) ± jitter
```

This makes the SDK more resilient during high-volume requests and helps avoid overwhelming the API.

## Enhanced Rate Limit Handling

The S2Match SDK implements sophisticated rate limit handling to ensure your application remains responsive even when interacting with API limits.

### How It Works

When the SDK receives a rate limit response (HTTP 429 Too Many Requests) from the API:

1. It automatically retries the request using an exponential backoff strategy
2. Each retry increases the wait time between attempts
3. The SDK adds random jitter to prevent synchronized retries
4. The SDK respects any `Retry-After` header provided by the server
5. After reaching the maximum number of retries, the SDK will give up and raise an exception

### Configuration

You can configure the rate limit handling behavior when initializing the SDK:

```python
from s2match import S2Match

sdk = S2Match(
    # Standard configuration parameters
    client_id="your_client_id",
    client_secret="your_client_secret",
    base_url="your_base_url",
    
    # Rate limit configuration
    max_retries=3,              # Maximum retry attempts (default: 3)
    base_retry_delay=1.0,       # Initial delay in seconds (default: 1.0)
    max_retry_delay=60.0        # Maximum delay in seconds (default: 60.0)
)
```

### Backoff Algorithm

The backoff delay is calculated using this formula:

```
delay = min(base_retry_delay * (2^retry_count), max_retry_delay) ± jitter
```

Where:
- `base_retry_delay` is the initial delay (default: 1.0 seconds)
- `retry_count` is the current retry attempt (starting at 0)
- `max_retry_delay` is the maximum delay (default: 60.0 seconds)
- `jitter` is a random value of ±20% of the calculated delay

This creates a backoff pattern like this (with default settings):
- First retry: ~1.0 seconds
- Second retry: ~2.0 seconds
- Third retry: ~4.0 seconds
- Fourth retry: ~8.0 seconds
- ...and so on up to max_retry_delay

### Example Usage

The retry mechanism is automatic and built into all API requests. You don't need to write any special code to handle rate limits:

```python
# This code automatically handles rate limits
try:
    player_data = sdk.fetch_player_with_displayname(["PlayerName"])
    matches = sdk.get_matches_by_player_uuid(player_uuid)
except requests.exceptions.RequestException as e:
    # This will only be raised if all retries fail
    print(f"Failed after multiple retries: {e}")
```

### Logging

The SDK logs information about rate limit retries:
- Warning level log when a rate limit is hit and a retry is scheduled
- Error level log when max retries are exceeded

You can adjust the logging level to see more or less information:

```python
import logging
logging.getLogger("S2Match").setLevel(logging.DEBUG)
```

## RallyHere API Endpoints

The S2Match SDK interacts with the following RallyHere Environment API endpoints:

### Authentication
- **`/users/v2/oauth/token`** - Obtain access token for API requests

### Player Lookup
- **`/users/v1/player`** - Look up players by display name and platform
- **`/users/v1/player/{player_id}/linked_portals`** - Get linked portal accounts for a player
- **`/users/v1/platform-user`** - Find player by platform identity (e.g., Steam ID)

### Match Data
- **`/match/v1/player/{player_uuid}/match`** - Get match history for a specific player
- **`/match/v1/match`** - Get matches by instance ID

### Player Statistics
- **`/match/v1/player/{player_uuid}/stats`** - Get player statistics

### Ranking
- **`/rank/v2/player/{player_uuid}/rank`** - Get player's rank list
- **`/rank/v3/rank/{rank_id}`** - Get rank configuration
- **`/rank/v2/player/{player_uuid}/rank/{rank_id}`** - Get detailed rank information

The SDK handles all the authentication, request formatting, and response parsing for these endpoints, allowing you to work with a simplified API focused on SMITE 2 data.

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

# Get player UUID from the response using the helper method
player_uuids = sdk.extract_player_uuids(player_data)
player_uuid = player_uuids[0] if player_uuids else None

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

### Helper Methods

#### `extract_player_uuids(player_lookup_response)`

Extract all player UUIDs from a player lookup response. This simplifies the process of extracting player UUIDs from the nested response structure.

**Parameters:**
- `player_lookup_response`: The response from fetch_player_with_displayname

**Returns:** List of player UUIDs

#### `filter_matches(matches, filters=None)`

Filter match data by various criteria such as god name, game mode, date range, and performance metrics.

**Parameters:**
- `matches`: List of match data dictionaries
- `filters`: Dictionary of filter criteria, e.g.,
  ```python
  {
      "god_name": "Anubis",      # Filter by god/character
      "mode": "Conquest",        # Filter by game mode
      "map": "Conquest Map",     # Filter by map
      "min_date": "2023-01-01",  # Filter by minimum date
      "max_date": "2023-12-31",  # Filter by maximum date
      "min_kills": 5,            # Filter by minimum kills
      "min_kda": 2.0,            # Filter by minimum KDA ratio
      "win_only": True,          # Filter to only show wins
      "max_deaths": 5            # Filter by maximum deaths
  }
  ```

**Returns:** Filtered list of match data dictionaries

#### `calculate_player_performance(matches)`

Calculate comprehensive performance metrics from a player's match history data.

**Parameters:**
- `matches`: List of match data dictionaries

**Returns:** Dictionary containing detailed performance metrics including:

```python
{
    # Overall stats
    "total_matches": 25,       # Total number of matches played
    "wins": 15,                # Total wins
    "losses": 10,              # Total losses
    "win_rate": 0.6,           # Win rate (0.0-1.0)
    
    # Aggregated combat stats
    "total_kills": 250,        # Total kills across all matches
    "total_deaths": 150,       # Total deaths across all matches
    "total_assists": 300,      # Total assists across all matches
    "total_damage": 500000,    # Total damage dealt
    "total_healing": 100000,   # Total healing done
    # ... other total stats ...
    
    # Average stats
    "avg_kills": 10.0,         # Average kills per match
    "avg_deaths": 6.0,         # Average deaths per match
    "avg_assists": 12.0,       # Average assists per match
    "avg_kda": 3.67,           # Overall KDA ratio
    "avg_damage_per_match": 20000.0,  # Average damage per match
    # ... other average stats ...
    
    # Favorites and best performing
    "favorite_god": "Thor",    # Most played god
    "favorite_role": "Jungle", # Most played role
    "favorite_mode": "Conquest", # Most played game mode
    "best_performing_god": "Anubis", # God with highest KDA (min 3 matches)
    
    # Detailed stats by god/role/mode
    "god_stats": {
        "Thor": {
            "matches": 10,       # Matches played with this god
            "wins": 7,           # Wins with this god 
            "win_rate": 0.7,     # Win rate with this god
            "kills": 100,        # Total kills with this god
            "deaths": 50,        # Total deaths with this god
            "assists": 120,      # Total assists with this god
            "avg_kills": 10.0,   # Average kills per match
            "avg_deaths": 5.0,   # Average deaths per match
            "avg_assists": 12.0, # Average assists per match
            "avg_kda": 4.4       # KDA ratio with this god
        },
        # ... other gods ...
    },
    "mode_stats": {
        "Conquest": {
            "matches": 20,       # Matches played in this mode
            "wins": 12,          # Wins in this mode
            "win_rate": 0.6,     # Win rate in this mode
            # ... other mode-specific stats ...
        },
        # ... other modes ...
    },
    "role_stats": {
        "Jungle": {
            "matches": 15,       # Matches played in this role
            "wins": 10,          # Wins in this role
            "win_rate": 0.67,    # Win rate in this role
        },
        # ... other roles ...
    }
}
```

#### `flatten_player_lookup_response(response)`

Flatten the deeply nested player lookup response structure into a simple list of player objects.

**Parameters:**
- `response`: The response from fetch_player_with_displayname

**Returns:** List of player dictionaries with display_name added to each record

**Before (Raw Response):**
```python
{
    "display_names": [
        {
            "PlayerName": [
                {
                    "player_uuid": "uuid-1",
                    "player_id": 12345,
                    "platform": "Steam"
                }
            ]
        }
    ]
}
```

**After (Flattened Response):**
```python
[
    {
        "display_name": "PlayerName",
        "player_uuid": "uuid-1",
        "player_id": 12345,
        "platform": "Steam"
    }
]
```

This makes it much easier to iterate through players, filter player data, and display player information in UI components.

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

# Extract all player UUIDs using the helper method
player_uuids = sdk.extract_player_uuids(player_data)
print(f"\nExtracted {len(player_uuids)} player UUIDs using the helper method:")
for uuid in player_uuids:
    print(f"  {uuid}")
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

# Filter matches using the filter_matches helper method
print("\nFiltering matches:")

# Filter by god name
thor_matches = sdk.filter_matches(matches, {"god_name": "Thor"})
print(f"Found {len(thor_matches)} matches with Thor")

# Filter by KDA
high_kda_matches = sdk.filter_matches(matches, {"min_kda": 3.0})
print(f"Found {len(high_kda_matches)} matches with KDA >= 3.0")

# Filter wins only
winning_matches = sdk.filter_matches(matches, {"win_only": True})
print(f"Found {len(winning_matches)} winning matches")

# Combined filters
filtered_matches = sdk.filter_matches(matches, {
    "win_only": True,
    "min_kills": 10,
    "mode": "Conquest"
})
print(f"Found {len(filtered_matches)} winning Conquest matches with 10+ kills")
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

## Streamlit Companion App

The S2Match SDK includes an interactive Streamlit companion application that provides a user-friendly interface for exploring all SDK features.

> **Note**: The Streamlit companion app is currently a work in progress but already offers comprehensive functionality for exploring the SDK.

### Features

- **Home Page**: Overview of the SDK and configuration options
- **Player Lookup**: Search for players by display name across platforms
- **Match History**: View detailed match data with performance visualizations
- **Player Statistics**: Analyze player performance metrics with charts
- **Full Player Data**: Comprehensive view of all player-related data in one place
- **API Explorer**: Interactive interface for testing any SDK method directly

### Running the App

To run the Streamlit companion app:

```bash
# Install Streamlit dependencies
pip install -r streamlit_app/requirements.txt

# Run the app
streamlit run streamlit_app/Home.py
```

Or use the included shell script:

```bash
./run_streamlit_app.sh
```

The app will open in your default web browser at http://localhost:8501.

### Demo Mode

The companion app includes a demo mode that uses mock data if you don't have API credentials. This allows you to explore the interface and functionality without a live API connection.

When you're ready to use live data, enter your API credentials in the sidebar on the Home page and click "Initialize SDK".

### Screenshots

*Coming soon*

### Feedback

We welcome feedback on the Streamlit companion app as we continue to develop and improve it. Please submit issues or suggestions through the repository issue tracker.

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

## GitHub Integration

If you're collaborating on a project using this SDK, you can use the following Git commands to keep your repository up-to-date.

### Pushing Changes to GitHub

If you've made changes and want to update the GitHub repository:

```bash
# Add all modified files
git add .

# Commit your changes with a descriptive message
git commit -m "Add Enhanced Rate Limit Handling feature"

# Push changes to GitHub
git push origin main
```

### Pulling Latest Changes

To get the latest changes from the GitHub repository:

```bash
# Fetch the latest changes
git fetch

# Merge the changes into your local branch
git pull origin main
```

### Submitting Issues or Feature Requests

If you encounter issues or have ideas for improvements:

1. Visit the [GitHub Issues](https://github.com/YourOrg/S2Match/issues) page
2. Click "New Issue"
3. Provide a descriptive title and detailed description
4. Include code samples, log outputs, or screenshots if relevant

### Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Versioning and Releases

The SDK follows [Semantic Versioning](https://semver.org/):

- **Major version** (x.0.0): Incompatible API changes
- **Minor version** (0.x.0): Backwards-compatible functionality
- **Patch version** (0.0.x): Backwards-compatible bug fixes

Check the [Releases](https://github.com/YourOrg/S2Match/releases) page for the latest versions. 