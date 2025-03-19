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
from utils.app_utils import display_code_example, format_json, display_json, load_demo_data, json_to_df, create_kda_chart, safe_get
from utils.logger import get_logger, log_exception, setup_logging
from utils.env_loader import load_env_file

# Set up logger
logger = get_logger("MatchHistory")
logger.info("Match History page loaded")

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
    page_title="Match History - S2Match SDK Companion",
    page_icon="🎮",
    layout="wide"
)

st.title("Match History")
st.subheader("Explore player match data and performance statistics")

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
    ### Match History Methods
    
    The S2Match SDK provides several methods for retrieving match data:
    
    1. **`fetch_matches_by_player_uuid`**: Fetch raw match data for a specific player.
       - Parameters: `player_uuid`, `page_size` (default: 10), `max_matches` (default: 100)
       - Returns: List of match data dictionaries (raw API format)
    
    2. **`get_matches_by_player_uuid`**: Fetch and transform match data for a specific player into SMITE 2 format.
       - Parameters: `player_uuid`, `page_size` (default: 10), `max_matches` (default: 100)
       - Returns: List of transformed match data dictionaries (SMITE 2 format)
    
    3. **`fetch_matches_by_instance`**: Fetch raw match data for a specific match instance.
       - Parameters: `instance_id`, `page_size` (default: 10)
       - Returns: List of match dictionaries (raw API format)
    
    4. **`get_matches_by_instance`**: Fetch and transform match data for a specific instance into SMITE 2 format.
       - Parameters: `instance_id`, `page_size` (default: 10)
       - Returns: List of transformed match dictionaries (SMITE 2 format)
    
    ### API Endpoints Used
    
    These methods interact with the following RallyHere Environment API endpoints:
    
    - `/match/v1/player/{player_uuid}/match` - Get match history for a specific player
    - `/match/v1/match` - Get matches by instance ID
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
        max_matches = st.number_input("Max Matches", min_value=1, max_value=100, value=10)
        
else:
    # Using player from previous page
    st.info(f"Using player UUID: {player_uuid}")
    max_matches = st.number_input("Max Matches", min_value=1, max_value=100, value=10)

# Display Code Example
with st.expander("Code Example", expanded=False):
    code_example = f"""
    from s2match import S2Match
    
    # Initialize the SDK
    sdk = S2Match()
    
    # Get match history for a player
    matches = sdk.get_matches_by_player_uuid(
        player_uuid="{player_uuid}",
        max_matches={max_matches}
    )
    
    # Process the match data
    for match in matches:
        print(f"Match ID: {{match.get('match_id')}}")
        print(f"God: {{match.get('god_name')}}")
        print(f"Mode: {{match.get('mode')}}")
        
        # Access basic stats
        basic_stats = match.get("basic_stats", {{}})
        kills = basic_stats.get("Kills", 0)
        deaths = basic_stats.get("Deaths", 0)
        assists = basic_stats.get("Assists", 0)
        
        print(f"K/D/A: {{kills}}/{{deaths}}/{{assists}}")
        
        # Calculate KDA ratio
        kda_ratio = (kills + assists) / max(deaths, 1)
        print(f"KDA Ratio: {{kda_ratio:.2f}}")
        
        # Check if the player won
        if match.get("team_id") == match.get("winning_team"):
            print("Result: Victory")
        else:
            print("Result: Defeat")
            
        print("-" * 30)
    """
    
    display_code_example("Match History Retrieval", code_example)

# Fetch Button
fetch_button = st.button("Fetch Match History")

# Match Results Section
if fetch_button:
    with st.spinner("Fetching match history..."):
        if not player_uuid:
            st.error("Please enter a player UUID")
            st.stop()
            
        if demo_mode:
            # Demo mode - use mock data
            st.info("Using demo data for match history")
            
            # Filter demo matches by player UUID
            matches = []
            for match in demo_data.get("matches", []):
                if match.get("player_uuid") == player_uuid:
                    matches.append(match)
                    
            # If no matches found for this player, use all demo matches
            if not matches:
                matches = demo_data.get("matches", [])
                
            # Limit to max_matches
            matches = matches[:max_matches]
        else:
            # Real API mode
            try:
                matches = sdk.get_matches_by_player_uuid(
                    player_uuid=player_uuid,
                    max_matches=max_matches
                )
            except Exception as e:
                st.error(f"Error fetching match history: {str(e)}")
                st.stop()
        
        # Store matches in session state for reuse
        if "all_matches" not in st.session_state:
            st.session_state["all_matches"] = matches.copy()

        if "filtered_matches" not in st.session_state:
            st.session_state["filtered_matches"] = st.session_state["all_matches"].copy()

        if "filter_applied" not in st.session_state:
            st.session_state["filter_applied"] = False
        
        # Display match count
        if not matches:
            st.warning("No matches found for this player")
            st.stop()
            
        matches_to_display = st.session_state["filtered_matches"] if st.session_state["filter_applied"] else st.session_state["all_matches"]
        st.success(f"Found {len(matches_to_display)} matches!" + (" (filtered)" if st.session_state["filter_applied"] else ""))
        
        # Simple filtering section
        st.subheader("Filter Matches")
        
        # Get unique values for filters from all_matches
        all_matches = st.session_state["all_matches"]
        all_gods = sorted(set(match.get("god_name") for match in all_matches if match.get("god_name")))
        all_modes = sorted(set(match.get("mode") for match in all_matches if match.get("mode")))
        
        # Initialize filter state if not exists
        if "filter_god" not in st.session_state:
            st.session_state["filter_god"] = "Any"
        if "filter_mode" not in st.session_state:
            st.session_state["filter_mode"] = "Any"
        if "filter_result" not in st.session_state:
            st.session_state["filter_result"] = "Any"
        if "filter_min_kills" not in st.session_state:
            st.session_state["filter_min_kills"] = 0
        if "filter_min_kda" not in st.session_state:
            st.session_state["filter_min_kda"] = 0.0
        
        # Define callback functions for filter changes
        def update_god_filter():
            st.session_state["filter_god"] = st.session_state["god_selector"]
        
        def update_mode_filter():
            st.session_state["filter_mode"] = st.session_state["mode_selector"]
        
        def update_result_filter():
            st.session_state["filter_result"] = st.session_state["result_selector"]
        
        def update_min_kills():
            st.session_state["filter_min_kills"] = st.session_state["kills_input"]
        
        def update_min_kda():
            st.session_state["filter_min_kda"] = st.session_state["kda_input"]
        
        # Create a layout with columns
        with st.container():
            st.info("Use the options below to filter match results, then click 'Apply Filters'.")
            
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                # Basic filters
                st.selectbox("God/Character", 
                             options=["Any"] + all_gods, 
                             index=0 if st.session_state["filter_god"] == "Any" else 1 + all_gods.index(st.session_state["filter_god"]) if st.session_state["filter_god"] in all_gods else 0,
                             key="god_selector",
                             on_change=update_god_filter)
                
                st.selectbox("Game Mode", 
                             options=["Any"] + all_modes, 
                             index=0 if st.session_state["filter_mode"] == "Any" else 1 + all_modes.index(st.session_state["filter_mode"]) if st.session_state["filter_mode"] in all_modes else 0,
                             key="mode_selector",
                             on_change=update_mode_filter)
                
                st.radio("Result", 
                         options=["Any", "Wins Only", "Losses Only"], 
                         index=["Any", "Wins Only", "Losses Only"].index(st.session_state["filter_result"]),
                         key="result_selector",
                         on_change=update_result_filter)
            
            with filter_col2:
                # Performance filters
                st.number_input("Minimum Kills", 
                               min_value=0, 
                               value=st.session_state["filter_min_kills"],
                               key="kills_input",
                               on_change=update_min_kills)
                
                st.number_input("Minimum KDA", 
                               min_value=0.0, 
                               value=st.session_state["filter_min_kda"], 
                               step=0.5,
                               key="kda_input",
                               on_change=update_min_kda)
            
            # Add buttons for applying and resetting filters
            col1, col2 = st.columns(2)
            
            def apply_filters():
                # Create filter dictionary
                filters = {}
                
                if st.session_state["filter_god"] != "Any":
                    filters["god_name"] = st.session_state["filter_god"]
                
                if st.session_state["filter_mode"] != "Any":
                    filters["mode"] = st.session_state["filter_mode"]
                
                if st.session_state["filter_result"] == "Wins Only":
                    filters["win_only"] = True
                elif st.session_state["filter_result"] == "Losses Only":
                    filters["win_only"] = False
                
                if st.session_state["filter_min_kills"] > 0:
                    filters["min_kills"] = st.session_state["filter_min_kills"]
                
                if st.session_state["filter_min_kda"] > 0:
                    filters["min_kda"] = st.session_state["filter_min_kda"]
                
                # Apply filtering
                if filters:
                    if demo_mode:
                        # Manual filtering for demo mode
                        filtered_matches = []
                        for match in st.session_state["all_matches"]:
                            include = True
                            
                            # Filter by god name
                            if "god_name" in filters and match.get("god_name") != filters["god_name"]:
                                include = False
                            
                            # Filter by game mode
                            if "mode" in filters and match.get("mode") != filters["mode"]:
                                include = False
                            
                            # Filter by win/loss
                            if "win_only" in filters:
                                if filters["win_only"] and match.get("team_id") != match.get("winning_team"):
                                    include = False
                                elif filters["win_only"] == False and match.get("team_id") == match.get("winning_team"):
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
                    else:
                        # Use SDK's filter_matches method
                        filtered_matches = sdk.filter_matches(st.session_state["all_matches"], filters)
                
                # Save filtered matches to session state
                st.session_state["filtered_matches"] = filtered_matches
                st.session_state["filter_applied"] = True
                
                # Update the display count
                if len(filtered_matches) == 0:
                    st.warning("No matches match the filter criteria")
                else:
                    st.success(f"Filtered to {len(filtered_matches)} matches using {len(filters)} criteria")
                
            def reset_filters():
                # Reset filter selections
                st.session_state["filter_god"] = "Any"
                st.session_state["filter_mode"] = "Any"
                st.session_state["filter_result"] = "Any"
                st.session_state["filter_min_kills"] = 0
                st.session_state["filter_min_kda"] = 0.0
                
                # Reset data
                st.session_state["filtered_matches"] = st.session_state["all_matches"]
                st.session_state["filter_applied"] = False
                
                st.success("Filters reset - showing all matches")
            
            with col1:
                if st.button("Apply Filters"):
                    apply_filters()
            
            with col2:
                if st.button("Reset Filters"):
                    reset_filters()
        
        # Use filtered matches for display if filters applied
        matches = st.session_state["filtered_matches"] if st.session_state["filter_applied"] else st.session_state["all_matches"]
        
        # Show example code
        with st.expander("SDK Filter Example"):
            example_code = f"""
            from s2match import S2Match
            
            # Initialize the SDK
            sdk = S2Match()
            
            # Get match history for a player
            matches = sdk.get_matches_by_player_uuid(
                player_uuid="{player_uuid}",
                max_matches={max_matches}
            )
            
            # Define filter criteria
            filters = {{
                "god_name": "{st.session_state['filter_god'] if st.session_state['filter_god'] != 'Any' else 'Anubis'}",
                "mode": "{st.session_state['filter_mode'] if st.session_state['filter_mode'] != 'Any' else 'Conquest'}",
                "win_only": {str(st.session_state['filter_result'] == 'Wins Only').lower()},
                "min_kills": {st.session_state['filter_min_kills'] if st.session_state['filter_min_kills'] > 0 else 5},
                "min_kda": {st.session_state['filter_min_kda'] if st.session_state['filter_min_kda'] > 0 else 2.0}
            }}
            
            # Apply filters
            filtered_matches = sdk.filter_matches(matches, filters)
            
            print(f"Filtered from {{len(matches)}} to {{len(filtered_matches)}} matches")
            """
            
            st.code(example_code, language="python")
        
        # Performance Overview
        st.subheader("Performance Overview")
        
        # Calculate some aggregate stats
        total_matches = len(matches)
        wins = sum(1 for match in matches if match.get("team_id") == match.get("winning_team"))
        losses = total_matches - wins
        
        total_kills = sum(match.get("basic_stats", {}).get("Kills", 0) for match in matches)
        total_deaths = sum(match.get("basic_stats", {}).get("Deaths", 0) for match in matches)
        total_assists = sum(match.get("basic_stats", {}).get("Assists", 0) for match in matches)
        
        avg_kills = total_kills / total_matches if total_matches > 0 else 0
        avg_deaths = total_deaths / total_matches if total_matches > 0 else 0
        avg_assists = total_assists / total_matches if total_matches > 0 else 0
        
        kda_ratio = (total_kills + total_assists) / max(total_deaths, 1)
        win_rate = wins / total_matches if total_matches > 0 else 0
        
        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Matches", total_matches)
            st.metric("Win Rate", f"{win_rate:.1%}")
            
        with col2:
            st.metric("Wins", wins)
            st.metric("Losses", losses)
            
        with col3:
            st.metric("Avg K/D/A", f"{avg_kills:.1f}/{avg_deaths:.1f}/{avg_assists:.1f}")
            st.metric("KDA Ratio", f"{kda_ratio:.2f}")
            
        with col4:
            st.metric("Total Kills", total_kills)
            st.metric("Total Deaths", total_deaths)
        
        # Performance Visualization
        st.subheader("Match Performance")
        
        # Create KDA chart using the utility function
        try:
            fig = create_kda_chart(matches, player_name="Player")
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating performance chart: {str(e)}")
        
        # God/Character Performance
        st.subheader("God/Character Performance")
        
        # Count matches by god
        god_stats = {}
        for match in matches:
            god = match.get("god_name", "Unknown")
            if god not in god_stats:
                god_stats[god] = {
                    "matches": 0,
                    "wins": 0,
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0
                }
                
            god_stats[god]["matches"] += 1
            
            if match.get("team_id") == match.get("winning_team"):
                god_stats[god]["wins"] += 1
                
            basic_stats = match.get("basic_stats", {})
            god_stats[god]["kills"] += basic_stats.get("Kills", 0)
            god_stats[god]["deaths"] += basic_stats.get("Deaths", 0)
            god_stats[god]["assists"] += basic_stats.get("Assists", 0)
        
        # Convert to DataFrame for visualization
        god_df = pd.DataFrame([
            {
                "God": god,
                "Matches": stats["matches"],
                "Wins": stats["wins"],
                "Losses": stats["matches"] - stats["wins"],
                "Win Rate": stats["wins"] / stats["matches"] if stats["matches"] > 0 else 0,
                "Avg Kills": stats["kills"] / stats["matches"] if stats["matches"] > 0 else 0,
                "Avg Deaths": stats["deaths"] / stats["matches"] if stats["matches"] > 0 else 0,
                "Avg Assists": stats["assists"] / stats["matches"] if stats["matches"] > 0 else 0,
                "KDA": (stats["kills"] + stats["assists"]) / max(stats["deaths"], 1)
            }
            for god, stats in god_stats.items()
        ])
        
        if not god_df.empty:
            # Sort by number of matches
            god_df = god_df.sort_values("Matches", ascending=False)
            
            # Display as a table
            st.dataframe(
                god_df.style.format({
                    "Win Rate": "{:.1%}",
                    "Avg Kills": "{:.1f}",
                    "Avg Deaths": "{:.1f}",
                    "Avg Assists": "{:.1f}",
                    "KDA": "{:.2f}"
                }),
                use_container_width=True
            )
            
            # Create a bar chart for win rates by god
            try:
                win_rate_fig = px.bar(
                    god_df,
                    x="God",
                    y="Win Rate",
                    color="Matches",
                    text_auto=".0%",
                    title="Win Rate by God/Character",
                    labels={"Win Rate": "Win Rate", "God": "God/Character", "Matches": "Number of Matches"},
                    height=400,
                    color_continuous_scale=px.colors.sequential.Blues
                )
                win_rate_fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(win_rate_fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating win rate chart: {str(e)}")
        
        # Match List
        st.subheader("Match List")
        
        # Create tabs for match details
        match_tabs = st.tabs(["Match Cards", "Table View", "Raw Data"])
        
        with match_tabs[0]:
            # Match Cards View
            # Display matches in a grid of cards
            cols_per_row = 3
            rows = [matches[i:i+cols_per_row] for i in range(0, len(matches), cols_per_row)]
            
            for row in rows:
                cols = st.columns(cols_per_row)
                
                for i, match in enumerate(row):
                    with cols[i]:
                        # Extract match info
                        match_id = match.get("match_id", "Unknown")
                        god = match.get("god_name", "Unknown")
                        mode = match.get("mode", "Unknown")
                        map_name = match.get("map", "Unknown")
                        
                        # Match result
                        result = "Victory" if match.get("team_id") == match.get("winning_team") else "Defeat"
                        result_color = "#4CAF50" if result == "Victory" else "#F44336"
                        
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
                        
                        # Create card
                        st.markdown(f"""
                        <div style="
                            border: 1px solid #ddd;
                            border-radius: 5px;
                            padding: 15px;
                            margin-bottom: 20px;
                            background-color: #f8f9fa;
                        ">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                <span style="font-weight: bold;">{god}</span>
                                <span style="color: {result_color}; font-weight: bold;">{result}</span>
                            </div>
                            <p style="margin-bottom: 5px;"><span style="font-weight: bold;">Mode:</span> {mode}</p>
                            <p style="margin-bottom: 5px;"><span style="font-weight: bold;">Map:</span> {map_name}</p>
                            <p style="margin-bottom: 5px;"><span style="font-weight: bold;">Date:</span> {match_date}</p>
                            <p style="margin-bottom: 5px;"><span style="font-weight: bold;">K/D/A:</span> {kills}/{deaths}/{assists}</p>
                            <p style="margin-bottom: 0;"><span style="font-weight: bold;">Match ID:</span> {match_id}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add button to view detailed match
                        if st.button("View Details", key=f"view_match_{match_id}"):
                            st.session_state["selected_match"] = match
                        
        with match_tabs[1]:
            # Table View
            # Convert matches to DataFrame
            match_data = []
            for match in matches:
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
                    "Match ID": match.get("match_id", "Unknown"),
                    "Date": match_date,
                    "God": match.get("god_name", "Unknown"),
                    "Mode": match.get("mode", "Unknown"),
                    "Map": match.get("map", "Unknown"),
                    "Result": result,
                    "Kills": basic_stats.get("Kills", 0),
                    "Deaths": basic_stats.get("Deaths", 0),
                    "Assists": basic_stats.get("Assists", 0),
                    "KDA": (basic_stats.get("Kills", 0) + basic_stats.get("Assists", 0)) / max(basic_stats.get("Deaths", 1), 1),
                    "Damage": basic_stats.get("TotalDamage", 0),
                    "Healing": basic_stats.get("TotalAllyHealing", 0) + basic_stats.get("TotalSelfHealing", 0)
                })
            
            match_df = pd.DataFrame(match_data)
            
            # Display as a table
            st.dataframe(
                match_df.style.format({
                    "KDA": "{:.2f}",
                    "Damage": "{:,.0f}",
                    "Healing": "{:,.0f}"
                }),
                use_container_width=True
            )
            
        with match_tabs[2]:
            # Raw Data View
            st.write("Raw match data in JSON format:")
            display_json(matches, title="Match Data")
            
            # Download button
            json_str = json.dumps(matches, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name="match_history.json",
                mime="application/json"
            )
            
# Detailed Match View
if "selected_match" in st.session_state:
    match = st.session_state["selected_match"]
    
    st.markdown("---")
    st.subheader(f"Match Details: {match.get('match_id', 'Unknown')}")
    
    # Create tabs for different sections
    detail_tabs = st.tabs(["Overview", "Performance", "Items", "Raw Data"])
    
    with detail_tabs[0]:
        # Overview tab
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Match information
            st.write("**Match Information**")
            
            # Format date
            match_date = "Unknown"
            if match.get("match_start"):
                try:
                    date_obj = datetime.fromisoformat(match.get("match_start").replace('Z', '+00:00'))
                    match_date = date_obj.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
                    
            # Calculate duration
            duration = "Unknown"
            if match.get("match_start") and match.get("match_end"):
                try:
                    start_time = datetime.fromisoformat(match.get("match_start").replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(match.get("match_end").replace('Z', '+00:00'))
                    duration_seconds = (end_time - start_time).total_seconds()
                    minutes = int(duration_seconds // 60)
                    seconds = int(duration_seconds % 60)
                    duration = f"{minutes}m {seconds}s"
                except:
                    pass
            
            # Match result
            result = "Victory" if match.get("team_id") == match.get("winning_team") else "Defeat"
            result_color = "#4CAF50" if result == "Victory" else "#F44336"
            
            # Display match info
            st.markdown(f"""
            - **Date**: {match_date}
            - **Duration**: {duration}
            - **Mode**: {match.get("mode", "Unknown")}
            - **Map**: {match.get("map", "Unknown")}
            - **God/Character**: {match.get("god_name", "Unknown")}
            - **Result**: <span style="color: {result_color}; font-weight: bold;">{result}</span>
            - **Team**: {match.get("team_id", "Unknown")}
            - **Winning Team**: {match.get("winning_team", "Unknown")}
            """, unsafe_allow_html=True)
            
        with col2:
            # Basic stats
            st.write("**Performance Stats**")
            
            basic_stats = match.get("basic_stats", {})
            
            # Create a more visual representation of K/D/A
            kills = basic_stats.get("Kills", 0)
            deaths = basic_stats.get("Deaths", 0)
            assists = basic_stats.get("Assists", 0)
            
            kda_cols = st.columns(3)
            with kda_cols[0]:
                st.metric("Kills", kills)
            with kda_cols[1]:
                st.metric("Deaths", deaths)
            with kda_cols[2]:
                st.metric("Assists", assists)
                
            # Calculate KDA ratio
            kda_ratio = (kills + assists) / max(deaths, 1)
            
            # Additional stats in columns
            stat_cols = st.columns(3)
            
            with stat_cols[0]:
                st.metric("KDA Ratio", f"{kda_ratio:.2f}")
                st.metric("Player Level", basic_stats.get("PlayerLevel", "N/A"))
                
            with stat_cols[1]:
                st.metric("Total Damage", f"{basic_stats.get('TotalDamage', 0):,}")
                st.metric("Damage Taken", f"{basic_stats.get('TotalDamageTaken', 0):,}")
                
            with stat_cols[2]:
                st.metric("Allied Healing", f"{basic_stats.get('TotalAllyHealing', 0):,}")
                st.metric("Self Healing", f"{basic_stats.get('TotalSelfHealing', 0):,}")
    
    with detail_tabs[1]:
        # Performance tab - more detailed stats
        st.write("**Detailed Performance Metrics**")
        
        basic_stats = match.get("basic_stats", {})
        damage_breakdown = match.get("damage_breakdown", {})
        
        # Create a pie chart of damage breakdown if available
        if damage_breakdown:
            # Try to create meaningful categories
            damage_categories = {}
            
            # Process damage breakdown data
            for category, values in damage_breakdown.items():
                if isinstance(values, dict):
                    for stat, value in values.items():
                        if isinstance(value, (int, float)) and value > 0:
                            key = f"{category}: {stat}"
                            damage_categories[key] = value
            
            if damage_categories:
                # Convert to DataFrame for visualization
                damage_df = pd.DataFrame([
                    {"Category": cat, "Damage": val}
                    for cat, val in damage_categories.items()
                ])
                
                # Create pie chart
                fig = px.pie(
                    damage_df,
                    values="Damage",
                    names="Category",
                    title="Damage Breakdown",
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
                
        # Display other performance stats in a table
        performance_data = {}
        
        # Add relevant stats from basic_stats
        for key, value in basic_stats.items():
            if isinstance(value, (int, float)):
                performance_data[key] = value
                
        # If we have data, display it
        if performance_data:
            # Convert to DataFrame
            perf_df = pd.DataFrame([
                {"Metric": key, "Value": value}
                for key, value in performance_data.items()
            ])
            
            st.dataframe(perf_df, use_container_width=True)
    
    with detail_tabs[2]:
        # Items tab - show items used in the match
        st.write("**Items Used**")
        
        items = match.get("items", {})
        
        if items:
            # Create a grid of item cards
            cols_per_row = 3
            item_list = list(items.items())
            rows = [item_list[i:i+cols_per_row] for i in range(0, len(item_list), cols_per_row)]
            
            for row in rows:
                cols = st.columns(cols_per_row)
                
                for i, (slot, item) in enumerate(row):
                    with cols[i]:
                        # Create card for item
                        if isinstance(item, dict) and "DisplayName" in item:
                            st.markdown(f"""
                            <div style="
                                border: 1px solid #ddd;
                                border-radius: 5px;
                                padding: 10px;
                                margin-bottom: 10px;
                                background-color: #f8f9fa;
                                text-align: center;
                            ">
                                <p style="font-weight: bold; margin-bottom: 5px;">{item["DisplayName"]}</p>
                                <p style="margin-bottom: 0; color: #666; font-size: 0.8em;">{slot}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.write(f"{slot}: {item}")
        else:
            st.info("No item data available for this match")
    
    with detail_tabs[3]:
        # Raw Data tab
        st.write("Raw match data in JSON format:")
        display_json(match, title="Match Data")

# Footer with page navigation
st.markdown("---")
prev_page = st.button("Previous: Player Lookup")
next_page = st.button("Next: Player Statistics")

if prev_page:
    import streamlit as st
    st.switch_page("pages/1_Player_Lookup.py")
    
if next_page:
    import streamlit as st
    st.switch_page("pages/3_Player_Statistics.py") 