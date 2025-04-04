import streamlit as st
import sys
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# Add the parent directory to sys.path to import the S2Match SDK
parent_dir = str(Path(__file__).parent.parent.parent.absolute())
sys.path.insert(0, parent_dir)

# Import utility functions
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
from utils.app_utils import display_code_example, format_json, display_json, load_demo_data, json_to_df
from utils.logger import get_logger, log_exception
from utils.env_loader import load_env_file

# Set up logger
logger = get_logger("FullPlayerData")
logger.info("Full Player Data page loaded")

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

# Function to add log message to session state
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
    page_title="Full Player Data - S2Match SDK Companion",
    page_icon="🎮",
    layout="wide"
)

st.title("Full Player Data")
st.subheader("Comprehensive player analysis including profiles, stats, and match history")

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
    ### Full Player Data Method
    
    The S2Match SDK provides a comprehensive method for retrieving all player data in one call:
    
    **`get_full_player_data_by_displayname`**: Fetch profile, stats, ranks, and match history for a player.
    - Parameters: 
      - `platform`: Platform to search (e.g., 'Steam', 'XboxLive')
      - `display_name`: The display name of the player
      - `max_matches`: Maximum number of matches to retrieve (default: 100)
    - Returns: Dictionary with player info, stats, ranks, and match history
    
    This method combines multiple API calls into a single function, making it easier to get a complete picture of a player's data. The returned data structure has the following sections:
    
    ```
    {
        "PlayerInfo": {
            "display_names": [...]  # Player profile information
        },
        "PlayerStats": [
            {
                "player_uuid": "...",
                "stats": {...}      # Statistics for this player
            },
            ...                     # Stats for linked accounts
        ],
        "PlayerRanks": [
            {...},                  # Rank information
            ...
        ],
        "MatchHistory": [
            {...},                  # Match history data
            ...
        ]
    }
    ```
    
    This single method replaces the need to make separate calls to:
    - `fetch_player_with_displayname`
    - `get_player_stats` (for each account)
    - `fetch_player_ranks_by_uuid` (for each account)
    - `get_matches_by_player_uuid` (for each account)
    """)

# Player Selection
st.subheader("Player Lookup")

# Option to use player from previous page if available
player_selection_method = "manual"
if "selected_player" in st.session_state:
    player_from_lookup = st.session_state.get("selected_player", {})
    player_name = st.session_state.get("selected_player_name", "Unknown Player")
    platform = player_from_lookup.get("platform")
    
    if player_name and platform:
        use_previous = st.checkbox(f"Use player from lookup: {player_name} ({platform})", value=True)
        if use_previous:
            player_selection_method = "previous"
            display_name = player_name
            selected_platform = platform

# Manual Player Selection
if player_selection_method == "manual":
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        display_name = st.text_input("Display Name", value="Weak3n")
        
    with col2:
        platforms = ["Steam", "XboxLive", "PlayStation", "EpicGames", "LegacyName", "Switch"]
        selected_platform = st.selectbox("Platform", platforms, index=0)
        
    with col3:
        max_matches = st.number_input("Max Matches", min_value=1, max_value=100, value=10)
else:
    # Display settings when using player from previous page
    max_matches = st.number_input("Max Matches", min_value=1, max_value=100, value=10)

# Display Code Example
with st.expander("Code Example", expanded=False):
    code_example = f"""
    from s2match import S2Match
    
    # Initialize the SDK
    sdk = S2Match()
    
    # Get comprehensive player data
    full_data = sdk.get_full_player_data_by_displayname(
        platform="{selected_platform}",
        display_name="{display_name}",
        max_matches={max_matches}
    )
    
    # Access player profile information
    display_names = full_data.get("PlayerInfo", {{}}).get("display_names", [])
    for display_name_dict in display_names:
        for name, players in display_name_dict.items():
            print(f"Found {{len(players)}} results for '{{name}}'")
            for player in players:
                print(f"  Player UUID: {{player.get('player_uuid')}}")
                print(f"  Platform: {{player.get('platform')}}")
                linked_portals = player.get("linked_portals", [])
                print(f"  Linked portals: {{len(linked_portals)}}")
    
    # Access player statistics
    for stats_obj in full_data.get("PlayerStats", []):
        player_uuid = stats_obj.get("player_uuid")
        stats = stats_obj.get("stats", {{}})
        print(f"Stats for player {{player_uuid}}:")
        print(f"  Total matches: {{stats.get('total_matches_played', 0)}}")
        print(f"  Total wins: {{stats.get('total_wins', 0)}}")
    
    # Access player ranks
    for rank in full_data.get("PlayerRanks", []):
        print(f"Rank: {{rank.get('rank_name', 'Unknown')}}")
        print(f"  Rank ID: {{rank.get('rank_id')}}")
        print(f"  Description: {{rank.get('rank_description')}}")
    
    # Access match history
    for match in full_data.get("MatchHistory", [])[:3]:  # Show first 3 matches
        print(f"Match ID: {{match.get('match_id')}}")
        print(f"God: {{match.get('god_name')}}")
        print(f"K/D/A: {{match.get('basic_stats', {{}}).get('Kills', 0)}}/{{match.get('basic_stats', {{}}).get('Deaths', 0)}}/{{match.get('basic_stats', {{}}).get('Assists', 0)}}")
    """
    
    display_code_example("Full Player Data Retrieval", code_example)

# Fetch Button
fetch_button = st.button("Fetch Full Player Data")

# Results Section
if fetch_button:
    with st.spinner("Fetching comprehensive player data... This might take a moment as it combines multiple API calls."):
        if not display_name:
            st.error("Please enter a display name")
            st.stop()
            
        if demo_mode:
            # Demo mode - use mock data
            add_log_message("INFO", f"Using demo data for player: {display_name} on platform: {selected_platform}")
            st.info("Using demo data for full player data")
            
            # Create mock full player data
            mock_player_data = {
                "PlayerInfo": {
                    "display_names": [
                        {
                            display_name: [
                                {
                                    "player_uuid": "demo-player-uuid",
                                    "player_id": 12345,
                                    "platform": selected_platform,
                                    "linked_portals": [
                                        {
                                            "player_uuid": "linked-uuid-1",
                                            "platform": "PlayStation" if selected_platform != "PlayStation" else "XboxLive",
                                            "player_id": 67890
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                "PlayerStats": [
                    {
                        "player_uuid": "demo-player-uuid",
                        "stats": {
                            "total_matches_played": 50,
                            "total_wins": 30
                        }
                    },
                    {
                        "player_uuid": "linked-uuid-1",
                        "stats": {
                            "total_matches_played": 25,
                            "total_wins": 15
                        }
                    }
                ],
                "PlayerRanks": [
                    {
                        "player_uuid": "demo-player-uuid",
                        "rank_id": "rank-001",
                        "rank_name": "Platinum",
                        "rank_description": "Platinum rank for Conquest mode",
                        "rank": {
                            "custom_data": {
                                "tier": 2,
                                "division": 1,
                                "points": 85
                            }
                        }
                    }
                ],
                "MatchHistory": []
            }
            
            # Add mock match history data
            for match in demo_data.get("matches", [])[:max_matches]:
                mock_player_data["MatchHistory"].append(match)
                
            full_data = mock_player_data
            
        else:
            # Real API mode
            try:
                add_log_message("INFO", f"Fetching full player data for {display_name} on platform {selected_platform}")
                
                full_data = sdk.get_full_player_data_by_displayname(
                    platform=selected_platform,
                    display_name=display_name,
                    max_matches=max_matches
                )
                
                add_log_message("INFO", "Full player data retrieved successfully")
            except Exception as e:
                error_msg = log_exception(logger, e, f"Error retrieving full player data: {e}")
                add_log_message("ERROR", f"Error retrieving full player data: {str(e)}")
                st.error(f"Error retrieving full player data: {str(e)}")
                st.stop()
        
        # Store data in session state for reuse
        st.session_state["current_full_data"] = full_data
        
        # Check if we got valid data
        if not full_data:
            st.warning("No data found for this player")
            st.stop()
            
        # Success message with summary of what was found
        num_players = 0
        player_info = full_data.get("PlayerInfo", {})
        display_names_list = player_info.get("display_names", [])
        
        for display_name_dict in display_names_list:
            for name, players in display_name_dict.items():
                num_players += len(players)
                
        num_stats = len(full_data.get("PlayerStats", []))
        num_ranks = len(full_data.get("PlayerRanks", []))
        num_matches = len(full_data.get("MatchHistory", []))
        
        st.success(f"Found data for {num_players} player(s), {num_stats} stats record(s), {num_ranks} rank(s), and {num_matches} match(es)!")
        
        # Create tabs for different sections
        player_tabs = st.tabs(["Player Profiles", "Statistics", "Ranks", "Match History", "Raw Data"])
        
        # Tab 1: Player Profiles
        with player_tabs[0]:
            st.subheader("Player Profiles")
            
            # Process each display name
            for display_name_dict in display_names_list:
                for name, players in display_name_dict.items():
                    st.write(f"### Results for '{name}'")
                    
                    # Create cards for each player
                    player_cols = st.columns(min(len(players), 3))
                    
                    for i, player in enumerate(players):
                        with player_cols[i]:
                            player_uuid = player.get("player_uuid", "Unknown")
                            player_platform = player.get("platform", "Unknown")
                            linked_portals = player.get("linked_portals", [])
                            
                            # Player card with styling
                            st.markdown(f"""
                            <div style="
                                border: 1px solid #444;
                                border-radius: 5px;
                                padding: 15px;
                                margin-bottom: 20px;
                                background-color: #2a2a2a;
                                color: #ffffff;
                            ">
                                <h4 style="margin-top: 0; color: #ffffff;">{name}</h4>
                                <p><strong style="color: #cccccc;">Platform:</strong> {player_platform}</p>
                                <p><strong style="color: #cccccc;">Player UUID:</strong> {player_uuid}</p>
                                <p><strong style="color: #cccccc;">Player ID:</strong> {player.get('player_id', 'Unknown')}</p>
                                <p><strong style="color: #cccccc;">Linked Accounts:</strong> {len(linked_portals)}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Show linked accounts if any
                            if linked_portals:
                                with st.expander("Linked Accounts", expanded=False):
                                    for portal in linked_portals:
                                        portal_uuid = portal.get("player_uuid", "Unknown")
                                        portal_platform = portal.get("platform", "Unknown")
                                        
                                        st.markdown(f"""
                                        <div style="
                                            border: 1px solid #444;
                                            border-radius: 5px;
                                            padding: 10px;
                                            margin-bottom: 10px;
                                            background-color: #1a1a1a;
                                            color: #ffffff;
                                        ">
                                            <p><strong style="color: #cccccc;">Platform:</strong> {portal_platform}</p>
                                            <p><strong style="color: #cccccc;">Player UUID:</strong> {portal_uuid}</p>
                                            <p><strong style="color: #cccccc;">Player ID:</strong> {portal.get('player_id', 'Unknown')}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
            
            # Display placeholder for next tabs
            st.info("Check the other tabs to view statistics, ranks, and match history!")

        # The other tab sections will be added in the next steps
        with player_tabs[1]:
            # Statistics Tab
            st.subheader("Player Statistics")
            
            # Check if we have stats data
            player_stats_list = full_data.get("PlayerStats", [])
            
            if not player_stats_list:
                st.warning("No statistics found for this player")
            else:
                # Create a selectbox to choose which player's stats to view
                stats_options = []
                
                # Find player names
                for display_name_dict in display_names_list:
                    for name, players in display_name_dict.items():
                        for player in players:
                            player_uuid = player.get("player_uuid")
                            player_platform = player.get("platform", "Unknown")
                            stats_options.append({
                                "label": f"{name} ({player_platform})",
                                "value": player_uuid
                            })
                            
                            # Add linked portals
                            for portal in player.get("linked_portals", []):
                                portal_uuid = portal.get("player_uuid")
                                portal_platform = portal.get("platform", "Unknown")
                                stats_options.append({
                                    "label": f"Linked Account: {portal_platform}",
                                    "value": portal_uuid
                                })
                
                # Create option labels and values
                stat_labels = [opt["label"] for opt in stats_options]
                stat_values = [opt["value"] for opt in stats_options]
                
                # Default to first option
                default_idx = 0
                
                selected_player_label = st.selectbox(
                    "Select account to view statistics",
                    options=stat_labels,
                    index=default_idx
                )
                
                selected_player_uuid = stat_values[stat_labels.index(selected_player_label)]
                
                # Find stats for selected player
                selected_stats = None
                for stats_obj in player_stats_list:
                    if stats_obj.get("player_uuid") == selected_player_uuid:
                        selected_stats = stats_obj.get("stats", {})
                        break
                
                if not selected_stats:
                    st.warning(f"No statistics available for the selected account")
                else:
                    # Display statistics
                    st.write(f"## Statistics for {selected_player_label}")
                    
                    # Calculate some derived stats
                    total_matches = selected_stats.get("total_matches_played", 0)
                    total_wins = selected_stats.get("total_wins", 0)
                    total_losses = total_matches - total_wins
                    win_rate = total_wins / max(total_matches, 1)
                    
                    # Display key metrics in columns
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Matches", total_matches)
                        
                    with col2:
                        st.metric("Wins", total_wins)
                        
                    with col3:
                        st.metric("Losses", total_losses)
                        
                    with col4:
                        st.metric("Win Rate", f"{win_rate:.1%}")
                    
                    # Create visualization of win/loss if there are matches
                    if total_matches > 0:
                        try:
                            # Pie chart for win/loss ratio
                            fig = go.Figure(data=[go.Pie(
                                labels=['Wins', 'Losses'],
                                values=[total_wins, total_losses],
                                hole=.3,
                                marker_colors=['#4CAF50', '#F44336']
                            )])
                            fig.update_layout(title_text="Win/Loss Distribution")
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error creating win/loss chart: {str(e)}")
                    
                    # Display all stats in a table
                    st.subheader("All Statistics")
                    
                    # Convert to DataFrame
                    stats_df = pd.DataFrame([
                        {"Statistic": key, "Value": value}
                        for key, value in selected_stats.items()
                    ])
                    
                    # Format values
                    for i, row in stats_df.iterrows():
                        value = row["Value"]
                        if isinstance(value, float) and "rate" in row["Statistic"].lower():
                            stats_df.at[i, "Value"] = f"{value:.1%}"
                        elif isinstance(value, float):
                            stats_df.at[i, "Value"] = f"{value:.2f}"
                        elif isinstance(value, int):
                            stats_df.at[i, "Value"] = f"{value:,}"
                    
                    # Display as a table
                    st.dataframe(stats_df, use_container_width=True)
                    
                    # Raw stats data
                    with st.expander("Raw Statistics Data", expanded=False):
                        st.json(selected_stats)

        with player_tabs[2]:
            # Ranks Tab
            st.subheader("Player Ranks")
            
            # Check if we have rank data
            player_ranks = full_data.get("PlayerRanks", [])
            
            if not player_ranks:
                st.warning("No rank data found for this player")
            else:
                # Create a grid of rank cards
                cols_per_row = 3
                num_ranks = len(player_ranks)
                num_rows = (num_ranks + cols_per_row - 1) // cols_per_row
                
                for i in range(num_rows):
                    row_ranks = player_ranks[i * cols_per_row:min((i + 1) * cols_per_row, num_ranks)]
                    cols = st.columns(cols_per_row)
                    
                    for j, rank in enumerate(row_ranks):
                        with cols[j]:
                            # Extract rank info
                            rank_name = rank.get("rank_name", "Unknown Rank")
                            rank_description = rank.get("rank_description", "")
                            rank_id = rank.get("rank_id", "Unknown")
                            player_uuid = rank.get("player_uuid", "Unknown")
                            
                            # Try to find player info
                            player_name = "Unknown Player"
                            player_platform = "Unknown"
                            for display_name_dict in display_names_list:
                                for name, players in display_name_dict.items():
                                    for player in players:
                                        if player.get("player_uuid") == player_uuid:
                                            player_name = name
                                            player_platform = player.get("platform", "Unknown")
                                            break
                                    if player_name != "Unknown Player":
                                        break
                                if player_name != "Unknown Player":
                                    break
                            
                            # Try to get custom data
                            custom_data = {}
                            rank_obj = rank.get("rank", {})
                            if rank_obj:
                                custom_data = rank_obj.get("custom_data", {})
                            
                            # Create rank card
                            st.markdown(f"""
                            <div style="
                                border: 1px solid #444;
                                border-radius: 5px;
                                padding: 15px;
                                margin-bottom: 20px;
                                background-color: #2a2a2a;
                                color: #ffffff;
                            ">
                                <h4 style="margin-top: 0; color: #ffffff;">{rank_name}</h4>
                                <p><em style="color: #cccccc;">{rank_description}</em></p>
                                <p><strong style="color: #cccccc;">Player:</strong> {player_name} ({player_platform})</p>
                                <p><strong style="color: #cccccc;">Rank ID:</strong> {rank_id}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Display custom data if available
                            if custom_data:
                                with st.expander("Rank Details", expanded=False):
                                    # Extract and display tier/division/points if available
                                    if "tier" in custom_data or "division" in custom_data or "points" in custom_data:
                                        tier = custom_data.get("tier", "Unknown")
                                        division = custom_data.get("division", "Unknown")
                                        points = custom_data.get("points", "Unknown")
                                        
                                        st.markdown(f"""
                                        <div style="
                                            display: flex;
                                            justify-content: space-between;
                                            margin-bottom: 10px;
                                        ">
                                            <div style="text-align: center;">
                                                <h5 style="color: #cccccc;">Tier</h5>
                                                <p style="font-size: 1.5em; font-weight: bold; color: #ffffff;">{tier}</p>
                                            </div>
                                            <div style="text-align: center;">
                                                <h5 style="color: #cccccc;">Division</h5>
                                                <p style="font-size: 1.5em; font-weight: bold; color: #ffffff;">{division}</p>
                                            </div>
                                            <div style="text-align: center;">
                                                <h5 style="color: #cccccc;">Points</h5>
                                                <p style="font-size: 1.5em; font-weight: bold; color: #ffffff;">{points}</p>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    # Show all custom data
                                    st.json(custom_data)
                
                # Display raw rank data
                with st.expander("Raw Rank Data", expanded=False):
                    st.json(player_ranks)

        with player_tabs[3]:
            # Match History Tab - Display a simplified version, since we have a dedicated Match History page
            st.subheader("Recent Match History")
            
            # Get match history data
            match_history = full_data.get("MatchHistory", [])
            
            if not match_history:
                st.warning("No match history found for this player")
            else:
                st.success(f"Found {len(match_history)} recent matches")
                
                # Display in a table format
                match_data = []
                for match in match_history:
                    # Extract basic info
                    match_id = match.get("match_id", "Unknown")
                    god_name = match.get("god_name", "Unknown")
                    map_name = match.get("map", "Unknown")
                    mode = match.get("mode", "Unknown")
                    
                    # Result
                    result = "Victory" if match.get("team_id") == match.get("winning_team") else "Defeat"
                    
                    # Match date
                    match_date = "Unknown"
                    if match.get("match_start"):
                        try:
                            date_obj = datetime.fromisoformat(match.get("match_start").replace('Z', '+00:00'))
                            match_date = date_obj.strftime("%Y-%m-%d %H:%M")
                        except:
                            pass
                    
                    # Stats
                    basic_stats = match.get("basic_stats", {})
                    kills = basic_stats.get("Kills", 0)
                    deaths = basic_stats.get("Deaths", 0)
                    assists = basic_stats.get("Assists", 0)
                    
                    match_data.append({
                        "Date": match_date,
                        "God": god_name,
                        "Mode": mode,
                        "Map": map_name,
                        "Result": result,
                        "K/D/A": f"{kills}/{deaths}/{assists}",
                        "Match ID": match_id
                    })
                
                # Convert to DataFrame
                match_df = pd.DataFrame(match_data)
                
                # Display table
                st.dataframe(match_df, use_container_width=True)
                
                # Add link to Match History page
                st.markdown("For more detailed match analysis, go to the [Match History page](Match_History)")
                
                # Show a KDA chart
                st.subheader("Performance Trend")
                
                try:
                    # Prepare data for chart
                    performance_data = []
                    for i, match in enumerate(match_history):
                        basic_stats = match.get("basic_stats", {})
                        kills = basic_stats.get("Kills", 0)
                        deaths = basic_stats.get("Deaths", 0)
                        assists = basic_stats.get("Assists", 0)
                        
                        # Match result
                        result = "Victory" if match.get("team_id") == match.get("winning_team") else "Defeat"
                        
                        # Match date/index
                        match_date = f"Match {i+1}"
                        if match.get("match_start"):
                            try:
                                date_obj = datetime.fromisoformat(match.get("match_start").replace('Z', '+00:00'))
                                match_date = date_obj.strftime("%m-%d %H:%M")
                            except:
                                pass
                        
                        performance_data.extend([
                            {"Match": match_date, "Stat": "Kills", "Value": kills, "Result": result},
                            {"Match": match_date, "Stat": "Deaths", "Value": deaths, "Result": result},
                            {"Match": match_date, "Stat": "Assists", "Value": assists, "Result": result}
                        ])
                    
                    # Create DataFrame
                    perf_df = pd.DataFrame(performance_data)
                    
                    # Create chart with Plotly
                    fig = px.line(
                        perf_df,
                        x="Match",
                        y="Value",
                        color="Stat",
                        markers=True,
                        title="Performance Metrics Over Recent Matches",
                        color_discrete_map={
                            "Kills": "#4CAF50",
                            "Deaths": "#F44336",
                            "Assists": "#2196F3"
                        }
                    )
                    
                    fig.update_layout(
                        xaxis_title="Match",
                        yaxis_title="Count",
                        legend_title="Metric"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Add a second chart for win/loss pattern
                    results = []
                    for i, match in enumerate(match_history):
                        # Match result
                        result = "Victory" if match.get("team_id") == match.get("winning_team") else "Defeat"
                        
                        # Match date/index
                        match_date = f"Match {i+1}"
                        if match.get("match_start"):
                            try:
                                date_obj = datetime.fromisoformat(match.get("match_start").replace('Z', '+00:00'))
                                match_date = date_obj.strftime("%m-%d %H:%M")
                            except:
                                pass
                        
                        results.append({
                            "Match": match_date,
                            "Result": result,
                            "Value": 1 if result == "Victory" else 0,
                            "God": match.get("god_name", "Unknown")
                        })
                    
                    # Create DataFrame for results
                    results_df = pd.DataFrame(results)
                    
                    # Create bar chart for results
                    result_fig = px.bar(
                        results_df,
                        x="Match",
                        y="Value",
                        color="Result",
                        hover_data=["God"],
                        title="Match Results (1 = Victory, 0 = Defeat)",
                        color_discrete_map={
                            "Victory": "#4CAF50",
                            "Defeat": "#F44336"
                        }
                    )
                    
                    result_fig.update_layout(
                        xaxis_title="Match",
                        yaxis_title="Outcome",
                        yaxis=dict(
                            tickmode="array",
                            tickvals=[0, 1],
                            ticktext=["Defeat", "Victory"]
                        )
                    )
                    
                    st.plotly_chart(result_fig, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Error creating performance charts: {str(e)}")
                
                # Show raw match data
                with st.expander("Raw Match History Data (First 3 Matches)", expanded=False):
                    st.json(match_history[:3])

        with player_tabs[4]:
            # Raw Data tab
            st.subheader("Raw Data")
            display_json(full_data, title="Full Player Data")

# Footer with page navigation
st.markdown("---")
prev_page = st.button("Previous: Player Statistics")
next_page = st.button("Next: API Explorer")

if prev_page:
    st.switch_page("pages/3_Player_Statistics.py")
    
if next_page:
    st.switch_page("pages/5_API_Explorer.py") 