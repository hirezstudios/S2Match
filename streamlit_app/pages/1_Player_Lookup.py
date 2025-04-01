import streamlit as st
import sys
import os
import json
import pandas as pd
from pathlib import Path
import plotly.express as px

# Add the parent directory to sys.path to import the S2Match SDK
parent_dir = str(Path(__file__).parent.parent.parent.absolute())
sys.path.insert(0, parent_dir)

# Import utility functions
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
from utils.app_utils import display_code_example, format_json, display_json, load_demo_data, json_to_df
from utils.logger import get_logger, log_exception
from utils.env_loader import load_env_file

# Set up logger
logger = get_logger("PlayerLookup")
logger.info("Player Lookup page loaded")

# Load environment variables
env_vars = load_env_file()

# Import the S2Match SDK
try:
    from s2match import S2Match
    logger.info("S2Match SDK imported successfully")
except ImportError as e:
    error_msg = log_exception(logger, e, "Failed to import S2Match SDK")
    st.error("S2Match SDK not found. Make sure you're running the app from the correct directory.")
    st.stop()
# Function to add log message to session state (from Home.py)
def add_log_message(level, message):
    """Add a log message to the session state log and the logger."""
    import time
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    if "log_messages" not in st.session_state:
        st.session_state.log_messages = []
        
    st.session_state.log_messages.append({
        "timestamp": timestamp,
        "level": level,
        "message": message
    })
    
    # Also log to the actual logger
    if level == "INFO":
        logger.info(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)
    elif level == "DEBUG":
        logger.debug(message)

# Page configuration
st.set_page_config(
    page_title="Player Lookup - S2Match SDK Companion",
    page_icon="🎮",
    layout="wide"
)

st.title("Player Lookup")
st.subheader("Search for players by display name across platforms")

# Check if SDK is initialized
if not st.session_state.get("sdk_initialized", False):
    st.warning("SDK is not initialized. Using demo data instead. Please initialize the SDK in the Home page for live data.")
    add_log_message("WARNING", "Using demo data - SDK not initialized")
    demo_mode = True
    demo_data = st.session_state.get("demo_data", load_demo_data())
else:
    demo_mode = False
    sdk = st.session_state.sdk_instance
    add_log_message("INFO", "Using initialized SDK")

# SDK Method Overview
with st.expander("SDK Method Overview", expanded=False):
    st.markdown("""
    ### Player Lookup Methods
    
    The S2Match SDK provides several methods for looking up players:
    
    1. **`fetch_player_with_displayname`**: Look up players by display name, optionally filtering by platform.
       - Parameters: `display_names` (list of names), `platform` (optional), `include_linked_portals` (boolean)
       - Returns: Dictionary containing player information
    
    2. **`fetch_player_by_platform_user_id`**: Find a player by platform identity.
       - Parameters: `platform` (e.g., "Steam"), `platform_user_id` (platform-specific ID)
       - Returns: Dictionary with player information
    
    ### API Endpoints Used
    
    These methods interact with the following RallyHere Environment API endpoints:
    
    - `/users/v1/player` - Look up players by display name and platform
    - `/users/v1/player/{player_id}/linked_portals` - Get linked portal accounts for a player
    - `/users/v1/platform-user` - Find player by platform identity
    """)

# Search Form
st.subheader("Search for Players")

col1, col2 = st.columns([3, 1])

with col1:
    display_name = st.text_input("Display Name", value=st.session_state.get("selected_player_name", ""))
    
with col2:
    platform = st.selectbox(
        "Platform (Optional)",
        options=["Any", "Steam", "XboxLive", "PlayStation", "EpicGames", "LegacyName"],
        index=0
    )
    
    include_linked = st.checkbox("Include Linked Accounts", value=True)

# Display Code Example
with st.expander("Code Example", expanded=False):
    platform_code = f'"{platform}"' if platform != "Any" else "None"
    code_example = f"""
    from s2match import S2Match
    
    # Initialize the SDK
    sdk = S2Match()
    
    # Fetch player data
    response = sdk.fetch_player_with_displayname(
        display_names=["{display_name}"],
        platform={platform_code},
        include_linked_portals={str(include_linked)}
    )
    
    # Option 1: Process raw nested response (complex)
    display_names = response.get("display_names", [])
    for display_name_dict in display_names:
        for name, players in display_name_dict.items():
            print(f"Results for '{{name}}':")
            for player in players:
                print(f"  Player UUID: {{player.get('player_uuid')}}")
                
    # Option 2: Use the flatten_player_lookup_response helper (simple)
    players = sdk.flatten_player_lookup_response(response)
    for player in players:
        print(f"{{player.get('display_name')}}: {{player.get('player_uuid')}}")
    """
    
    display_code_example("Player Lookup Example", code_example)

search_button = st.button("Search Players")

st.markdown("---")

# Search Results Section
if search_button:
    add_log_message("INFO", f"Searching for player: {display_name} on platform: {platform if platform != 'Any' else 'All platforms'}")
    
    with st.spinner("Searching for players..."):
        if demo_mode:
            # Demo mode - use mock data
            logger.debug("Using demo data for player lookup")
            add_log_message("INFO", "Using demo data for player lookup")
            st.info("Using demo data for player lookup")
            
            # Filter demo players by name (case-insensitive partial match)
            filtered_players = []
            for player in demo_data.get("players", []):
                if display_name.lower() in player.get("display_name", "").lower():
                    if platform == "Any" or platform == player.get("platform"):
                        filtered_players.append(player)
            
            # Create a mock response structure similar to the SDK
            mock_response = {
                "display_names": []
            }
            
            if filtered_players:
                name_dict = {}
                for player in filtered_players:
                    player_obj = {
                        "player_uuid": player.get("player_uuid"),
                        "player_id": hash(player.get("player_uuid")) % 10000,  # Mock player_id
                        "platform": player.get("platform"),
                        "linked_portals": []
                    }
                    
                    # Add mock linked portals if requested
                    if include_linked:
                        # Add 1-2 mock linked portals
                        platforms = ["Steam", "XboxLive", "PlayStation", "EpicGames", "Discord"]
                        platforms.remove(player.get("platform"))
                        for i in range(min(2, len(platforms))):
                            linked_portal = {
                                "player_uuid": f"linked-{hash(player.get('player_uuid') + i) % 10000}",
                                "platform": platforms[i],
                                "player_id": hash(player.get("player_uuid") + i) % 10000
                            }
                            player_obj["linked_portals"].append(linked_portal)
                    
                    # Add to the name dictionary
                    name_dict.setdefault(player.get("display_name"), []).append(player_obj)
                
                # Add the name dictionary to the mock response
                for name, players in name_dict.items():
                    mock_response["display_names"].append({name: players})
            
            st.session_state["player_data"] = mock_response
            
        else:
            # Real API mode
            try:
                logger.debug(f"Making API call to fetch player with display name: {display_name}")
                platform_param = None if platform == "Any" else platform
                
                add_log_message("INFO", f"Sending API request with params: display_name={display_name}, platform={platform_param}, include_linked_portals={include_linked}")
                
                st.session_state["player_data"] = sdk.fetch_player_with_displayname(
                    display_names=[display_name],
                    platform=platform_param,
                    include_linked_portals=include_linked
                )
                
                logger.debug("API call successful")
                add_log_message("INFO", "Player lookup successful")
            except Exception as e:
                error_msg = log_exception(logger, e, f"Error searching for player: {display_name}")
                add_log_message("ERROR", f"Error searching for player: {str(e)}")
                st.error(f"Error searching for player: {str(e)}")
                st.stop()
        
        # Display results
        display_names = st.session_state["player_data"].get("display_names", [])
        
        if not display_names or all(not players for name_dict in display_names for _, players in name_dict.items()):
            logger.warning(f"No players found with display name '{display_name}'")
            add_log_message("WARNING", f"No players found with display name '{display_name}'")
            st.warning(f"No players found with display name '{display_name}'")
        else:
            total_players = sum(len(players) for name_dict in display_names for _, players in name_dict.items())
            logger.info(f"Found {total_players} players matching '{display_name}'")
            add_log_message("INFO", f"Found {total_players} players matching '{display_name}'")
            
            st.success(f"Found {total_players} player{'s'[:total_players^1]}!")
            

# Add a "View Options" section right after searching but before displaying results
if "player_data" in st.session_state:
    st.session_state["active_response_format"] = st.radio(
        "Response Format",
        options=st.session_state.response_formats,
        horizontal=True            
    )

    # Show examples of how to use the returned data
    with st.expander("Using the Response Data", expanded=False):
        st.markdown("""
### How to Extract Player UUID from Response
                
The response data is structured as a nested dictionary. Here's how to extract player UUIDs:
        """)
                
        extraction_code = """
# Using the new extract_player_uuids helper method
player_uuids = sdk.extract_player_uuids(player_data)
                                
# Now player_uuids contains all player UUIDs found
print(f"Found {len(player_uuids)} player UUIDs: {player_uuids}")
                
# For further queries, you can use the first UUID
if player_uuids:
    first_uuid = player_uuids[0]
                    
    # Example: Get player stats
    stats = sdk.get_player_stats(first_uuid)
                    
    # Example: Get player match history
    matches = sdk.get_matches_by_player_uuid(
        player_uuid=first_uuid,
        max_matches=5
    )
        """
                
        st.code(extraction_code, language="python")
                
        st.markdown("""
### Traditional Way (Without Helper)
                
For reference, here's how you would extract UUIDs without the helper method:
        """)
                
        manual_code = """
# Manual extraction process
player_uuids = []
display_names = player_data.get("display_names", [])
for display_name_dict in display_names:
    for name, players in display_name_dict.items():
        for player in players:
            player_uuid = player.get("player_uuid")
            if player_uuid:
                player_uuids.append(player_uuid)
        """
                
        st.code(manual_code, language="python")
                
        st.markdown("""
### Working with Linked Portals
                
If you included linked portals in your request, here's how to process them:
        """)
                
        linked_code = """
# For each player, process their linked portals
for display_name_dict in player_data.get("display_names", []):
    for name, players in display_name_dict.items():
        for player in players:
            linked_portals = player.get("linked_portals", [])
                            
            print(f"Player {name} has {len(linked_portals)} linked portals:")
                            
            for portal in linked_portals:
                portal_uuid = portal.get("player_uuid")
                portal_platform = portal.get("platform")
                                
                print(f"  - {portal_platform}: {portal_uuid}")
                                
                # Example: You can also fetch data for linked accounts
                portal_stats = sdk.get_player_stats(portal_uuid)
        """
                
        st.code(linked_code, language="python")

        st.write("""
### Raw vs. Flattened Response Structure
                
The player lookup endpoint returns data in a deeply nested structure that can be difficult to work with:
                
```python
{
    "display_names": [
        {
            "PlayerName": [
                {
                    "player_uuid": "uuid_string",
                    "player_id": 12345,
                    "platform": "Steam",
                    "linked_portals": [...]
                }
            ]
        }
    ]
}
```
                
The `flatten_player_lookup_response` helper method transforms this into a much simpler flat list:
                
```python
[
    {
        "display_name": "PlayerName",
        "player_uuid": "uuid_string",
        "player_id": 12345,
        "platform": "Steam",
        "linked_portals": [...]
    }
]
```
                
This makes it much easier to:
- Iterate through players with a simple loop
- Filter and sort player data
- Display player information in tables or UI components
        """)
                
        # Show before/after code comparison
        col1, col2 = st.columns(2)
                
        with col1:
            st.write("**Without Helper (Complex)**")
            st.code("""
# Complex nested loops
for display_name_dict in response.get("display_names", []):
    for name, players in display_name_dict.items():
        for player in players:
            # Now we can use the player data
            player_uuid = player.get("player_uuid")
            # ...more processing...
            """, language="python")
                
        with col2:
            st.write("**With Helper (Simple)**") 
            st.code("""
# Simple iteration
players = sdk.flatten_player_lookup_response(response)
for player in players:
    # Directly access player data
    player_uuid = player.get("player_uuid")
    name = player.get("display_name")
    # ...more processing...
            """, language="python")

    player_data = st.session_state["player_data"]
    view_format = st.session_state.active_response_format
    
    # Create flattened version of the data for simplified view
    if view_format == "Flattened Response (Simplified)":
        # Use the SDK helper method to flatten the response
        try:
            flattened_players = sdk.flatten_player_lookup_response(player_data)
            #st.success(f"Flattened response contains {len(flattened_players)} player records")
            
            # Display flattened player data
            st.subheader("Flattened Players")
            
            # Create a formatted table of players
            if flattened_players:
                # Convert players to DataFrame for display
                players_df = []
                for player in flattened_players:
                    players_df.append({
                        "Display Name": player.get("display_name", "Unknown"),
                        "Player UUID": player.get("player_uuid", "Unknown"),
                        "Platform": player.get("platform", "Unknown"),
                        "Player ID": player.get("player_id", "Unknown"),
                        "Linked Accounts": len(player.get("linked_portals", [])),
                    })
                
                # Display as DataFrame
                import pandas as pd
                st.dataframe(pd.DataFrame(players_df))
                
                # Allow selection of a player for other pages
                st.subheader("Select a Player")
                
                # Create buttons for each player
                for i, player in enumerate(flattened_players):
                    display_name = player.get("display_name", "Unknown")
                    player_uuid = player.get("player_uuid", "Unknown")
                    platform = player.get("platform", "Unknown")
                    
                    selection_text = f"{display_name} ({platform}) - {player_uuid[:8]}..."
                    if st.button(f"Select {selection_text}", key=f"select_flat_{i}"):
                        st.session_state["selected_player"] = player
                        st.session_state["selected_player_name"] = display_name
                        st.success(f"Selected {display_name} for use in other pages")
                
                # Option to view raw data
                with st.expander("View Full Player Data", expanded=False):
                    st.json(flattened_players)
            else:
                st.warning("No players found in the flattened response")
        except Exception as e:
            add_log_message("ERROR", f"Error flattening player data: {str(e)}")
            st.error(f"Error processing flattened view: {str(e)}")
            # Fall back to raw view
            view_format = "Raw API Response"
    
    # Display raw API response format (original view)
    if view_format == "Raw API Response":
        # Original display code for raw API response 
        #st.subheader("Player Data")
        
        display_names = player_data.get("display_names", [])
        
        if display_names:
            for display_name_dict in display_names:
                for display_name, players in display_name_dict.items():
                    st.write(f"### Results for '{display_name}'")
                    
                    for i, player in enumerate(players):
                        with st.container():
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.write(f"**Player {i+1}:**")
                                st.write(f"Player UUID: `{player.get('player_uuid', 'Unknown')}`")
                                st.write(f"Platform: {player.get('platform', 'Unknown')}")
                                st.write(f"Player ID: {player.get('player_id', 'Unknown')}")
                            
                            with col2:
                                # Add a button to select this player for other pages
                                if st.button(f"Select {display_name}", key=f"select_{i}"):
                                    st.session_state["selected_player"] = player
                                    st.session_state["selected_player_name"] = display_name
                                    st.success(f"Selected {display_name} for use in other pages")
                                
                                # Check if linked_portals exists and display count
                                linked_portals = player.get("linked_portals", [])
                                if linked_portals:
                                    st.write(f"Linked accounts: {len(linked_portals)}")
                                    
                                    # Expand to see linked accounts
                                    with st.expander("View Linked Accounts", expanded=False):
                                        for j, portal in enumerate(linked_portals):
                                            st.write(f"Platform: {portal.get('platform', 'Unknown')}  \n"
                                                     f"Player Name: {portal.get('display_name', 'Unknown')}  \n"
                                                     f"UUID: `{portal.get('player_uuid', 'Unknown')}`")

                        st.markdown("---")
                        
            # Using the new extract_player_uuids helper method
            player_uuids = sdk.extract_player_uuids(player_data)
            

            # Display raw JSON data if requested
            with st.expander("Raw JSON Response", expanded=False):
                st.json(player_data)
        else:
            st.warning(f"No players found with the name '{display_name}' on {platform}")

# Display full response
        with st.expander("Full Response Data", expanded=False):
                # Use display_json with use_expander=False since we're already in an expander
                display_json(player_data, title="API Response", use_expander=False)

# Footer with page navigation
st.markdown("---")
next_page = st.button("Next: Match History")
if next_page:
    add_log_message("INFO", "Navigating to Match History page")
    import streamlit as st
    st.switch_page("pages/2_Match_History.py") 

