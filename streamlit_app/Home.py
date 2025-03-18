import streamlit as st
import sys
import os
import json
import time
from pathlib import Path

# Add the parent directory to sys.path to import the S2Match SDK
parent_dir = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, parent_dir)

# Import utility functions
from utils.app_utils import load_css, display_code_example, format_json, display_json, load_demo_data
from utils.logger import setup_logging, get_logger, log_exception
from utils.env_loader import load_env_file

# Set up logging
setup_logging()
logger = get_logger("Home")
logger.info("Starting S2Match SDK Companion app")

# Load environment variables from .env file
env_vars = load_env_file()
logger.info("Environment variables loaded successfully")

# Import the S2Match SDK
try:
    from s2match import S2Match
    logger.info("S2Match SDK imported successfully")
except ImportError as e:
    error_msg = log_exception(logger, e, "Failed to import S2Match SDK")
    st.error("S2Match SDK not found. Make sure you're running the app from the correct directory.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="S2Match SDK Companion",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_css()

# Session state initialization
if "sdk_initialized" not in st.session_state:
    st.session_state.sdk_initialized = False
    st.session_state.sdk_instance = None
    st.session_state.demo_data = load_demo_data()
    st.session_state.log_messages = []
    logger.info("Session state initialized")

# Function to add log message to session state
def add_log_message(level, message):
    """Add a log message to the session state log and the logger."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
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

# Sidebar for authentication
with st.sidebar:
    st.title("S2Match SDK Configuration")
    
    # Environment variable inputs
    with st.expander("API Credentials", expanded=not st.session_state.sdk_initialized):
        # Pre-fill with values from .env file
        client_id = st.text_input(
            "Client ID", 
            value=env_vars.get("CLIENT_ID", ""),
            type="password"
        )
        
        client_secret = st.text_input(
            "Client Secret",
            value=env_vars.get("CLIENT_SECRET", ""),
            type="password"
        )
        
        base_url = st.text_input(
            "Base URL",
            value=env_vars.get("RH_BASE_URL", "")
        )
    
    # Advanced settings - not inside another expander
    with st.expander("Advanced Settings", expanded=False):
        cache_enabled = st.checkbox(
            "Enable Caching",
            value=env_vars.get("CACHE_ENABLED", True)
        )
        
        rate_limit_delay = st.slider(
            "Rate Limit Delay (seconds)",
            0.0, 2.0, env_vars.get("RATE_LIMIT_DELAY", 0.0), 0.1
        )
        
        log_level = st.selectbox(
            "Log Level",
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(
                env_vars.get("LOG_LEVEL", "INFO").upper()
            )
        )
    
    # Initialize SDK button
    if st.button("Initialize SDK"):
        try:
            # Log attempt
            add_log_message("INFO", "Attempting to initialize SDK...")
            
            # Set environment variables for SDK initialization
            os.environ["CLIENT_ID"] = client_id
            os.environ["CLIENT_SECRET"] = client_secret
            os.environ["RH_BASE_URL"] = base_url
            os.environ["LOG_LEVEL"] = log_level
            
            with st.spinner("Initializing SDK..."):
                # Initialize SDK instance
                sdk = S2Match(
                    client_id=client_id,
                    client_secret=client_secret,
                    base_url=base_url,
                    cache_enabled=cache_enabled,
                    rate_limit_delay=rate_limit_delay
                )
                
                # Test authentication
                token = sdk.get_access_token()
                
                # Store SDK instance in session state
                st.session_state.sdk_instance = sdk
                st.session_state.sdk_initialized = True
                
                add_log_message("INFO", "SDK initialized successfully. Access token obtained.")
                st.success("SDK initialized successfully! Access token obtained.")
        except Exception as e:
            error_msg = log_exception(logger, e, "Failed to initialize SDK")
            add_log_message("ERROR", f"Failed to initialize SDK: {str(e)}")
            st.error(f"Failed to initialize SDK: {str(e)}")
    
    # Display SDK status
    if st.session_state.sdk_initialized:
        st.success("SDK Status: Initialized")
    else:
        st.warning("SDK Status: Not Initialized")
    
    # Navigation info
    st.subheader("Navigation")
    st.info("""
    Use the pages in the sidebar to explore different SDK features:
    - Player Lookup: Search for players by name
    - Match History: View match data for players
    - Player Statistics: View player performance stats
    - Full Player Data: Comprehensive player analysis
    - API Explorer: Try any SDK method directly
    """)
    
    # App logs in sidebar
    with st.expander("Application Logs"):
        if st.session_state.log_messages:
            for log in st.session_state.log_messages:
                if log["level"] == "ERROR":
                    st.error(f"{log['timestamp']} - {log['message']}")
                elif log["level"] == "WARNING":
                    st.warning(f"{log['timestamp']} - {log['message']}")
                else:
                    st.info(f"{log['timestamp']} - {log['message']}")
        else:
            st.info("No logs yet.")
        
        if st.button("Clear Logs"):
            st.session_state.log_messages = []
            add_log_message("INFO", "Logs cleared")

# Main content
st.title("S2Match SDK Companion")
st.subheader("Interactive Explorer for SMITE 2 Match Data")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ## Welcome to the S2Match SDK Companion
    
    This interactive app demonstrates the capabilities of the S2Match SDK for retrieving and analyzing SMITE 2 match data through the RallyHere Environment API.
    
    ### What you can do:
    - Search for players by display name
    - View detailed match history with visualizations
    - Analyze player statistics and performance metrics
    - Explore comprehensive player data including linked accounts
    - Try out any SDK method directly through the API Explorer
    
    ### Getting Started
    1. Enter your API credentials in the sidebar
    2. Initialize the SDK to authenticate with the API
    3. Navigate to any of the feature pages to explore the data
    
    Each page includes example code snippets showing how to use the SDK in your own applications.
    """)
    
    # SDK Overview
    with st.expander("SDK Overview"):
        st.markdown("""
        The S2Match SDK provides a Python interface for accessing SMITE 2 match data through the RallyHere Environment API. 
        
        ### Key Features
        - **Authentication**: Simple token-based authentication with automatic refresh
        - **Match Data**: Fetch detailed match history for players and specific matches
        - **Player Stats**: Access player statistics and performance metrics
        - **Player Lookup**: Find players by display name, platform, or other identifiers
        - **Data Transformation**: Convert raw API responses into SMITE 2-friendly formats
        - **Item Enrichment**: Automatically populate item details from local database
        - **Caching**: Built-in response caching to improve performance and respect rate limits
        
        ### API Endpoints
        The SDK interacts with the following RallyHere Environment API endpoints:
        """)
        
        endpoints = {
            "Authentication": ["/users/v2/oauth/token - Obtain access token for API requests"],
            "Player Lookup": [
                "/users/v1/player - Look up players by display name and platform",
                "/users/v1/player/{player_id}/linked_portals - Get linked portal accounts",
                "/users/v1/platform-user - Find player by platform identity"
            ],
            "Match Data": [
                "/match/v1/player/{player_uuid}/match - Get match history for a player",
                "/match/v1/match - Get matches by instance ID"
            ],
            "Player Statistics": ["/match/v1/player/{player_uuid}/stats - Get player statistics"],
            "Ranking": [
                "/rank/v2/player/{player_uuid}/rank - Get player's rank list",
                "/rank/v3/rank/{rank_id} - Get rank configuration",
                "/rank/v2/player/{player_uuid}/rank/{rank_id} - Get detailed rank information"
            ]
        }
        
        for category, endpoint_list in endpoints.items():
            st.write(f"**{category}**")
            for endpoint in endpoint_list:
                st.write(f"- `{endpoint}`")

with col2:
    # Quick example
    st.subheader("Quick Example")
    code_example = """
    from s2match import S2Match

    # Initialize the SDK
    sdk = S2Match()

    # Look up a player by display name
    player_data = sdk.fetch_player_with_displayname(
        display_names=["PlayerName"],
        platform="Steam"
    )

    # Get player UUID
    player_uuid = None
    display_names = player_data.get("display_names", [])
    for display_name_dict in display_names:
        for name, players in display_name_dict.items():
            if players:
                player_uuid = players[0].get("player_uuid")
                break

    # Get player's match history
    if player_uuid:
        matches = sdk.get_matches_by_player_uuid(
            player_uuid=player_uuid,
            max_matches=5
        )
        
        # Display match information
        for match in matches:
            print(f"Match ID: {match.get('match_id')}")
            print(f"God: {match.get('god_name')}")
            stats = match.get("basic_stats", {})
            print(f"K/D/A: {stats.get('Kills')}/{stats.get('Deaths')}/{stats.get('Assists')}")
    """
    
    st.code(code_example, language="python")
    
    # Quick stats/demo data
    if st.session_state.sdk_initialized:
        st.subheader("Live SDK Status")
        st.write("SDK is connected and ready to use!")
        
        try:
            # Show token expiry
            token_expiry = st.session_state.sdk_instance._token_expiry
            import time
            current_time = time.time()
            expiry_seconds = int(token_expiry - current_time)
            
            st.metric("Token Valid For", f"{expiry_seconds} seconds")
            add_log_message("INFO", f"Access token valid for {expiry_seconds} seconds")
        except Exception as e:
            log_exception(logger, e, "Could not retrieve token expiry information")
            st.warning("Could not retrieve token expiry information")
    else:
        st.subheader("Demo Data")
        st.write("Initialize the SDK to use live data instead of demo data.")
        
        # Display some sample data metrics
        demo_data = st.session_state.demo_data
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Sample Players", len(demo_data.get("players", [])))
        with col2:
            st.metric("Sample Matches", len(demo_data.get("matches", [])))
            
        # Sample player card
        if demo_data.get("players"):
            sample_player = demo_data["players"][0]
            st.write("**Sample Player:**")
            st.write(f"Name: {sample_player.get('display_name')}")
            st.write(f"Platform: {sample_player.get('platform')}")
            st.write(f"Matches: {sample_player.get('matches_played')}")

# Footer
st.markdown("---")
st.markdown("S2Match SDK Companion | SMITE 2 Match Data Explorer") 