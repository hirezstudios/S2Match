import os
import requests
import base64
import json
import logging
import time
from typing import Optional, List, Union, Dict, Any

# Configure logging - Improved setup to better handle LOG_LEVEL
log_level_str = os.getenv("LOG_LEVEL", "INFO")
log_level = getattr(logging, log_level_str.upper(), logging.INFO)

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("S2Match")
logger.setLevel(log_level)  # Explicitly set the logger level

class S2Match:
    """
    A Python SDK for external partners to interact with the RallyHere Environment API,
    providing access to SMITE 2 match data in a standardized format.
    
    This SDK focuses exclusively on retrieving and transforming match data,
    player statistics, and related information through the Environment API.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        cache_enabled: bool = True,
        rate_limit_delay: float = 0.0,
        max_retries: int = 3,
        base_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0
    ):
        """
        Initialize the S2Match SDK.

        Args:
            client_id: Client ID for Environment API. If not provided, uses env var CLIENT_ID.
            client_secret: Client secret for Environment API. If not provided, uses env var CLIENT_SECRET.
            base_url: Base URL for Environment API. If not provided, uses env var RH_BASE_URL.
            cache_enabled: Whether to enable response caching. Default is True.
            rate_limit_delay: Delay in seconds between API calls to avoid rate limiting. Default is 0.
            max_retries: Maximum number of retry attempts for rate-limited requests. Default is 3.
            base_retry_delay: Initial delay in seconds before first retry. Default is 1.0.
            max_retry_delay: Maximum delay in seconds between retries. Default is 60.0.
        """
        # Environment API credentials
        self.client_id = client_id or os.getenv("CLIENT_ID")
        self.client_secret = client_secret or os.getenv("CLIENT_SECRET")
        self.base_url = base_url or os.getenv("RH_BASE_URL")
        
        # SDK configuration
        self.cache_enabled = cache_enabled
        self.rate_limit_delay = rate_limit_delay
        self.cache = {} if cache_enabled else None
        
        # Rate limit handling configuration
        self.max_retries = max_retries
        self.base_retry_delay = base_retry_delay
        self.max_retry_delay = max_retry_delay
        
        # Rate limit state tracking
        self._consecutive_rate_limits = 0
        self._last_retry_timestamp = 0
        
        # Authentication state
        self._access_token = None
        self._token_expiry = 0
        
        # Basic validation
        if not self.client_id or not self.client_secret or not self.base_url:
            raise ValueError(
                "Missing environment credentials or base URL. "
                "Provide client_id/client_secret/base_url or set environment variables."
            )
        
        logger.info("S2Match SDK initialized successfully")
        
    def get_access_token(self) -> str:
        """
        Get a valid access token for the RallyHere Environment API.
        
        This method checks if there is a cached, non-expired token first.
        If not, it requests a new token from the API.
        
        Returns:
            str: A valid access token for API requests.
            
        Raises:
            requests.exceptions.RequestException: If the token request fails.
        """
        # Check if we have a valid token already
        current_time = time.time()
        if self._access_token and current_time < self._token_expiry:
            logger.debug("Using cached access token")
            return self._access_token
            
        # Get new token
        logger.info("Requesting new access token")
        creds = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(creds.encode()).decode()

        url = f"{self.base_url}/users/v2/oauth/token"
        headers = {
            "Authorization": f"Basic {encoded}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {"grant_type": "client_credentials"}

        try:
            # Use our new request wrapper
            resp = self._make_request_with_retry('post', url, json=payload, headers=headers, timeout=10)
            token_data = resp.json()
            
            self._access_token = token_data["access_token"]
            # Set expiry to 90% of actual expiry to be safe
            expiry_seconds = int(token_data.get("expires_in", 3600) * 0.9)
            self._token_expiry = current_time + expiry_seconds
            
            logger.info(f"Access token obtained, valid for ~{expiry_seconds} seconds")
            return self._access_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to obtain access token: {e}")
            raise
            
    def _handle_rate_limiting(self):
        """
        Apply rate limiting delay if configured.
        """
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)
            
    def _calculate_backoff_delay(self, retry_count: int) -> float:
        """
        Calculate the exponential backoff delay with random jitter for rate limit handling.
        
        This method implements an exponential backoff algorithm with jitter, which
        increases the delay between retry attempts exponentially (base * 2^retry_count)
        while adding random variation to prevent synchronized retries.
        
        The formula used is:
        delay = min(base_retry_delay * (2^retry_count), max_retry_delay) ± jitter
        
        Where jitter is a random value of ±20% of the calculated delay.
        
        Args:
            retry_count: Current retry attempt (0-based index)
            
        Returns:
            float: Delay in seconds before next retry, including jitter
        """
        import random
        # Calculate exponential backoff: base_delay * 2^retry_count
        delay = self.base_retry_delay * (2 ** retry_count)
        # Apply a maximum cap
        delay = min(delay, self.max_retry_delay)
        # Add random jitter (±20%)
        jitter = delay * 0.2 * (random.random() * 2 - 1)
        return delay + jitter
    
    def _make_request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request with automatic retry logic for rate limit errors.
        
        This method handles rate limits (HTTP 429) automatically using exponential
        backoff with jitter. When a rate limit is encountered, the method will:
        
        1. Calculate a delay based on the exponential backoff algorithm
        2. Respect any Retry-After header provided by the server
        3. Wait for the calculated delay
        4. Retry the request up to max_retries times
        
        The method tracks consecutive rate limits and resets the counter after 
        a successful request.
        
        Args:
            method: HTTP method ('get', 'post', etc.)
            url: Request URL
            **kwargs: Additional arguments to pass to the requests method
                (headers, json, params, etc.)
            
        Returns:
            requests.Response: The successful response from the API
            
        Raises:
            requests.exceptions.RequestException: If the request fails after max retries
                or encounters a non-rate-limit error
                
        Example:
            response = self._make_request_with_retry('get', url, headers=headers)
            data = response.json()
        """
        # Apply basic rate limiting
        self._handle_rate_limiting()
        
        # Get the appropriate request method
        request_method = getattr(requests, method.lower())
        
        # Make the initial request
        retry_count = 0
        while True:
            try:
                response = request_method(url, **kwargs)
                
                # If we got a 429, handle rate limiting
                if response.status_code == 429:
                    if retry_count >= self.max_retries:
                        logger.error(f"Rate limit exceeded after {retry_count} retries. Giving up.")
                        response.raise_for_status()  # This will raise an exception
                        
                    # Increment our consecutive rate limit counter
                    self._consecutive_rate_limits += 1
                    
                    # Calculate backoff delay
                    delay = self._calculate_backoff_delay(retry_count)
                    retry_count += 1
                    
                    # Get retry-after header if available
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            # If Retry-After is seconds
                            retry_seconds = float(retry_after)
                            # Use the larger of our calculated delay or the server's suggestion
                            delay = max(delay, retry_seconds)
                        except ValueError:
                            # If Retry-After is a date, we'll just use our calculated delay
                            pass
                            
                    logger.warning(
                        f"Rate limit hit (429), retrying in {delay:.2f} seconds. "
                        f"Attempt {retry_count}/{self.max_retries}"
                    )
                    
                    # Record the timestamp and sleep
                    self._last_retry_timestamp = time.time()
                    time.sleep(delay)
                    continue  # Retry the request
                
                # If we get here, the request succeeded (no 429)
                # Reset consecutive rate limit counter
                self._consecutive_rate_limits = 0
                
                # Check for other error status codes
                response.raise_for_status()
                
                return response
                
            except requests.exceptions.RequestException as e:
                # If it's not a rate limit error or we've exceeded retries, re-raise
                if retry_count >= self.max_retries:
                    logger.error(f"Request failed after {retry_count} retries: {e}")
                    raise
                
                # Check if this is a rate limit exception
                is_rate_limit = False
                if isinstance(e, requests.exceptions.HTTPError):
                    if hasattr(e, 'response') and getattr(e.response, 'status_code', 0) == 429:
                        is_rate_limit = True
                
                if not is_rate_limit:
                    # If it's not a rate limit error, re-raise
                    logger.error(f"Request failed with non-rate-limit error: {e}")
                    raise
                
                # For rate limit exceptions during retry, continue the retry loop
                retry_count += 1
            
    def fetch_matches_by_player_uuid(
        self,
        player_uuid: str,
        page_size: int = 10,
        max_matches: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch match data for the specified player from RallyHere.
        
        Args:
            player_uuid: The UUID of the player to fetch matches for.
            page_size: Number of matches to retrieve per page. Default is 10.
            max_matches: Maximum number of matches to retrieve in total. Default is 100.
            
        Returns:
            List[Dict[str, Any]]: A list of match data dictionaries.
            
        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        logger.info(f"Fetching matches for player UUID: {player_uuid}")
        matches = []
        cursor = None
        token = self.get_access_token()
        
        cache_key = f"matches_player_{player_uuid}_{page_size}_{max_matches}"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug(f"Using cached match data for player {player_uuid}")
            return self.cache[cache_key]

        while len(matches) < max_matches:
            url = f"{self.base_url}/match/v1/player/{player_uuid}/match?page_size={page_size}"
            if cursor:
                url += f"&cursor={cursor}"

            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {token}'
            }

            try:
                # Use our new request wrapper with retry logic
                response = self._make_request_with_retry('get', url, headers=headers)
                data = response.json()

                matches.extend(data.get("player_matches", []))
                cursor = data.get("cursor")

                if not cursor:
                    break
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching matches: {e}")
                raise

        result = matches[:max_matches]
        
        if self.cache_enabled:
            self.cache[cache_key] = result
            
        logger.info(f"Fetched {len(result)} matches for player {player_uuid}")
        return result
        
    def fetch_player_stats(self, player_uuid: str) -> Dict[str, Any]:
        """
        Fetch player statistics from RallyHere using the /stats endpoint.
        
        Args:
            player_uuid: The UUID of the player to fetch stats for.
            
        Returns:
            Dict[str, Any]: A dictionary containing player statistics.
            
        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        logger.info(f"Fetching stats for player UUID: {player_uuid}")
        token = self.get_access_token()
        
        cache_key = f"stats_player_{player_uuid}"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug(f"Using cached stats data for player {player_uuid}")
            return self.cache[cache_key]
            
        self._handle_rate_limiting()
        
        url = f"{self.base_url}/match/v1/player/{player_uuid}/stats"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if self.cache_enabled:
                self.cache[cache_key] = data
                
            logger.info(f"Fetched stats for player {player_uuid}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching player stats: {e}")
            raise
            
    def fetch_matches_by_instance(
        self,
        instance_id: str,
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch match data filtered by instance_id from RallyHere.
        
        Args:
            instance_id: The instance ID to fetch matches for.
            page_size: Number of matches to retrieve per page. Default is 10.
            
        Returns:
            List[Dict[str, Any]]: A list of match dictionaries.
            
        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        logger.info(f"Fetching matches for instance ID: {instance_id}")
        matches = []
        cursor = None
        token = self.get_access_token()
        
        cache_key = f"matches_instance_{instance_id}_{page_size}"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug(f"Using cached match data for instance {instance_id}")
            return self.cache[cache_key]

        # Try with instance_id parameter
        url = f"{self.base_url}/match/v1/match?instance_id={instance_id}&page_size={page_size}"
        logger.debug(f"Request URL: {url}")
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        try:
            self._handle_rate_limiting()
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            matches.extend(data.get("matches", []))
            cursor = data.get("cursor")
            
            # Continue fetching if there's a cursor
            while cursor:
                self._handle_rate_limiting()
                next_url = f"{self.base_url}/match/v1/match?instance_id={instance_id}&page_size={page_size}&cursor={cursor}"
                response = requests.get(next_url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                matches.extend(data.get("matches", []))
                cursor = data.get("cursor")
                
            logger.info(f"Fetched {len(matches)} matches for instance {instance_id}")
            
            if self.cache_enabled:
                self.cache[cache_key] = matches
                
            return matches
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching matches by instance: {e}")
            raise
            
    def fetch_player_by_platform_user_id(
        self,
        platform: str,
        platform_user_id: str
    ) -> Dict[str, Any]:
        """
        Find an existing platform user via platform identity.
        
        Args:
            platform: Platform to search (e.g., 'XboxLive', 'PSN', 'Steam', etc.).
            platform_user_id: The user's platform-specific ID.
            
        Returns:
            Dict[str, Any]: A dictionary with fields including platform, platform_user_id, 
                           display_name, player_uuid, etc.
                           
        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        logger.info(f"Fetching player by platform {platform} with user ID: {platform_user_id}")
        token = self.get_access_token()
        
        cache_key = f"player_platform_{platform}_{platform_user_id}"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug(f"Using cached player data for {platform} user {platform_user_id}")
            return self.cache[cache_key]
            
        self._handle_rate_limiting()
        
        url = f"{self.base_url}/users/v1/platform-user"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        params = {
            "platform": platform,
            "platform_user_id": platform_user_id
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if self.cache_enabled:
                self.cache[cache_key] = data
                
            logger.info(f"Fetched player data for {platform} user {platform_user_id}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching player by platform user ID: {e}")
            raise
            
    def fetch_player_with_displayname(
        self,
        display_names: List[str],
        platform: Optional[str] = None,
        include_linked_portals: bool = True
    ) -> Dict[str, Any]:
        """
        Lookup one or more players by display name and optionally by platform.
        Optionally fetch their linked_portals data in the consolidated response.
        
        Args:
            display_names: List of display names to find.
            platform: (Optional) Platform to look up by (case-sensitive: e.g., "Steam").
            include_linked_portals: Whether to include linked portal data. Default is True.
            
        Returns:
            Dict[str, Any]: Data containing player information.
            
        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        display_names_str = ",".join(display_names)
        logger.info(f"Fetching players with display names: {display_names_str}")
        token = self.get_access_token()
        
        cache_key = f"player_displayname_{display_names_str}_{platform}_{include_linked_portals}"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug(f"Using cached player data for display names {display_names_str}")
            return self.cache[cache_key]
            
        # Step 1: Call the main endpoint to find players by display name / platform
        self._handle_rate_limiting()
        url = f"{self.base_url}/users/v1/player"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        params = {}
        if display_names:
            params["display_name"] = display_names
        if platform:
            params["platform"] = platform
            
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            base_result = response.json()

            # If we do not want the linked portals, just return what we got
            if not include_linked_portals:
                if self.cache_enabled:
                    self.cache[cache_key] = base_result
                    
                logger.info(f"Fetched player data for display names {display_names_str} (without linked portals)")
                return base_result

            # Helper method to fetch linked portals for a single player_id
            def _fetch_linked_portals(pid: int) -> list:
                self._handle_rate_limiting()
                linked_url = f"{self.base_url}/users/v1/player/{pid}/linked_portals"
                resp = requests.get(linked_url, headers=headers)
                resp.raise_for_status()
                portals_json = resp.json()
                # Typically returns something like { "linked_portals": [ {...}, ... ] }
                return portals_json.get("linked_portals", [])

            # Step 2: For each player, also fetch linked portals and nest that data
            display_names_list = base_result.get("display_names", [])
            for display_name_dict in display_names_list:
                for display_name, player_array in display_name_dict.items():
                    for player_obj in player_array:
                        pid = player_obj.get("player_id")
                        if pid is not None:
                            # fetch linked portals
                            try:
                                lp = _fetch_linked_portals(pid)
                                # attach to our original data structure
                                player_obj["linked_portals"] = lp
                            except requests.exceptions.RequestException as e:
                                # If there's an error, we store an empty list and an error note
                                player_obj["linked_portals"] = []
                                player_obj["linked_portals_error"] = str(e)
                                logger.warning(f"Error fetching linked portals for player {pid}: {e}")

            if self.cache_enabled:
                self.cache[cache_key] = base_result
                
            logger.info(f"Fetched player data for display names {display_names_str} (with linked portals)")
            return base_result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching player by display name: {e}")
            raise
    
    # -------------------------------------------------------------------------
    # SMITE 2: Transformations
    # -------------------------------------------------------------------------
    def transform_player(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single player's record from RallyHere's native format
        into a SMITE 2–friendly format.
        
        Args:
            player_data: Raw player data from RallyHere API.
            
        Returns:
            Dict[str, Any]: Transformed player data in SMITE 2-friendly format.
        """
        logger.debug(f"Transforming player data for player {player_data.get('player_uuid')}")
        
        # Ensure we have a valid custom_data dict
        custom_data = player_data.get("custom_data", {}) or {}

        transformed = {
            "player_uuid": player_data.get("player_uuid"),
            "team_id": player_data.get("team_id"),
            "placement": player_data.get("placement"),
            "joined_match_timestamp": player_data.get("joined_match_timestamp"),
            "left_match_timestamp": player_data.get("left_match_timestamp"),
            "duration_seconds": player_data.get("duration_seconds"),
        }

        # God / Character
        character_choice = custom_data.get("CharacterChoice", "")
        if character_choice and character_choice.startswith("Gods."):
            god_name = character_choice.split(".", 1)[1]
        else:
            god_name = character_choice or "UnknownGod"
        transformed["god_name"] = god_name

        # Convert certain keys to int
        basic_stats_keys = [
            "Kills", "Deaths", "Assists", "TowerKills", "PhoenixKills", "TitanKills",
            "TotalDamage", "TotalNPCDamage", "TotalDamageTaken", "TotalDamageMitigated",
            "TotalGoldEarned", "TotalXPEarned", "TotalStructureDamage", "TotalMinionDamage",
            "TotalAllyHealing", "TotalSelfHealing", "TotalWardsPlaced", "PlayerLevel"
        ]
        basic_stats = {}
        for stat_key in basic_stats_keys:
            raw_val = custom_data.get(stat_key)
            basic_stats[stat_key] = int(raw_val) if (raw_val and isinstance(raw_val, str) and raw_val.isdigit()) else 0
        transformed["basic_stats"] = basic_stats

        # Role info
        transformed["assigned_role"] = custom_data.get("AssignedRole")
        transformed["played_role"] = custom_data.get("PlayedRole")

        # Potentially parse JSON fields (e.g., items)
        items_str = custom_data.get("Items")
        if items_str:
            try:
                transformed["items"] = json.loads(items_str)
            except (json.JSONDecodeError, TypeError):
                transformed["items"] = {}
        else:
            transformed["items"] = {}
            
        role_prefs_str = custom_data.get("RolePreferences")
        if role_prefs_str:
            try:
                transformed["role_preferences"] = json.loads(role_prefs_str)
            except (json.JSONDecodeError, TypeError):
                transformed["role_preferences"] = {}
        else:
            transformed["role_preferences"] = {}

        # Damage breakdown
        damage_breakdown = {}
        for key, raw_val in custom_data.items():
            if not isinstance(raw_val, str):
                continue
            if not raw_val.isdigit():
                continue

            if key.startswith("Gods."):
                segments = key.split(".")
                if len(segments) >= 3:
                    god_part = segments[1]
                    stat_part = ".".join(segments[2:])
                    damage_breakdown.setdefault(god_part, {})
                    damage_breakdown[god_part][stat_part] = int(raw_val)
            elif key.startswith("Items."):
                segments = key.split(".")
                if len(segments) == 3:
                    _, item_name, item_stat = segments
                    damage_breakdown.setdefault(item_name, {})
                    damage_breakdown[item_name][item_stat] = int(raw_val)
                else:
                    item_name = segments[1] if len(segments) > 1 else "UnknownItem"
                    damage_breakdown.setdefault(item_name, {})
                    damage_breakdown[item_name]["value"] = int(raw_val)
            elif key.startswith("NPC.") or key.startswith("Ability.Type.Item"):
                damage_breakdown.setdefault("Misc", {})
                damage_breakdown["Misc"][key] = int(raw_val)
            else:
                damage_breakdown.setdefault("misc_stats", {})
                damage_breakdown["misc_stats"][key] = int(raw_val)

        transformed["damage_breakdown"] = damage_breakdown

        return transformed

    def transform_matches(self, rh_matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform a list of player match records from RallyHere's native format
        into a SMITE 2-friendly format.
        
        Args:
            rh_matches: List of raw match data from RallyHere API.
            
        Returns:
            List[Dict[str, Any]]: Transformed match data in SMITE 2-friendly format.
        """
        logger.info(f"Transforming {len(rh_matches)} matches to SMITE 2 format")
        s2_matches = []
        for record in rh_matches:
            player_transformed = self.transform_player(record)

            # Additional match-level fields
            match_info = record.get("match", {})
            match_custom = match_info.get("custom_data", {})

            player_transformed["match_id"] = match_info.get("match_id")
            player_transformed["match_start"] = match_info.get("start_timestamp")
            player_transformed["match_end"] = match_info.get("end_timestamp")
            player_transformed["map"] = match_custom.get("CurrentMap")
            player_transformed["mode"] = match_custom.get("CurrentMode")
            player_transformed["lobby_type"] = match_custom.get("LobbyType")
            player_transformed["winning_team"] = match_custom.get("WinningTeam")

            s2_matches.append(player_transformed)

        # Enrich matches with item data
        s2_matches = self._enrich_matches_with_item_data(s2_matches)
        return s2_matches

    def transform_matches_by_instance(self, rh_matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform raw instance-based match data from RallyHere into a SMITE 2-friendly format.
        
        Args:
            rh_matches: List of raw match data from RallyHere API.
            
        Returns:
            List[Dict[str, Any]]: Transformed match data in SMITE 2-friendly format.
        """
        logger.info(f"Transforming {len(rh_matches)} instance-based matches to SMITE 2 format")
        s2_matches = []

        for match_info in rh_matches:
            match_id = match_info.get("match_id")
            start_ts = match_info.get("start_timestamp")
            end_ts = match_info.get("end_timestamp")
            duration_seconds = match_info.get("duration_seconds")
            custom_data = match_info.get("custom_data", {}) or {}  # Ensure custom_data is a dict

            s2_match = {
                "match_id": match_id,
                "start_timestamp": start_ts,
                "end_timestamp": end_ts,
                "duration_seconds": duration_seconds,
                "map": custom_data.get("CurrentMap", "Unknown"),
                "mode": custom_data.get("CurrentMode", "Unknown"),
                "lobby_type": custom_data.get("LobbyType", "Unknown"),
                "winning_team": custom_data.get("WinningTeam"),
                "segments": [],
                "final_players": []
            }

            # Transform each segment
            segments = match_info.get("segments", [])
            for seg in segments:
                segment_label = seg.get("match_segment")
                seg_start = seg.get("start_timestamp")
                seg_end = seg.get("end_timestamp")
                seg_duration = seg.get("duration_seconds")

                seg_players = seg.get("players", [])
                transformed_players = [self.transform_player(p) for p in seg_players]

                s2_segment = {
                    "segment_label": segment_label,
                    "start_timestamp": seg_start,
                    "end_timestamp": seg_end,
                    "duration_seconds": seg_duration,
                    "players": transformed_players
                }
                s2_match["segments"].append(s2_segment)

            # top-level "players" if it exists
            top_level_players = match_info.get("players", [])
            s2_final_players = [self.transform_player(p) for p in top_level_players]
            s2_match["final_players"] = s2_final_players

            s2_matches.append(s2_match)

        # Enrich matches with item data
        s2_matches = self._enrich_matches_with_item_data(s2_matches)
        return s2_matches

    def _enrich_matches_with_item_data(self, s2_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        For each entity (match record or player record) in s2_data, replace
        the 'items' IDs with full item data from items.json.
        
        Args:
            s2_data: List of match/player records to enrich.
            
        Returns:
            List[Dict[str, Any]]: Enriched data with full item details.
        """
        logger.debug(f"Enriching {len(s2_data)} records with item data")
        item_map = self._load_items_map()

        if not s2_data:
            return s2_data

        first = s2_data[0]
        if isinstance(first, dict):
            # If it has segments/final_players, assume instance-based match shape
            if "segments" in first and "final_players" in first:
                for match in s2_data:
                    # handle top-level players
                    for player in match.get("final_players", []):
                        self._replace_item_ids(player, item_map)
                    # handle segment-based players
                    for segment in match.get("segments", []):
                        for player in segment.get("players", []):
                            self._replace_item_ids(player, item_map)
            else:
                # Otherwise, assume it's a list of player records (player-based shape).
                for player_record in s2_data:
                    self._replace_item_ids(player_record, item_map)

        return s2_data

    def _replace_item_ids(self, player: Dict[str, Any], item_map: Dict[str, Any]) -> None:
        """
        Given a single player's dictionary, replace each item ID in player["items"]
        with a fully described item node from the item_map.
        
        Args:
            player: Player data dictionary to update.
            item_map: Dictionary mapping item IDs to full item data.
        """
        items_dict = player.get("items", {})
        for slot_key, item_id in list(items_dict.items()):
            # If the item ID is in our map, replace the string ID with the full item data
            if item_id in item_map:
                items_dict[slot_key] = item_map[item_id]
            else:
                # Provide a lightweight fallback structure with placeholder display name
                items_dict[slot_key] = {
                    "Item_Id": item_id,
                    "DisplayName": "<display name missing>"
                }

    def _load_items_map(self) -> Dict[str, Any]:
        """
        Load items.json from disk, creating a dictionary mapping
        Item_Id -> item data object.
        
        Returns:
            Dict[str, Any]: Dictionary mapping item IDs to full item data.
            
        Raises:
            FileNotFoundError: If items.json can't be found.
            json.JSONDecodeError: If items.json is not valid JSON.
        """
        # Adjust this path to wherever your items.json file lives:
        items_json_path = os.path.join(os.path.dirname(__file__), "items.json")

        try:
            with open(items_json_path, "r", encoding="utf-8") as f:
                items_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading items.json: {e}")
            return {}

        # Build a map of { "0000000000000000000000000000009F": {...full item data...}, ... }
        item_map = {}
        for item_obj in items_data:
            item_id = item_obj.get("Item_Id")
            if item_id:
                item_map[item_id] = item_obj
        return item_map
        
    # -------------------------------------------------------------------------
    # SMITE 2: High-level Methods
    # -------------------------------------------------------------------------
    def get_matches_by_player_uuid(
        self,
        player_uuid: str,
        page_size: int = 10,
        max_matches: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch and transform match data for a specific player.
        
        This method fetches raw match data and then transforms it
        into a SMITE 2-friendly format with enriched item data.
        
        Args:
            player_uuid: The UUID of the player to fetch matches for.
            page_size: Number of matches to retrieve per page. Default is 10.
            max_matches: Maximum number of matches to retrieve in total. Default is 100.
            
        Returns:
            List[Dict[str, Any]]: Transformed match data in SMITE 2-friendly format.
            
        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        logger.info(f"Getting SMITE 2 match data for player UUID: {player_uuid}")
        
        cache_key = f"s2_matches_player_{player_uuid}_{page_size}_{max_matches}"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug(f"Using cached S2 match data for player {player_uuid}")
            return self.cache[cache_key]
            
        # First get the raw match data
        rh_matches = self.fetch_matches_by_player_uuid(player_uuid, page_size, max_matches)
        
        # Transform the raw data into SMITE 2–friendly structures
        s2_players = self.transform_matches(rh_matches)
        
        if self.cache_enabled:
            self.cache[cache_key] = s2_players
            
        return s2_players
        
    def get_player_stats(self, player_uuid: str) -> Dict[str, Any]:
        """
        Fetch player statistics in SMITE 2 format.
        
        This is a simple wrapper around fetch_player_stats as the stats endpoint
        returns minimal fields that don't need transformation.
        
        Args:
            player_uuid: The UUID of the player to fetch stats for.
            
        Returns:
            Dict[str, Any]: Player statistics.
            
        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        logger.info(f"Getting SMITE 2 player stats for UUID: {player_uuid}")
        return self.fetch_player_stats(player_uuid)
        
    def get_matches_by_instance(
        self,
        instance_id: str,
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch and transform match data for a specific instance ID.
        
        Args:
            instance_id: The instance ID to fetch matches for.
            page_size: Number of matches to retrieve per page. Default is 10.
            
        Returns:
            List[Dict[str, Any]]: Transformed match data in SMITE 2-friendly format.
            
        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        logger.info(f"Getting SMITE 2 match data for instance ID: {instance_id}")
        
        cache_key = f"s2_matches_instance_{instance_id}_{page_size}"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug(f"Using cached S2 match data for instance {instance_id}")
            return self.cache[cache_key]
            
        # First get the raw match data
        rh_matches = self.fetch_matches_by_instance(instance_id, page_size)
        
        # Check if we got any data
        if not rh_matches:
            logger.warning(f"No match data found for instance ID {instance_id}")
            return []
            
        # Transform the raw data into SMITE 2–friendly structures
        s2_matches = self.transform_matches_by_instance(rh_matches)
        
        if self.cache_enabled:
            self.cache[cache_key] = s2_matches
            
        return s2_matches
        
    def get_full_player_data_by_displayname(
        self,
        platform: str,
        display_name: str,
        max_matches: int = 100
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive player data including profiles, stats, and match history.
        
        This method consolidates multiple API calls to provide a complete picture
        of a player's data in SMITE 2 format.
        
        Args:
            platform: Platform to search (e.g., 'XboxLive', 'PSN', 'Steam', etc.).
            display_name: The display name of the player to look up.
            max_matches: Maximum number of matches to retrieve per player. Default is 100.
            
        Returns:
            Dict[str, Any]: Consolidated player data including profile info, stats, 
                           ranks, and match history.
            
        Raises:
            requests.exceptions.RequestException: If any API request fails.
        """
        logger.info(f"Getting full SMITE 2 player data for {platform} player: {display_name}")
        
        cache_key = f"s2_full_player_{platform}_{display_name}_{max_matches}"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug(f"Using cached full S2 player data for {display_name}")
            return self.cache[cache_key]
            
        token = self.get_access_token()
        
        # Get the base "player info" data (including linked portals)
        player_info = self.fetch_player_with_displayname(
            display_names=[display_name],
            platform=platform,
            include_linked_portals=True
        )
        
        # Gather all player_uuids (including linked portals)
        all_player_uuids = set()
        for display_name_dict in player_info.get("display_names", []):
            for _, player_array in display_name_dict.items():
                for player_obj in player_array:
                    main_uuid = player_obj.get("player_uuid")
                    if main_uuid:
                        all_player_uuids.add(main_uuid)
                    for lp in player_obj.get("linked_portals", []):
                        lp_uuid = lp.get("player_uuid")
                        if lp_uuid:
                            all_player_uuids.add(lp_uuid)
        
        combined_data = {
            "PlayerInfo": player_info,
            "PlayerStats": [],
            "PlayerRanks": [],
            "MatchHistory": []
        }
        
        # For each UUID found, fetch stats, ranks & match history
        for uuid_val in all_player_uuids:
            # Fetch and transform player stats
            stats_data = self.get_player_stats(uuid_val)
            
            # Fetch and transform matches
            matches_data = self.get_matches_by_player_uuid(uuid_val, max_matches=max_matches)
            
            # Add to combined data
            combined_data["PlayerStats"].append({
                "player_uuid": uuid_val,
                "stats": stats_data
            })
            combined_data["MatchHistory"].extend(matches_data)
            
            # Fetch rank data if available
            try:
                ranks_data = self.fetch_player_ranks_by_uuid(token, uuid_val)
                # The response typically includes {"player_ranks": [ ... ]}, so we grab that list
                combined_data["PlayerRanks"].extend(ranks_data.get("player_ranks", []))
            except Exception as e:
                logger.warning(f"Error fetching rank data for player {uuid_val}: {e}")
                # Continue processing other data even if ranks fail
        
        if self.cache_enabled:
            self.cache[cache_key] = combined_data
            
        return combined_data
    
    def fetch_player_ranks_by_uuid(
        self,
        token: str,
        player_uuid: str
    ) -> Dict[str, Any]:
        """
        Fetch and enrich a player's ranks from the RallyHere Environment API.
        
        Args:
            token: A valid access token.
            player_uuid: The UUID of the player.
            
        Returns:
            Dict[str, Any]: Enriched rank data.
            
        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        logger.info(f"Fetching ranks for player UUID: {player_uuid}")
        
        cache_key = f"ranks_player_{player_uuid}"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug(f"Using cached rank data for player {player_uuid}")
            return self.cache[cache_key]
            
        # Step 1a: Fetch the player's rank list
        self._handle_rate_limiting()
        list_url = f"{self.base_url}/rank/v2/player/{player_uuid}/rank"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        try:
            list_resp = requests.get(list_url, headers=headers)
            list_resp.raise_for_status()
            
            data = list_resp.json()  # Expected shape: {"player_ranks": [...]}
            player_ranks = data.get("player_ranks", [])
            
            # Step 1b & 1c: Fetch additional rank data
            for rank_obj in player_ranks:
                rank_id = rank_obj.get("rank_id")
                if rank_id:
                    # Fetch rank config
                    self._handle_rate_limiting()
                    config_url = f"{self.base_url}/rank/v3/rank/{rank_id}"
                    config_resp = requests.get(config_url, headers=headers)
                    config_resp.raise_for_status()
                    config_data = config_resp.json()
                    
                    configs_list = config_data.get("rank_configs", [])
                    if configs_list:
                        rank_info = configs_list[0]
                        rank_obj["rank_name"] = rank_info.get("name")
                        rank_obj["rank_description"] = rank_info.get("description")
                    else:
                        rank_obj["rank_name"] = "<no_config>"
                        rank_obj["rank_description"] = "<no_config>"
                    
                    # Fetch single rank data
                    self._handle_rate_limiting()
                    single_rank_url = f"{self.base_url}/rank/v2/player/{player_uuid}/rank/{rank_id}"
                    single_resp = requests.get(single_rank_url, headers=headers)
                    single_resp.raise_for_status()
                    single_data = single_resp.json()
                    
                    sr_list = single_data.get("player_ranks", [])
                    if sr_list:
                        # Typically only one rank object in this array
                        detailed_rank_obj = sr_list[0]
                        # Merge in the "custom_data" if it exists
                        if "rank" in detailed_rank_obj and "custom_data" in detailed_rank_obj["rank"]:
                            # Ensure our original rank_obj["rank"] is a dict
                            rank_obj.setdefault("rank", {})
                            rank_obj["rank"]["custom_data"] = detailed_rank_obj["rank"].get("custom_data", {})
            
            if self.cache_enabled:
                self.cache[cache_key] = data
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching player ranks: {e}")
            raise 

    def extract_player_uuids(self, player_lookup_response: Dict[str, Any]) -> List[str]:
        """
        Extract all player UUIDs from a player lookup response.
        
        Args:
            player_lookup_response: The response from fetch_player_with_displayname
            
        Returns:
            list: A list of player UUIDs
        """
        logger.debug("Extracting player UUIDs from lookup response")
        uuids = []
        display_names = player_lookup_response.get("display_names", [])
        for display_name_dict in display_names:
            for name, players in display_name_dict.items():
                for player in players:
                    player_uuid = player.get("player_uuid")
                    if player_uuid:
                        uuids.append(player_uuid)
        
        logger.debug(f"Extracted {len(uuids)} player UUIDs")
        return uuids
        
    def filter_matches(self, matches: List[Dict[str, Any]], filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
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
                    "min_kda": 2.0,
                    "win_only": True,
                    "map": "Conquest Map"
                }
                
        Returns:
            list: Filtered list of match data dictionaries
        """
        if not filters:
            return matches
            
        logger.debug(f"Filtering {len(matches)} matches with criteria: {filters}")
        filtered_matches = []
        
        for match in matches:
            include = True
            
            # Filter by god name
            if "god_name" in filters and match.get("god_name") != filters["god_name"]:
                include = False
                
            # Filter by game mode
            if "mode" in filters and match.get("mode") != filters["mode"]:
                include = False
                
            # Filter by map
            if "map" in filters and match.get("map") != filters["map"]:
                include = False
                
            # Filter by date range
            if "min_date" in filters:
                import datetime
                start_ts = match.get("match_start")
                if start_ts:
                    try:
                        # Parse the match date
                        if 'T' in start_ts:
                            # Remove timezone info for consistent comparison
                            match_date_str = start_ts.replace('Z', '')
                            if '+' in match_date_str:
                                match_date_str = match_date_str.split('+')[0]
                            match_date = datetime.datetime.fromisoformat(match_date_str)
                        else:
                            match_date = datetime.datetime.fromisoformat(start_ts)
                            
                        # Parse min_date (could be just YYYY-MM-DD or full ISO format)
                        min_date_str = filters["min_date"]
                        if 'T' in min_date_str:
                            # Remove timezone info for consistent comparison
                            min_date_str = min_date_str.replace('Z', '')
                            if '+' in min_date_str:
                                min_date_str = min_date_str.split('+')[0]
                            min_date = datetime.datetime.fromisoformat(min_date_str)
                        else:
                            # If just a date is provided (no time), use start of day
                            min_date = datetime.datetime.fromisoformat(f"{min_date_str}T00:00:00")
                            
                        if match_date < min_date:
                            include = False
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid date format for match {match.get('match_id')}: {e}")
                        
            if "max_date" in filters:
                import datetime
                start_ts = match.get("match_start")
                if start_ts:
                    try:
                        # Parse the match date
                        if 'T' in start_ts:
                            # Remove timezone info for consistent comparison
                            match_date_str = start_ts.replace('Z', '')
                            if '+' in match_date_str:
                                match_date_str = match_date_str.split('+')[0]
                            match_date = datetime.datetime.fromisoformat(match_date_str)
                        else:
                            match_date = datetime.datetime.fromisoformat(start_ts)
                            
                        # Parse max_date (could be just YYYY-MM-DD or full ISO format)
                        max_date_str = filters["max_date"]
                        if 'T' in max_date_str:
                            # Remove timezone info for consistent comparison
                            max_date_str = max_date_str.replace('Z', '')
                            if '+' in max_date_str:
                                max_date_str = max_date_str.split('+')[0]
                            max_date = datetime.datetime.fromisoformat(max_date_str)
                        else:
                            # If just a date is provided (no time), use end of day
                            max_date = datetime.datetime.fromisoformat(f"{max_date_str}T23:59:59")
                            
                        if match_date > max_date:
                            include = False
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid date format for match {match.get('match_id')}: {e}")
            
            # Filter by win/loss
            if "win_only" in filters:
                winning_team = match.get("winning_team")
                team_id = match.get("team_id")
                if winning_team is not None and team_id is not None:
                    if filters["win_only"] and team_id != winning_team:
                        include = False
                    elif filters["win_only"] == False and team_id == winning_team:
                        include = False
                else:
                    include = False
            
            # Filter by performance stats
            basic_stats = match.get("basic_stats", {})
            
            if "min_kills" in filters and basic_stats.get("Kills", 0) < filters["min_kills"]:
                include = False
                
            if "min_deaths" in filters and basic_stats.get("Deaths", 0) < filters["min_deaths"]:
                include = False
                
            if "max_deaths" in filters and basic_stats.get("Deaths", 0) > filters["max_deaths"]:
                include = False
                
            if "min_assists" in filters and basic_stats.get("Assists", 0) < filters["min_assists"]:
                include = False
                
            if "min_kda" in filters:
                kills = basic_stats.get("Kills", 0)
                deaths = max(basic_stats.get("Deaths", 1), 1)  # Avoid division by zero
                assists = basic_stats.get("Assists", 0)
                kda = (kills + assists) / deaths
                if kda < filters["min_kda"]:
                    include = False
                    
            if "min_damage" in filters and basic_stats.get("TotalDamage", 0) < filters["min_damage"]:
                include = False
                
            if "min_healing" in filters:
                total_healing = basic_stats.get("TotalAllyHealing", 0) + basic_stats.get("TotalSelfHealing", 0)
                if total_healing < filters["min_healing"]:
                    include = False
                    
            # Include the match if it passed all filters
            if include:
                filtered_matches.append(match)
                
        logger.debug(f"Filter returned {len(filtered_matches)} matches out of {len(matches)}")
        return filtered_matches 

    def calculate_player_performance(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate aggregate performance metrics from a player's match history.
        
        This method analyzes a list of match data to produce comprehensive performance statistics,
        including overall metrics, per-god statistics, and per-game mode statistics.
        
        Args:
            matches: List of match data dictionaries
            
        Returns:
            Dict[str, Any]: Dictionary containing aggregate performance metrics including:
                - total_matches: Total number of matches played
                - wins, losses: Count of wins and losses
                - win_rate: Percentage of matches won
                - avg_kills, avg_deaths, avg_assists: Average per match
                - avg_kda: Overall KDA ratio
                - total_kills, total_deaths, total_assists: Total counts
                - total_damage, total_healing: Total damage and healing done
                - god_stats: Per-god performance metrics
                - mode_stats: Per-mode performance metrics
        """
        logger.info(f"Calculating player performance metrics for {len(matches)} matches")
        
        if not matches:
            logger.warning("No matches provided for performance calculation")
            return {}
            
        total_matches = len(matches)
        wins = 0
        kills = 0
        deaths = 0
        assists = 0
        damage = 0
        healing = 0
        mitigated = 0
        structure_damage = 0
        minion_damage = 0
        gold_earned = 0
        wards_placed = 0
        
        god_stats = {}
        mode_stats = {}
        role_stats = {}
        
        # Process each match
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
            mitigated += basic_stats.get("TotalDamageMitigated", 0)
            structure_damage += basic_stats.get("TotalStructureDamage", 0)
            minion_damage += basic_stats.get("TotalMinionDamage", 0)
            gold_earned += basic_stats.get("TotalGoldEarned", 0)
            wards_placed += basic_stats.get("TotalWardsPlaced", 0)
            
            # Track stats by god
            god_name = match.get("god_name")
            if god_name:
                if god_name not in god_stats:
                    god_stats[god_name] = {
                        "matches": 0,
                        "wins": 0,
                        "kills": 0,
                        "deaths": 0,
                        "assists": 0,
                        "damage": 0
                    }
                
                god_stats[god_name]["matches"] += 1
                if match.get("team_id") == match.get("winning_team"):
                    god_stats[god_name]["wins"] += 1
                god_stats[god_name]["kills"] += basic_stats.get("Kills", 0)
                god_stats[god_name]["deaths"] += basic_stats.get("Deaths", 0)
                god_stats[god_name]["assists"] += basic_stats.get("Assists", 0)
                god_stats[god_name]["damage"] += basic_stats.get("TotalDamage", 0)
                
            # Track stats by game mode
            mode = match.get("mode")
            if mode:
                if mode not in mode_stats:
                    mode_stats[mode] = {
                        "matches": 0,
                        "wins": 0,
                        "kills": 0,
                        "deaths": 0,
                        "assists": 0
                    }
                
                mode_stats[mode]["matches"] += 1
                if match.get("team_id") == match.get("winning_team"):
                    mode_stats[mode]["wins"] += 1
                mode_stats[mode]["kills"] += basic_stats.get("Kills", 0)
                mode_stats[mode]["deaths"] += basic_stats.get("Deaths", 0)
                mode_stats[mode]["assists"] += basic_stats.get("Assists", 0)
            
            # Track stats by role
            role = match.get("played_role")
            if role:
                if role not in role_stats:
                    role_stats[role] = {
                        "matches": 0,
                        "wins": 0
                    }
                
                role_stats[role]["matches"] += 1
                if match.get("team_id") == match.get("winning_team"):
                    role_stats[role]["wins"] += 1
        
        # Calculate averages and win rates
        avg_kills = kills / total_matches if total_matches > 0 else 0
        avg_deaths = deaths / total_matches if total_matches > 0 else 0
        avg_assists = assists / total_matches if total_matches > 0 else 0
        avg_kda = (kills + assists) / max(deaths, 1)
        win_rate = wins / total_matches if total_matches > 0 else 0
        
        # Calculate win rates and averages by god
        for god, stats in god_stats.items():
            stats["win_rate"] = stats["wins"] / stats["matches"] if stats["matches"] > 0 else 0
            stats["avg_kills"] = stats["kills"] / stats["matches"] if stats["matches"] > 0 else 0
            stats["avg_deaths"] = stats["deaths"] / stats["matches"] if stats["matches"] > 0 else 0
            stats["avg_assists"] = stats["assists"] / stats["matches"] if stats["matches"] > 0 else 0
            stats["avg_kda"] = (stats["kills"] + stats["assists"]) / max(stats["deaths"], 1)
            stats["avg_damage"] = stats["damage"] / stats["matches"] if stats["matches"] > 0 else 0
            
        # Calculate win rates and averages by mode
        for mode, stats in mode_stats.items():
            stats["win_rate"] = stats["wins"] / stats["matches"] if stats["matches"] > 0 else 0
            stats["avg_kills"] = stats["kills"] / stats["matches"] if stats["matches"] > 0 else 0
            stats["avg_deaths"] = stats["deaths"] / stats["matches"] if stats["matches"] > 0 else 0
            stats["avg_assists"] = stats["assists"] / stats["matches"] if stats["matches"] > 0 else 0
            stats["avg_kda"] = (stats["kills"] + stats["assists"]) / max(stats["deaths"], 1)
        
        # Calculate win rates by role
        for role, stats in role_stats.items():
            stats["win_rate"] = stats["wins"] / stats["matches"] if stats["matches"] > 0 else 0
        
        # Determine favorite god and role (most played)
        favorite_god = max(god_stats.items(), key=lambda x: x[1]["matches"])[0] if god_stats else None
        favorite_role = max(role_stats.items(), key=lambda x: x[1]["matches"])[0] if role_stats else None
        favorite_mode = max(mode_stats.items(), key=lambda x: x[1]["matches"])[0] if mode_stats else None
        
        # Find best performing god (highest KDA with at least 3 matches)
        best_gods = [g for g, s in god_stats.items() if s["matches"] >= 3]
        best_god = max(best_gods, key=lambda g: god_stats[g]["avg_kda"]) if best_gods else favorite_god
        
        # Build complete performance stats dictionary
        performance_stats = {
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
            "total_mitigated": mitigated,
            "total_structure_damage": structure_damage,
            "total_minion_damage": minion_damage,
            "total_gold_earned": gold_earned,
            "total_wards_placed": wards_placed,
            "avg_damage_per_match": damage / total_matches if total_matches > 0 else 0,
            "avg_healing_per_match": healing / total_matches if total_matches > 0 else 0,
            "avg_gold_per_match": gold_earned / total_matches if total_matches > 0 else 0,
            "avg_wards_per_match": wards_placed / total_matches if total_matches > 0 else 0,
            "favorite_god": favorite_god,
            "favorite_role": favorite_role,
            "favorite_mode": favorite_mode,
            "best_performing_god": best_god,
            "god_stats": god_stats,
            "mode_stats": mode_stats,
            "role_stats": role_stats
        }
        
        logger.debug(f"Calculated performance metrics: win_rate={win_rate:.1%}, avg_kda={avg_kda:.2f}")
        return performance_stats 

    def flatten_player_lookup_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Flatten the player lookup response into a simple list of player objects.
        
        The player lookup endpoints return data in a deeply nested structure that can be
        difficult to work with. This method transforms that nested structure into a flat
        list of player records, making it much easier to iterate, filter, and display.
        
        Args:
            response: The response from fetch_player_with_displayname
            
        Returns:
            List[Dict[str, Any]]: A list of player dictionaries with display_name added to each record
        """
        logger.info("Flattening player lookup response")
        players = []
        
        if not response:
            logger.warning("Empty response provided to flatten_player_lookup_response")
            return []
            
        display_names = response.get("display_names", [])
        if not display_names:
            logger.warning("No display_names found in response")
            return []
            
        # Iterate through the nested structure
        for display_name_dict in display_names:
            for display_name, player_list in display_name_dict.items():
                for player in player_list:
                    # Create a copy of the player object
                    player_copy = player.copy()
                    # Add the display name to the player record
                    player_copy["display_name"] = display_name
                    # Add to our flattened list
                    players.append(player_copy)
                    
        logger.debug(f"Flattened player lookup response: {len(players)} players found")
        return players 