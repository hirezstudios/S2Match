import streamlit as st
import os
import sys
import logging
from pathlib import Path

# Add parent directory to sys.path to import s2match from root
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import S2Match
from s2match import S2Match

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Streamlit")

# Configure page
st.set_page_config(
    page_title="SMITE 2 Match Data Explorer",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if not already set
if "initialized" not in st.session_state:
    # Load environment variables for default values
    default_client_id = os.getenv("CLIENT_ID", "")
    default_client_secret = os.getenv("CLIENT_SECRET", "")
    default_base_url = os.getenv("RH_BASE_URL", "")
    
    # Initialize session state
    st.session_state.client_id = default_client_id
    st.session_state.client_secret = default_client_secret
    st.session_state.base_url = default_base_url
    st.session_state.cache_enabled = True
    st.session_state.rate_limit_delay = 0.0
    
    # Set default rate limit parameters
    st.session_state.max_retries = 3
    st.session_state.base_retry_delay = 1.0
    st.session_state.max_retry_delay = 60.0
    
    st.session_state.initialized = True

# Initialize SDK with configuration from session state
def initialize_sdk():
    try:
        # Get configuration from session state, with defaults if not set
        client_id = st.session_state.get("client_id")
        client_secret = st.session_state.get("client_secret")
        base_url = st.session_state.get("base_url")
        cache_enabled = st.session_state.get("cache_enabled", True)
        rate_limit_delay = st.session_state.get("rate_limit_delay", 0.0)
        
        # Get rate limit parameters with defaults
        max_retries = st.session_state.get("max_retries", 3)
        base_retry_delay = st.session_state.get("base_retry_delay", 1.0)
        max_retry_delay = st.session_state.get("max_retry_delay", 60.0)
        
        # Initialize the SDK with all parameters
        sdk = S2Match(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            cache_enabled=cache_enabled,
            rate_limit_delay=rate_limit_delay,
            max_retries=max_retries,
            base_retry_delay=base_retry_delay,
            max_retry_delay=max_retry_delay
        )
        
        return sdk
        
    except Exception as e:
        st.error(f"Error initializing SDK: {e}")
        return None

# Main app
def main():
    # Sidebar header
    st.sidebar.title("SMITE 2 Match Data Explorer")
    st.sidebar.markdown("---")
    
    # Main content
    st.title("SMITE 2 Match Data Explorer")
    st.markdown("""
    Welcome to the SMITE 2 Match Data Explorer!
    
    This application allows you to explore and analyze SMITE 2 match data using the S2Match SDK.
    
    Features:
    - Player Lookup
    - Match History
    - Player Statistics
    - Match Analysis
    - Settings Configuration
    
    Navigate using the sidebar menu to access different features.
    """)
    
    # Status indicator
    st.sidebar.markdown("---")
    sdk_status = st.sidebar.empty()
    
    # Check SDK configuration
    if not st.session_state.get("client_id") or not st.session_state.get("client_secret") or not st.session_state.get("base_url"):
        sdk_status.error("⚠️ SDK not fully configured. Please visit the Settings page.")
    else:
        # Try to initialize the SDK to verify credentials
        try:
            sdk = initialize_sdk()
            token = sdk.get_access_token()
            sdk_status.success("✅ SDK properly configured and authenticated")
        except Exception as e:
            sdk_status.error(f"⚠️ SDK configuration error: {e}")

# Run the main function
if __name__ == "__main__":
    main() 