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
    
    # Get player match history
    matches = sdk.get_matches_by_player_uuid(
        player_uuid="{player_uuid}",
        max_matches={max_matches}
    )
    
    # Calculate performance metrics using the helper method
    performance_stats = sdk.calculate_player_performance(matches)
    
    # Display overall performance metrics
    print(f"Total Matches: {{performance_stats['total_matches']}}")
    print(f"Win Rate: {{performance_stats['win_rate']:.1%}}")
    print(f"KDA Ratio: {{performance_stats['avg_kda']:.2f}} ({{performance_stats['avg_kills']:.1f}}/{{performance_stats['avg_deaths']:.1f}}/{{performance_stats['avg_assists']:.1f}})")
    print(f"Favorite God: {{performance_stats.get('favorite_god', 'Unknown')}}")
    print(f"Favorite Role: {{performance_stats.get('favorite_role', 'Unknown')}}")
    
    # Analyze god performance
    god_stats = performance_stats.get("god_stats", {{}})
    for god, stats in sorted(god_stats.items(), key=lambda x: x[1]["matches"], reverse=True):
        print(f"{{god}}: {{stats['matches']}} matches, {{stats['win_rate']:.1%}} win rate, {{stats['avg_kda']:.2f}} KDA")
    
    # Analyze mode performance
    mode_stats = performance_stats.get("mode_stats", {{}})
    for mode, stats in sorted(mode_stats.items(), key=lambda x: x[1]["matches"], reverse=True):
        print(f"{{mode}}: {{stats['matches']}} matches, {{stats['win_rate']:.1%}} win rate")
    """
    
    display_code_example("Player Performance Analysis", code_example)

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
            
            # Also create mock match history for performance metrics
            matches = demo_data.get("matches", [])
            # Filter to only include this player's matches
            matches = [m for m in matches if m.get("player_uuid") == player_uuid]
            # If no matches found, use all demo matches
            if not matches:
                matches = demo_data.get("matches", [])
            # Limit to max_matches
            matches = matches[:max_matches]
            
            # Calculate performance metrics using a new instance with a mock S2Match
            sdk = S2Match()
            player_stats = sdk.calculate_player_performance(matches)
            
            add_log_message("INFO", f"Generated mock statistics for player {player_uuid}")
            
        else:
            # Real API mode
            try:
                # Get match history for player
                add_log_message("INFO", f"Fetching match history for player UUID: {player_uuid} (max: {max_matches} matches)")
                matches = sdk.get_matches_by_player_uuid(
                    player_uuid=player_uuid,
                    max_matches=max_matches
                )
                add_log_message("INFO", f"Retrieved {len(matches)} matches for performance analysis")
                
                # If we have matches, calculate performance metrics
                if matches:
                    # Calculate performance metrics using the SDK helper method
                    add_log_message("INFO", "Calculating player performance metrics")
                    player_stats = sdk.calculate_player_performance(matches)
                    add_log_message("INFO", "Player performance metrics calculated successfully")
                else:
                    # No matches found, create empty stats
                    add_log_message("WARNING", "No matches found for player, using empty stats")
                    player_stats = {}
                
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
        total_matches = player_stats.get("total_matches", 0)
        total_wins = player_stats.get("wins", 0)
        total_losses = player_stats.get("losses", total_matches - total_wins)
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
            kda = player_stats.get("avg_kda", 0)
            st.metric("KDA Ratio", f"{kda:.2f}")
        
        # Additional combat metrics
        damage_cols = st.columns(4)
        
        with damage_cols[0]:
            avg_damage = player_stats.get("avg_damage_per_match", 0)
            st.metric("Avg Damage/Match", f"{avg_damage:,.0f}")
            
        with damage_cols[1]:
            avg_healing = player_stats.get("avg_healing_per_match", 0)
            st.metric("Avg Healing/Match", f"{avg_healing:,.0f}")
            
        with damage_cols[2]:
            gold_per_match = player_stats.get("avg_gold_per_match", 0)
            st.metric("Avg Gold/Match", f"{gold_per_match:,.0f}")
            
        with damage_cols[3]:
            wards_per_match = player_stats.get("avg_wards_per_match", 0)
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
        god_stats = player_stats.get("god_stats", {})
        role_stats = player_stats.get("role_stats", {})
        
        if god_stats or role_stats:
            st.subheader("God & Role Performance")
            
            god_role_cols = st.columns(2)
            
            with god_role_cols[0]:
                if god_stats:
                    st.write("**Gods Played**")
                    # Convert to DataFrame for visualization
                    gods_df = pd.DataFrame([
                        {"God": god, "Matches": stats["matches"], "Win Rate": stats["win_rate"], "KDA": stats["avg_kda"]}
                        for god, stats in god_stats.items()
                    ]).sort_values("Matches", ascending=False)
                    
                    # Create bar chart
                    try:
                        gods_fig = px.bar(
                            gods_df.head(10),  # Top 10 gods
                            x="God",
                            y="Matches",
                            title="Most Played Gods",
                            color="KDA",
                            color_continuous_scale=px.colors.sequential.Blues,
                            hover_data=["Win Rate", "KDA"]
                        )
                        gods_fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(gods_fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating gods chart: {str(e)}")
                        st.dataframe(
                            gods_df.head(10).style.format({
                                "Win Rate": "{:.1%}",
                                "KDA": "{:.2f}"
                            })
                        )
            
            with god_role_cols[1]:
                if role_stats:
                    st.write("**Roles Played**")
                    # Convert to DataFrame for visualization
                    roles_df = pd.DataFrame([
                        {"Role": role, "Matches": stats["matches"], "Win Rate": stats["win_rate"]}
                        for role, stats in role_stats.items()
                    ]).sort_values("Matches", ascending=False)
                    
                    # Create pie chart
                    try:
                        roles_fig = px.pie(
                            roles_df,
                            values="Matches",
                            names="Role",
                            title="Role Distribution",
                            hover_data=["Win Rate"]
                        )
                        st.plotly_chart(roles_fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating roles chart: {str(e)}")
                        st.dataframe(
                            roles_df.style.format({
                                "Win Rate": "{:.1%}"
                            })
                        )
        
        # Display mode performance if available
        mode_stats = player_stats.get("mode_stats", {})
        if mode_stats:
            st.subheader("Game Mode Performance")
            
            # Convert to DataFrame for visualization
            modes_df = pd.DataFrame([
                {"Mode": mode, "Matches": stats["matches"], "Win Rate": stats["win_rate"], "KDA": stats["avg_kda"]}
                for mode, stats in mode_stats.items()
            ]).sort_values("Matches", ascending=False)
            
            # Display as a table
            st.dataframe(
                modes_df.style.format({
                    "Win Rate": "{:.1%}",
                    "KDA": "{:.2f}"
                }),
                use_container_width=True
            )
            
            # Create bar chart for mode comparison
            try:
                modes_fig = px.bar(
                    modes_df,
                    x="Mode",
                    y="Matches",
                    color="Win Rate",
                    title="Performance by Game Mode",
                    color_continuous_scale=px.colors.sequential.Viridis,
                    hover_data=["KDA"]
                )
                st.plotly_chart(modes_fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating modes chart: {str(e)}")
        
        # Display favorite & best performing sections
        st.subheader("Favorites & Best Performers")
        
        favorites_cols = st.columns(4)
        
        with favorites_cols[0]:
            favorite_god = player_stats.get("favorite_god", "Unknown")
            st.metric("Favorite God", favorite_god)
            
        with favorites_cols[1]:
            favorite_role = player_stats.get("favorite_role", "Unknown")
            st.metric("Favorite Role", favorite_role)
            
        with favorites_cols[2]:
            favorite_mode = player_stats.get("favorite_mode", "Unknown")
            st.metric("Favorite Mode", favorite_mode)
            
        with favorites_cols[3]:
            best_god = player_stats.get("best_performing_god", "Unknown")
            st.metric("Best Performing God", best_god)
            
            # Add tooltip with explanation if best_god exists in god_stats
            if best_god in god_stats:
                st.caption(f"KDA: {god_stats[best_god]['avg_kda']:.2f}, Win Rate: {god_stats[best_god]['win_rate']:.1%} (minimum 3 matches)")
        
        # Display all stats
        st.subheader("All Performance Metrics")
        
        # Convert stats to DataFrame, excluding nested dictionaries
        stats_df = pd.DataFrame([
            {"Metric": key, "Value": value}
            for key, value in player_stats.items()
            if not isinstance(value, dict) and not isinstance(value, list)  # Skip nested structures
        ])
        
        # Format values
        for i, row in stats_df.iterrows():
            value = row["Value"]
            if isinstance(value, float) and ("rate" in row["Metric"].lower() or "ratio" in row["Metric"].lower() or "avg" in row["Metric"].lower()):
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