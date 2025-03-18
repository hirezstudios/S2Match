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
logger = get_logger("PlayerStatistics")
logger.info("Player Statistics page loaded")

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

# Function to calculate extended statistics from match history data
def calculate_extended_stats(matches):
    """
    Calculate detailed player statistics from match history data.
    
    Args:
        matches: List of match data dictionaries
        
    Returns:
        Dict with extended statistics
    """
    if not matches:
        return {}
    
    # Initialize stats dictionary
    extended_stats = {
        "total_matches": len(matches),
        "total_wins": 0,
        "total_losses": 0,
        "total_kills": 0,
        "total_deaths": 0,
        "total_assists": 0,
        "total_damage_dealt": 0,
        "total_damage_taken": 0,
        "total_healing": 0,
        "total_mitigated": 0,
        "total_structure_damage": 0,
        "total_minion_damage": 0,
        "total_gold_earned": 0,
        "total_wards_placed": 0,
        "gods_played": {},
        "roles_played": {}
    }
    
    # Process each match
    for match in matches:
        # Win/Loss
        if match.get("team_id") == match.get("winning_team"):
            extended_stats["total_wins"] += 1
        else:
            extended_stats["total_losses"] += 1
        
        # Process basic stats
        basic_stats = match.get("basic_stats", {})
        extended_stats["total_kills"] += basic_stats.get("Kills", 0)
        extended_stats["total_deaths"] += basic_stats.get("Deaths", 0)
        extended_stats["total_assists"] += basic_stats.get("Assists", 0)
        extended_stats["total_damage_dealt"] += basic_stats.get("TotalDamage", 0)
        extended_stats["total_damage_taken"] += basic_stats.get("TotalDamageTaken", 0)
        extended_stats["total_healing"] += (basic_stats.get("TotalAllyHealing", 0) + basic_stats.get("TotalSelfHealing", 0))
        extended_stats["total_mitigated"] += basic_stats.get("TotalDamageMitigated", 0)
        extended_stats["total_structure_damage"] += basic_stats.get("TotalStructureDamage", 0)
        extended_stats["total_minion_damage"] += basic_stats.get("TotalMinionDamage", 0)
        extended_stats["total_gold_earned"] += basic_stats.get("TotalGoldEarned", 0)
        extended_stats["total_wards_placed"] += basic_stats.get("TotalWardsPlaced", 0)
        
        # Track god usage
        god_name = match.get("god_name", "Unknown")
        extended_stats["gods_played"][god_name] = extended_stats["gods_played"].get(god_name, 0) + 1
        
        # Track role usage
        played_role = match.get("played_role", "Unknown")
        if played_role:
            extended_stats["roles_played"][played_role] = extended_stats["roles_played"].get(played_role, 0) + 1
    
    # Calculate derived stats
    extended_stats["win_rate"] = extended_stats["total_wins"] / max(extended_stats["total_matches"], 1)
    extended_stats["kda_ratio"] = (extended_stats["total_kills"] + extended_stats["total_assists"]) / max(extended_stats["total_deaths"], 1)
    
    # Calculate averages
    extended_stats["avg_kills_per_match"] = extended_stats["total_kills"] / max(extended_stats["total_matches"], 1)
    extended_stats["avg_deaths_per_match"] = extended_stats["total_deaths"] / max(extended_stats["total_matches"], 1)
    extended_stats["avg_assists_per_match"] = extended_stats["total_assists"] / max(extended_stats["total_matches"], 1)
    extended_stats["avg_damage_per_match"] = extended_stats["total_damage_dealt"] / max(extended_stats["total_matches"], 1)
    extended_stats["avg_healing_per_match"] = extended_stats["total_healing"] / max(extended_stats["total_matches"], 1)
    
    # Find most played god and role
    if extended_stats["gods_played"]:
        extended_stats["favorite_god"] = max(extended_stats["gods_played"].items(), key=lambda x: x[1])[0]
    if extended_stats["roles_played"]:
        extended_stats["favorite_role"] = max(extended_stats["roles_played"].items(), key=lambda x: x[1])[0]
    
    return extended_stats

# Page configuration
st.set_page_config(
    page_title="Player Statistics - S2Match SDK Companion",
    page_icon="🎮",
    layout="wide"
)

st.title("Player Statistics")
st.subheader("Analyze detailed player performance metrics")

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
    ### Player Statistics Methods
    
    The S2Match SDK provides several methods for retrieving player statistics:
    
    1. **`fetch_player_stats`**: Fetch player statistics from the RallyHere Environment API.
       - Parameters: `player_uuid`
       - Returns: Dictionary with player statistics (typically just win/loss data)
    
    2. **`get_player_stats`**: Wrapper around fetch_player_stats, providing the same functionality.
       - Parameters: `player_uuid`
       - Returns: Dictionary with player statistics
    
    3. **`get_matches_by_player_uuid`**: Fetch match history that can be used to calculate detailed statistics.
       - Parameters: `player_uuid`, `max_matches` (default: 100)
       - Returns: List of match data that can be analyzed for performance metrics
    
    4. **`get_full_player_data_by_displayname`**: Comprehensive method that fetches player profile, stats, and match history.
       - Parameters: `platform`, `display_name`, `max_matches` (default: 100)
       - Returns: Combined dictionary with player info, stats, ranks, and match history
    
    ### Note on Statistics Data
    
    The RallyHere Environment API's `/match/v1/player/{player_uuid}/stats` endpoint provides limited statistics (primarily win/loss data).
    For more comprehensive statistics, this app calculates additional metrics by analyzing the player's match history.
    """)

# Player Selection
st.subheader("Select Player")

# Option to use player from previous page if available
player_selection_method = "manual"
if "selected_player" in st.session_state:
    player_from_lookup = st.session_state.get("selected_player", {})
    player_name = st.session_state.get("selected_player_name", "Unknown Player")
    player_uuid = player_from_lookup.get("player_uuid")
    
    if player_uuid:
        use_previous = st.checkbox(f"Use player from lookup: {player_name}", value=True)
        if use_previous:
            player_selection_method = "previous"

# Manual Player Selection
if player_selection_method == "manual":
    col1, col2 = st.columns([3, 1])
    
    with col1:
        player_uuid = st.text_input("Player UUID", value="e3438d31-c3ee-5377-b645-5a604b0e2b0e")
    
    with col2:
        max_matches = st.number_input("Max Matches to Analyze", min_value=1, max_value=100, value=20)
        
else:
    # Using player from previous page
    st.info(f"Using player UUID: {player_uuid}")
    max_matches = st.number_input("Max Matches to Analyze", min_value=1, max_value=100, value=20)

# Display Code Example
with st.expander("Code Example", expanded=False):
    code_example = f"""
    from s2match import S2Match
    
    # Initialize the SDK
    sdk = S2Match()
    
    # Get player statistics (limited data from API)
    player_stats = sdk.get_player_stats(
        player_uuid="{player_uuid}"
    )
    
    # For more comprehensive statistics, analyze match history
    matches = sdk.get_matches_by_player_uuid(
        player_uuid="{player_uuid}",
        max_matches={max_matches}
    )
    
    # Calculate statistics from match history
    extended_stats = {{
        "total_matches": len(matches),
        "total_wins": 0,
        "total_kills": 0,
        "total_deaths": 0,
        "total_assists": 0,
        "gods_played": {{}}
    }}
    
    for match in matches:
        # Win/Loss
        if match.get("team_id") == match.get("winning_team"):
            extended_stats["total_wins"] += 1
            
        # Process basic stats
        basic_stats = match.get("basic_stats", {{}})
        extended_stats["total_kills"] += basic_stats.get("Kills", 0)
        extended_stats["total_deaths"] += basic_stats.get("Deaths", 0)
        extended_stats["total_assists"] += basic_stats.get("Assists", 0)
        
        # Track god usage
        god_name = match.get("god_name", "Unknown")
        extended_stats["gods_played"][god_name] = extended_stats["gods_played"].get(god_name, 0) + 1
    
    # Calculate derived stats
    extended_stats["win_rate"] = extended_stats["total_wins"] / max(extended_stats["total_matches"], 1)
    extended_stats["kda_ratio"] = (extended_stats["total_kills"] + extended_stats["total_assists"]) / max(extended_stats["total_deaths"], 1)
    
    print(f"Win rate: {{extended_stats['win_rate']:.1%}}")
    print(f"KDA ratio: {{extended_stats['kda_ratio']:.2f}}")
    print(f"Favorite god: {{max(extended_stats['gods_played'].items(), key=lambda x: x[1])[0]}}")
    """
    
    display_code_example("Comprehensive Player Statistics Analysis", code_example)

# Fetch Button
fetch_button = st.button("Fetch Player Statistics")

# Statistics Results Section
if fetch_button:
    with st.spinner("Fetching player statistics..."):
        if not player_uuid:
            st.error("Please enter a player UUID")
            st.stop()
            
        if demo_mode:
            # Demo mode - use mock data
            add_log_message("INFO", f"Using demo data for player UUID: {player_uuid}")
            st.info("Using demo data for player statistics")
            
            # Create mock player stats
            basic_stats = {
                "total_matches_played": 50,
                "total_wins": 30
            }
            
            # Also create mock match history for extended stats
            matches = demo_data.get("matches", [])
            # Filter to only include this player's matches
            matches = [m for m in matches if m.get("player_uuid") == player_uuid]
            # If no matches found, use all demo matches
            if not matches:
                matches = demo_data.get("matches", [])
            # Limit to max_matches
            matches = matches[:max_matches]
            
            # Calculate extended stats from match history
            extended_stats = calculate_extended_stats(matches)
            
            # Merge basic and extended stats
            player_stats = {**basic_stats, **extended_stats}
            
            add_log_message("INFO", f"Generated mock statistics for player {player_uuid}")
            
        else:
            # Real API mode
            try:
                # First, get basic stats from the API
                add_log_message("INFO", f"Fetching stats for player UUID: {player_uuid}")
                basic_stats = sdk.get_player_stats(player_uuid=player_uuid)
                add_log_message("INFO", "Basic player statistics fetched successfully")
                
                # Next, get match history for extended stats
                add_log_message("INFO", f"Fetching match history for player UUID: {player_uuid} (max: {max_matches} matches)")
                matches = sdk.get_matches_by_player_uuid(
                    player_uuid=player_uuid,
                    max_matches=max_matches
                )
                add_log_message("INFO", f"Retrieved {len(matches)} matches for extended stats analysis")
                
                # Calculate extended stats from match history
                extended_stats = calculate_extended_stats(matches)
                
                # Merge basic and extended stats
                player_stats = {**basic_stats, **extended_stats}
                
                add_log_message("INFO", "Comprehensive player statistics calculated successfully")
                
            except Exception as e:
                error_msg = log_exception(logger, e, f"Error fetching player statistics: {e}")
                add_log_message("ERROR", f"Error fetching player statistics: {str(e)}")
                st.error(f"Error fetching player statistics: {str(e)}")
                st.stop()
        
        # Store stats in session state for reuse
        st.session_state["current_player_stats"] = player_stats
        st.session_state["current_player_matches"] = matches if "matches" in locals() else []
        
        # Check if we got valid stats
        if not player_stats:
            st.warning("No statistics found for this player")
            st.stop()
            
        st.success("Player statistics retrieved successfully!")
        
        # Display Statistics Overview
        st.subheader("Statistics Overview")
        
        # Calculate some derived stats if not provided
        total_matches = player_stats.get("total_matches", player_stats.get("total_matches_played", 0))
        total_wins = player_stats.get("total_wins", 0)
        total_losses = player_stats.get("total_losses", total_matches - total_wins)
        win_rate = player_stats.get("win_rate", total_wins / max(total_matches, 1))
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Matches", total_matches)
            
        with col2:
            st.metric("Wins", total_wins)
            
        with col3:
            st.metric("Losses", total_losses)
            
        with col4:
            st.metric("Win Rate", f"{win_rate:.1%}")
        
        # Combat Performance metrics
        st.subheader("Combat Performance")
        
        combat_cols = st.columns(4)
        
        with combat_cols[0]:
            st.metric("Total Kills", player_stats.get("total_kills", 0))
            
        with combat_cols[1]:
            st.metric("Total Deaths", player_stats.get("total_deaths", 0))
            
        with combat_cols[2]:
            st.metric("Total Assists", player_stats.get("total_assists", 0))
            
        with combat_cols[3]:
            kda = player_stats.get("kda_ratio", (player_stats.get("total_kills", 0) + player_stats.get("total_assists", 0)) / max(player_stats.get("total_deaths", 1), 1))
            st.metric("KDA Ratio", f"{kda:.2f}")
        
        # Additional combat metrics
        damage_cols = st.columns(4)
        
        with damage_cols[0]:
            avg_damage = player_stats.get("avg_damage_per_match", player_stats.get("total_damage_dealt", 0) / max(total_matches, 1))
            st.metric("Avg Damage/Match", f"{avg_damage:,.0f}")
            
        with damage_cols[1]:
            avg_healing = player_stats.get("avg_healing_per_match", player_stats.get("total_healing", 0) / max(total_matches, 1))
            st.metric("Avg Healing/Match", f"{avg_healing:,.0f}")
            
        with damage_cols[2]:
            gold_per_match = player_stats.get("total_gold_earned", 0) / max(total_matches, 1)
            st.metric("Avg Gold/Match", f"{gold_per_match:,.0f}")
            
        with damage_cols[3]:
            wards_per_match = player_stats.get("total_wards_placed", 0) / max(total_matches, 1)
            st.metric("Avg Wards/Match", f"{wards_per_match:.1f}")
        
        # Create visualization of win/loss
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
        
        # God/Role section if data is available
        gods_played = player_stats.get("gods_played", {})
        roles_played = player_stats.get("roles_played", {})
        
        if gods_played or roles_played:
            st.subheader("God & Role Performance")
            
            god_role_cols = st.columns(2)
            
            with god_role_cols[0]:
                if gods_played:
                    st.write("**Gods Played**")
                    # Convert to DataFrame for visualization
                    gods_df = pd.DataFrame([
                        {"God": god, "Matches": count}
                        for god, count in gods_played.items()
                    ]).sort_values("Matches", ascending=False)
                    
                    # Create bar chart
                    try:
                        gods_fig = px.bar(
                            gods_df.head(10),  # Top 10 gods
                            x="God",
                            y="Matches",
                            title="Most Played Gods",
                            color="Matches",
                            color_continuous_scale=px.colors.sequential.Blues
                        )
                        gods_fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(gods_fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating gods chart: {str(e)}")
                        st.dataframe(gods_df.head(10))
            
            with god_role_cols[1]:
                if roles_played:
                    st.write("**Roles Played**")
                    # Convert to DataFrame for visualization
                    roles_df = pd.DataFrame([
                        {"Role": role, "Matches": count}
                        for role, count in roles_played.items()
                    ]).sort_values("Matches", ascending=False)
                    
                    # Create pie chart
                    try:
                        roles_fig = px.pie(
                            roles_df,
                            values="Matches",
                            names="Role",
                            title="Role Distribution"
                        )
                        st.plotly_chart(roles_fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating roles chart: {str(e)}")
                        st.dataframe(roles_df)
        
        # Display all stats
        st.subheader("All Statistics")
        
        # Convert stats to DataFrame
        stats_df = pd.DataFrame([
            {"Statistic": key, "Value": value}
            for key, value in player_stats.items()
            if not isinstance(value, dict)  # Skip nested dictionaries
        ])
        
        # Format values
        for i, row in stats_df.iterrows():
            value = row["Value"]
            if isinstance(value, float) and ("rate" in row["Statistic"].lower() or "ratio" in row["Statistic"].lower()):
                stats_df.at[i, "Value"] = f"{value:.2f}"
            elif isinstance(value, float):
                stats_df.at[i, "Value"] = f"{value:.1f}"
            elif isinstance(value, int):
                stats_df.at[i, "Value"] = f"{value:,}"
        
        # Display as a table
        st.dataframe(stats_df, use_container_width=True)
        
        # Raw data
        with st.expander("Raw Statistics Data", expanded=False):
            st.json(player_stats)
        
        # If we have match data, offer to show match history
        if "matches" in locals() and matches:
            st.subheader("Recent Matches Used for Analysis")
            
            with st.expander("Show Match History", expanded=False):
                # Convert to DataFrame for display
                match_data = []
                for match in matches[:10]:  # Show top 10 matches
                    basic_stats = match.get("basic_stats", {})
                    
                    # Format date
                    match_date = "Unknown"
                    if match.get("match_start"):
                        try:
                            date_obj = datetime.fromisoformat(match.get("match_start").replace('Z', '+00:00'))
                            match_date = date_obj.strftime("%Y-%m-%d %H:%M")
                        except:
                            pass
                    
                    # Result
                    result = "Victory" if match.get("team_id") == match.get("winning_team") else "Defeat"
                    
                    match_data.append({
                        "Date": match_date,
                        "God": match.get("god_name", "Unknown"),
                        "Mode": match.get("mode", "Unknown"),
                        "Result": result,
                        "K/D/A": f"{basic_stats.get('Kills', 0)}/{basic_stats.get('Deaths', 0)}/{basic_stats.get('Assists', 0)}",
                        "Damage": basic_stats.get("TotalDamage", 0)
                    })
                
                match_df = pd.DataFrame(match_data)
                st.dataframe(match_df, use_container_width=True)
                
                # Link to Match History page
                st.markdown("Go to the [Match History page](Match_History) to see detailed match data.")

# Footer with page navigation
st.markdown("---")
prev_page = st.button("Previous: Match History")
next_page = st.button("Next: Full Player Data")

if prev_page:
    st.switch_page("pages/2_Match_History.py")
    
if next_page:
    st.switch_page("pages/4_Full_Player_Data.py") 