import streamlit as st
import sys
import os
import json
import inspect
from pathlib import Path

# Add the parent directory to sys.path to import the S2Match SDK
parent_dir = str(Path(__file__).parent.parent.parent.absolute())
sys.path.insert(0, parent_dir)

# Import utility functions
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
from utils.app_utils import display_code_example, format_json, display_json, load_demo_data
from utils.logger import get_logger, log_exception
from utils.env_loader import load_env_file

# Set up logger
logger = get_logger("APIExplorer")
logger.info("API Explorer page loaded")

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
    page_title="API Explorer - S2Match SDK Companion",
    page_icon="🎮",
    layout="wide"
)

st.title("API Explorer")
st.subheader("Directly interact with any SDK method")

# Check if SDK is initialized
if not st.session_state.get("sdk_initialized", False):
    st.warning("SDK is not initialized. Many methods may not work properly. Please initialize the SDK in the Home page.")
    add_log_message("WARNING", "Using SDK without initialization")
    demo_mode = True
else:
    demo_mode = False
    sdk = st.session_state.sdk_instance
    add_log_message("INFO", "Using initialized SDK")

# List of SDK methods
sdk_methods = [
    "fetch_player_with_displayname",
    "fetch_player_by_platform_user_id",
    "fetch_matches_by_player_uuid",
    "fetch_player_stats",
    "fetch_matches_by_instance",
    "get_matches_by_player_uuid",
    "get_player_stats",
    "get_matches_by_instance",
    "get_full_player_data_by_displayname",
    "extract_player_uuids"
]

# SDK Method Selection
st.subheader("Select SDK Method")
selected_method = st.selectbox("Choose a method to execute", sdk_methods)

# Method Description and Parameters
with st.expander("Method Details", expanded=True):
    # Get method details using inspect
    try:
        method = getattr(S2Match, selected_method)
        signature = inspect.signature(method)
        doc = method.__doc__
        
        st.markdown(f"### `{selected_method}`")
        st.markdown(doc)
        
        st.markdown("#### Parameters")
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
                
            param_type = param.annotation.__name__ if param.annotation != inspect.Parameter.empty else "Any"
            default = param.default if param.default != inspect.Parameter.empty else "Required"
            
            st.markdown(f"- **{param_name}** ({param_type}): {default}")
    except Exception as e:
        st.error(f"Error getting method details: {str(e)}")

# Parameter Input Section
st.subheader("Input Parameters")

params = {}

# Create input fields based on method signature
try:
    method = getattr(S2Match, selected_method)
    signature = inspect.signature(method)
    
    for param_name, param in signature.parameters.items():
        if param_name == 'self':
            continue
            
        default = param.default if param.default != inspect.Parameter.empty else None
        
        if param.annotation == bool or (default is not None and isinstance(default, bool)):
            params[param_name] = st.checkbox(f"{param_name}", value=bool(default) if default is not None else False)
        elif param.annotation == int or (default is not None and isinstance(default, int)):
            params[param_name] = st.number_input(f"{param_name}", value=int(default) if default is not None else 0)
        elif param.annotation == float or (default is not None and isinstance(default, float)):
            params[param_name] = st.number_input(f"{param_name}", value=float(default) if default is not None else 0.0)
        elif param.annotation == list or param_name in ["display_names"]:
            input_str = st.text_input(f"{param_name} (comma-separated for lists)", value="" if default is None else str(default))
            if input_str:
                if param_name == "display_names" or param.annotation == list:
                    params[param_name] = [item.strip() for item in input_str.split(",")]
                else:
                    params[param_name] = input_str
        else:
            params[param_name] = st.text_input(f"{param_name}", value="" if default is None else str(default))
except Exception as e:
    st.error(f"Error creating parameter inputs: {str(e)}")

# Execute Button
execute_button = st.button("Execute Method")

# Result Section
if execute_button:
    with st.spinner(f"Executing {selected_method}..."):
        if demo_mode and selected_method not in ["get_access_token"]:
            st.info("Using demo mode. Results will be simulated.")
            
            # Simulate response
            add_log_message("INFO", f"Simulating {selected_method} with parameters: {params}")
            
            if "player" in selected_method.lower():
                # Simulate player data
                result = {
                    "player_uuid": "demo-player-uuid-12345",
                    "display_name": params.get("display_names", ["DemoPlayer"])[0] if "display_names" in params else "DemoPlayer",
                    "platform": params.get("platform", "Steam"),
                    "stats": {
                        "total_matches_played": 42,
                        "total_wins": 25
                    }
                }
            elif "match" in selected_method.lower():
                # Simulate match data
                result = [
                    {
                        "match_id": "demo-match-1",
                        "player_uuid": params.get("player_uuid", "demo-player-uuid"),
                        "match_start": "2023-01-01T12:00:00Z",
                        "match_end": "2023-01-01T12:30:00Z",
                        "god_name": "Thor",
                        "mode": "Conquest",
                        "map": "Conquest Map",
                        "basic_stats": {
                            "Kills": 10,
                            "Deaths": 5,
                            "Assists": 15
                        }
                    }
                ]
            else:
                # Generic response
                result = {"status": "success", "message": "Operation completed (simulated)"}
                
        else:
            # Real API mode
            try:
                # Initialize SDK if not already done
                if not hasattr(st.session_state, "sdk_instance") or st.session_state.sdk_instance is None:
                    st.session_state.sdk_instance = S2Match()
                
                sdk = st.session_state.sdk_instance
                method = getattr(sdk, selected_method)
                
                # Log parameters for debugging
                add_log_message("INFO", f"Executing {selected_method} with parameters: {params}")
                
                # Remove empty parameters
                params = {k: v for k, v in params.items() if v != ""}
                
                # Execute method
                result = method(**params)
                add_log_message("INFO", f"Method {selected_method} executed successfully")
            except Exception as e:
                error_msg = log_exception(logger, e, f"Error executing {selected_method}")
                add_log_message("ERROR", f"Error executing {selected_method}: {str(e)}")
                st.error(f"Error executing {selected_method}: {str(e)}")
                result = {"error": str(e)}
        
        # Display result
        st.success(f"Method {selected_method} executed")
        
        # Display result based on type
        if isinstance(result, dict):
            display_json(result, title="Response (JSON)")
        elif isinstance(result, list):
            st.write(f"Response (List with {len(result)} items):")
            display_json(result, title="Response Items")
        elif isinstance(result, str):
            st.code(result, language="text")
        else:
            st.write("Response:", result)
            
        # Download button for results
        if result:
            try:
                result_json = json.dumps(result, indent=2)
                st.download_button(
                    label="Download Result",
                    data=result_json,
                    file_name=f"{selected_method}_result.json",
                    mime="application/json"
                )
            except:
                st.warning("Result cannot be downloaded as JSON")

# Footer with page navigation
st.markdown("---")
prev_page = st.button("Previous: Full Player Data")

if prev_page:
    st.switch_page("pages/4_Full_Player_Data.py") 