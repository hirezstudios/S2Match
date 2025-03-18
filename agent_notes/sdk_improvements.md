# S2Match SDK Improvement Suggestions

This document tracks specific code-level improvements we could make to the S2Match SDK based on insights gained during the Streamlit companion app development.

## Helper Methods

### 1. Extract Player UUIDs Helper

**Problem:** The player lookup response structure is deeply nested and hard to navigate to extract player UUIDs.

**Proposed Solution:**
```python
def extract_player_uuids(player_lookup_response):
    """
    Extract all player UUIDs from a player lookup response.
    
    Args:
        player_lookup_response: The response from fetch_player_with_displayname
        
    Returns:
        list: A list of player UUIDs
    """
    uuids = []
    display_names = player_lookup_response.get("display_names", [])
    for display_name_dict in display_names:
        for name, players in display_name_dict.items():
            for player in players:
                player_uuid = player.get("player_uuid")
                if player_uuid:
                    uuids.append(player_uuid)
    return uuids
```

### 2. Match Filtering Helper

**Problem:** There's no built-in way to filter matches by criteria like game mode, god, date range, etc.

**Proposed Solution:**
```python
def filter_matches(matches, filters=None):
    """
    Filter match data by various criteria.
    
    Args:
        matches: List of match data dictionaries
        filters: Dictionary of filter criteria, e.g.,
            {
                "god_name": "Anubis",
                "mode": "Conquest",
                "min_date": "2023-01-01",
                "max_date": "2023-12-31",
                "min_kills": 5,
                "min_kda": 2.0
            }
            
    Returns:
        list: Filtered list of match data dictionaries
    """
    if not filters:
        return matches
        
    filtered_matches = []
    
    for match in matches:
        include = True
        
        # Filter by god name
        if "god_name" in filters and match.get("god_name") != filters["god_name"]:
            include = False
            
        # Filter by game mode
        if "mode" in filters and match.get("mode") != filters["mode"]:
            include = False
            
        # Filter by date range
        if "min_date" in filters:
            import datetime
            start_ts = match.get("match_start")
            if start_ts:
                match_date = datetime.datetime.fromisoformat(start_ts.replace('Z', '+00:00'))
                min_date = datetime.datetime.fromisoformat(filters["min_date"])
                if match_date < min_date:
                    include = False
                    
        if "max_date" in filters:
            import datetime
            start_ts = match.get("match_start")
            if start_ts:
                match_date = datetime.datetime.fromisoformat(start_ts.replace('Z', '+00:00'))
                max_date = datetime.datetime.fromisoformat(filters["max_date"])
                if match_date > max_date:
                    include = False
        
        # Filter by performance stats
        basic_stats = match.get("basic_stats", {})
        
        if "min_kills" in filters and basic_stats.get("Kills", 0) < filters["min_kills"]:
            include = False
            
        if "min_kda" in filters:
            kills = basic_stats.get("Kills", 0)
            deaths = max(basic_stats.get("Deaths", 1), 1)  # Avoid division by zero
            assists = basic_stats.get("Assists", 0)
            kda = (kills + assists) / deaths
            if kda < filters["min_kda"]:
                include = False
                
        if include:
            filtered_matches.append(match)
            
    return filtered_matches
```

### 3. Player Performance Aggregation

**Problem:** Developers need to write their own code to calculate common player performance metrics.

**Proposed Solution:**
```python
def calculate_player_performance(matches):
    """
    Calculate aggregate performance metrics from a player's match history.
    
    Args:
        matches: List of match data dictionaries
        
    Returns:
        dict: Dictionary containing aggregate performance metrics
    """
    if not matches:
        return {}
        
    total_matches = len(matches)
    wins = 0
    kills = 0
    deaths = 0
    assists = 0
    damage = 0
    healing = 0
    
    god_stats = {}
    mode_stats = {}
    
    for match in matches:
        # Count wins
        if match.get("team_id") == match.get("winning_team"):
            wins += 1
            
        # Accumulate basic stats
        basic_stats = match.get("basic_stats", {})
        kills += basic_stats.get("Kills", 0)
        deaths += basic_stats.get("Deaths", 0)
        assists += basic_stats.get("Assists", 0)
        damage += basic_stats.get("TotalDamage", 0)
        healing += basic_stats.get("TotalAllyHealing", 0) + basic_stats.get("TotalSelfHealing", 0)
        
        # Track stats by god
        god_name = match.get("god_name")
        if god_name:
            if god_name not in god_stats:
                god_stats[god_name] = {
                    "matches": 0,
                    "wins": 0,
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0
                }
            
            god_stats[god_name]["matches"] += 1
            if match.get("team_id") == match.get("winning_team"):
                god_stats[god_name]["wins"] += 1
            god_stats[god_name]["kills"] += basic_stats.get("Kills", 0)
            god_stats[god_name]["deaths"] += basic_stats.get("Deaths", 0)
            god_stats[god_name]["assists"] += basic_stats.get("Assists", 0)
            
        # Track stats by game mode
        mode = match.get("mode")
        if mode:
            if mode not in mode_stats:
                mode_stats[mode] = {
                    "matches": 0,
                    "wins": 0
                }
            
            mode_stats[mode]["matches"] += 1
            if match.get("team_id") == match.get("winning_team"):
                mode_stats[mode]["wins"] += 1
    
    # Calculate averages and win rates
    avg_kills = kills / total_matches if total_matches > 0 else 0
    avg_deaths = deaths / total_matches if total_matches > 0 else 0
    avg_assists = assists / total_matches if total_matches > 0 else 0
    avg_kda = (kills + assists) / max(deaths, 1)
    win_rate = wins / total_matches if total_matches > 0 else 0
    
    # Calculate win rates by god and mode
    for god, stats in god_stats.items():
        stats["win_rate"] = stats["wins"] / stats["matches"] if stats["matches"] > 0 else 0
        stats["avg_kills"] = stats["kills"] / stats["matches"] if stats["matches"] > 0 else 0
        stats["avg_deaths"] = stats["deaths"] / stats["matches"] if stats["matches"] > 0 else 0
        stats["avg_assists"] = stats["assists"] / stats["matches"] if stats["matches"] > 0 else 0
        stats["avg_kda"] = (stats["kills"] + stats["assists"]) / max(stats["deaths"], 1)
        
    for mode, stats in mode_stats.items():
        stats["win_rate"] = stats["wins"] / stats["matches"] if stats["matches"] > 0 else 0
    
    return {
        "total_matches": total_matches,
        "wins": wins,
        "losses": total_matches - wins,
        "win_rate": win_rate,
        "avg_kills": avg_kills,
        "avg_deaths": avg_deaths,
        "avg_assists": avg_assists,
        "avg_kda": avg_kda,
        "total_kills": kills,
        "total_deaths": deaths,
        "total_assists": assists,
        "total_damage": damage,
        "total_healing": healing,
        "god_stats": god_stats,
        "mode_stats": mode_stats
    }
```

### 4. Flattened Player Lookup Response

**Problem:** The player lookup response structure is unnecessarily nested, making it hard to work with.

**Proposed Solution:**
```python
def flatten_player_lookup_response(response):
    """
    Flatten the player lookup response into a simple list of player objects.
    
    Args:
        response: The response from fetch_player_with_displayname
        
    Returns:
        list: A list of player dictionaries with display_name added
    """
    players = []
    
    display_names = response.get("display_names", [])
    for display_name_dict in display_names:
        for name, player_list in display_name_dict.items():
            for player in player_list:
                player_copy = player.copy()
                player_copy["display_name"] = name
                players.append(player_copy)
                
    return players
```

## Error Handling Improvements

### 1. Enhanced Rate Limit Handling

**Problem:** The current rate limiting strategy is basic and doesn't handle rate limit errors adaptively.

**Proposed Solution:**
```python
def _handle_rate_limiting(self, retry_count=0):
    """
    Apply rate limiting delay with exponential backoff for retries.
    
    Args:
        retry_count: The number of retry attempts so far
    """
    if retry_count == 0:
        # Standard delay for normal operation
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)
    else:
        # Exponential backoff for retries
        backoff_delay = min(self.rate_limit_delay * (2 ** retry_count), 30)
        logger.warning(f"Rate limit encountered, backing off for {backoff_delay} seconds")
        time.sleep(backoff_delay)
```

### 2. Input Parameter Validation

**Problem:** The SDK doesn't validate input parameters before making API calls, leading to unhelpful error messages.

**Proposed Solution:**
```python
def _validate_params(self, **kwargs):
    """
    Validate input parameters before making API calls.
    
    Args:
        **kwargs: Parameters to validate with their constraints
        
    Raises:
        ValueError: If any parameter fails validation
    """
    for param_name, constraints in kwargs.items():
        value = constraints.get("value")
        required = constraints.get("required", False)
        
        # Check required parameters
        if required and (value is None or (isinstance(value, str) and not value.strip())):
            raise ValueError(f"Parameter '{param_name}' is required but was not provided")
            
        # Skip further validation if value is None
        if value is None:
            continue
            
        # Type checking
        expected_type = constraints.get("type")
        if expected_type and not isinstance(value, expected_type):
            raise ValueError(f"Parameter '{param_name}' should be of type {expected_type.__name__}, got {type(value).__name__}")
            
        # Min/max value checking for numbers
        if isinstance(value, (int, float)):
            min_val = constraints.get("min")
            max_val = constraints.get("max")
            
            if min_val is not None and value < min_val:
                raise ValueError(f"Parameter '{param_name}' should be at least {min_val}, got {value}")
                
            if max_val is not None and value > max_val:
                raise ValueError(f"Parameter '{param_name}' should be at most {max_val}, got {value}")
                
        # List validation
        if isinstance(value, list):
            min_len = constraints.get("min_len")
            max_len = constraints.get("max_len")
            
            if min_len is not None and len(value) < min_len:
                raise ValueError(f"Parameter '{param_name}' should have at least {min_len} items, got {len(value)}")
                
            if max_len is not None and len(value) > max_len:
                raise ValueError(f"Parameter '{param_name}' should have at most {max_len} items, got {len(value)}")
```

## Future Work Items

1. Async versions of API methods for concurrent operations
2. Batch processing for multiple player lookup
3. Data export utilities (CSV, JSON)
4. More comprehensive error handling with specific error classes
5. Method for retrieving god/character metadata
6. Support for tournament/competitive match data 