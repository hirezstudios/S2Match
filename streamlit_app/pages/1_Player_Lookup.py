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
    display_name = st.text_input("Display Name", value="Weak3n")
    
with col2:
    platform = st.selectbox(
        "Platform (Optional)",
        options=["Any", "Steam", "XboxLive", "PlayStation", "EpicGames", "Discord"],
        index=0
    )
    
    include_linked = st.checkbox("Include Linked Accounts", value=True)

search_button = st.button("Search Players")

# Display Code Example
with st.expander("Code Example", expanded=False):
    platform_code = f'"{platform}"' if platform != "Any" else "None"
    code_example = f"""
    from s2match import S2Match
    
    # Initialize the SDK
    sdk = S2Match()
    
    # Look up player by display name
    player_data = sdk.fetch_player_with_displayname(
        display_names=["{display_name}"],
        platform={platform_code},
        include_linked_portals={str(include_linked)}
    )
    
    # Process results
    display_names = player_data.get("display_names", [])
    for display_name_dict in display_names:
        for name, players in display_name_dict.items():
            print(f"Results for '{{name}}':")
            for player in players:
                print(f"  Player UUID: {{player.get('player_uuid')}}")
                print(f"  Platform: {{player.get('platform')}}")
                
                # Access linked portals if included
                linked_portals = player.get("linked_portals", [])
                print(f"  Linked portals: {{len(linked_portals)}}")
                for portal in linked_portals:
                    print(f"    - {{portal.get('platform')}}: {{portal.get('player_uuid')}}")
    """
    
    display_code_example("Player Lookup", code_example)

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
            
            player_data = mock_response
            
        else:
            # Real API mode
            try:
                logger.debug(f"Making API call to fetch player with display name: {display_name}")
                platform_param = None if platform == "Any" else platform
                
                add_log_message("INFO", f"Sending API request with params: display_name={display_name}, platform={platform_param}, include_linked_portals={include_linked}")
                
                player_data = sdk.fetch_player_with_displayname(
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
        display_names = player_data.get("display_names", [])
        
        if not display_names or all(not players for name_dict in display_names for _, players in name_dict.items()):
            logger.warning(f"No players found with display name '{display_name}'")
            add_log_message("WARNING", f"No players found with display name '{display_name}'")
            st.warning(f"No players found with display name '{display_name}'")
        else:
            total_players = sum(len(players) for name_dict in display_names for _, players in name_dict.items())
            logger.info(f"Found {total_players} players matching '{display_name}'")
            add_log_message("INFO", f"Found {total_players} players matching '{display_name}'")
            st.success(f"Found {total_players} players!")
            
            # Counter for player cards
            player_counter = 0
            
            # Process each display name result
            for name_dict in display_names:
                for name, players in name_dict.items():
                    st.subheader(f"Results for '{name}'")
                    
                    # Create a grid of player cards
                    cols = st.columns(min(3, len(players)))
                    
                    for i, player in enumerate(players):
                        player_counter += 1
                        col_idx = i % len(cols)
                        
                        with cols[col_idx]:
                            # Player card with styling
                            st.markdown(f"""
                            <div style="
                                border: 1px solid #ddd;
                                border-radius: 5px;
                                padding: 15px;
                                margin-bottom: 20px;
                                background-color: #f8f9fa;
                            ">
                                <h3 style="margin-top: 0;">{name}</h3>
                                <p><strong>Platform:</strong> {player.get('platform', 'Unknown')}</p>
                                <p><strong>Player UUID:</strong> {player.get('player_uuid', 'Unknown')}</p>
                                <p><strong>Player ID:</strong> {player.get('player_id', 'Unknown')}</p>
                                <p><strong>Linked Accounts:</strong> {len(player.get('linked_portals', []))}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Add buttons for additional actions
                            # Create a unique key for each button
                            view_key = f"view_player_{hash(str(player.get('player_uuid', '')))}"
                            if st.button("View Details", key=view_key):
                                st.session_state['selected_player'] = player
                                st.session_state['selected_player_name'] = name
                                add_log_message("INFO", f"Selected player: {name} (UUID: {player.get('player_uuid', 'Unknown')})")
                    
            # Display selected player details if any
            if 'selected_player' in st.session_state:
                player = st.session_state['selected_player']
                name = st.session_state.get('selected_player_name', 'Player')
                
                st.markdown("---")
                st.subheader(f"Detailed Player Information: {name}")
                
                # Create tabs for different sections
                player_tabs = st.tabs(["Player Info", "Linked Accounts", "Raw JSON"])
                
                with player_tabs[0]:
                    # Convert player data to DataFrame for display
                    player_info = {k: v for k, v in player.items() if k != 'linked_portals'}
                    player_df = pd.DataFrame([player_info])
                    
                    # Display as a table
                    st.dataframe(player_df)
                
                with player_tabs[1]:
                    linked_portals = player.get('linked_portals', [])
                    
                    if not linked_portals:
                        st.info("No linked accounts found for this player.")
                    else:
                        st.write(f"{len(linked_portals)} linked accounts found:")
                        
                        # Create a DataFrame from linked portals
                        linked_df = pd.DataFrame(linked_portals)
                        st.dataframe(linked_df)
                        
                        # Create a graph visualization of linked accounts
                        if len(linked_portals) > 0:
                            try:
                                # Prepare data for network graph
                                nodes = [{"id": player.get('player_uuid'), "label": name, "platform": player.get('platform', 'Unknown')}]
                                edges = []
                                
                                for portal in linked_portals:
                                    portal_uuid = portal.get('player_uuid')
                                    portal_platform = portal.get('platform', 'Unknown')
                                    
                                    nodes.append({"id": portal_uuid, "label": f"{portal_platform} Account", "platform": portal_platform})
                                    edges.append({"source": player.get('player_uuid'), "target": portal_uuid})
                                
                                # Create a network visualization (simplified for Streamlit)
                                node_df = pd.DataFrame(nodes)
                                
                                # Use Plotly to create a simple visualization
                                import plotly.graph_objects as go
                                import networkx as nx
                                
                                # Create NetworkX graph
                                G = nx.Graph()
                                
                                # Add nodes
                                for node in nodes:
                                    G.add_node(node["id"], label=node["label"], platform=node["platform"])
                                
                                # Add edges
                                for edge in edges:
                                    G.add_edge(edge["source"], edge["target"])
                                
                                # Position nodes in a circle
                                pos = nx.spring_layout(G)
                                
                                # Create node trace
                                node_x = []
                                node_y = []
                                node_text = []
                                node_color = []
                                
                                platform_colors = {
                                    "Steam": "#1b2838",
                                    "XboxLive": "#107c10",
                                    "PlayStation": "#003791",
                                    "EpicGames": "#2a2a2a",
                                    "Discord": "#7289da",
                                    "Unknown": "#888888"
                                }
                                
                                for node, position in pos.items():
                                    node_x.append(position[0])
                                    node_y.append(position[1])
                                    node_label = G.nodes[node]["label"]
                                    node_platform = G.nodes[node]["platform"]
                                    node_text.append(f"{node_label}<br>Platform: {node_platform}")
                                    node_color.append(platform_colors.get(node_platform, "#888888"))
                                
                                node_trace = go.Scatter(
                                    x=node_x, y=node_y,
                                    mode='markers',
                                    hoverinfo='text',
                                    text=node_text,
                                    marker=dict(
                                        showscale=False,
                                        color=node_color,
                                        size=20,
                                        line=dict(width=2, color='#ffffff')
                                    )
                                )
                                
                                # Create edge trace
                                edge_x = []
                                edge_y = []
                                
                                for edge in G.edges():
                                    x0, y0 = pos[edge[0]]
                                    x1, y1 = pos[edge[1]]
                                    edge_x.extend([x0, x1, None])
                                    edge_y.extend([y0, y1, None])
                                
                                edge_trace = go.Scatter(
                                    x=edge_x, y=edge_y,
                                    line=dict(width=1, color='#888'),
                                    hoverinfo='none',
                                    mode='lines'
                                )
                                
                                # Create figure
                                fig = go.Figure(data=[edge_trace, node_trace],
                                    layout=go.Layout(
                                        title=f'Linked Accounts for {name}',
                                        showlegend=False,
                                        hovermode='closest',
                                        margin=dict(b=20, l=5, r=5, t=40),
                                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                                    )
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                            except Exception as e:
                                error_msg = log_exception(logger, e, "Error creating visualization")
                                st.error(f"Error creating visualization: {str(e)}")
                
                with player_tabs[2]:
                    # Display raw JSON
                    display_json(player, title="Player Data")
            
            # Display full response
            st.markdown("---")
            with st.expander("Full Response Data", expanded=False):
                # Use display_json with use_expander=False since we're already in an expander
                display_json(player_data, title="API Response", use_expander=False)
            
            # Show examples of how to use the returned data
            with st.expander("Using the Response Data", expanded=False):
                st.markdown("""
                ### How to Extract Player UUID from Response
                
                The response data is structured as a nested dictionary. Here's how to extract player UUIDs:
                """)
                
                extraction_code = """
                # Process response data
                player_uuids = []
                display_names = player_data.get("display_names", [])
                for display_name_dict in display_names:
                    for name, players in display_name_dict.items():
                        for player in players:
                            player_uuid = player.get("player_uuid")
                            if player_uuid:
                                player_uuids.append(player_uuid)
                                
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

# Footer with page navigation
st.markdown("---")
next_page = st.button("Next: Match History")
if next_page:
    add_log_message("INFO", "Navigating to Match History page")
    import streamlit as st
    st.switch_page("pages/2_Match_History.py") 