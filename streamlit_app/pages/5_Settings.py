import streamlit as st
import os
import sys
import logging
from pathlib import Path

# Add parent directory to sys.path to import s2match from root
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import S2Match
from s2match import S2Match

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Streamlit-Settings")

# Page title
st.title("SDK Settings")
st.markdown("Configure the S2Match SDK settings on this page.")

# API Credentials Section
st.subheader("API Credentials")

# Get current values from session state
default_client_id = st.session_state.get("client_id", os.getenv("CLIENT_ID", ""))
default_client_secret = st.session_state.get("client_secret", os.getenv("CLIENT_SECRET", ""))
default_base_url = st.session_state.get("base_url", os.getenv("RH_BASE_URL", ""))

# Display input fields
client_id = st.text_input("Client ID", value=default_client_id, type="password")
client_secret = st.text_input("Client Secret", value=default_client_secret, type="password")
base_url = st.text_input("Base URL", value=default_base_url)

# Cache Settings
st.subheader("Cache Settings")
cache_enabled = st.checkbox("Enable Caching", value=st.session_state.get("cache_enabled", True),
                           help="Enable caching to reduce repeated API calls")

# Basic Rate Limit Settings
st.subheader("Basic Rate Limit Settings")
rate_limit_delay = st.number_input("Rate Limit Delay (seconds)", 
                                   min_value=0.0, 
                                   max_value=10.0, 
                                   value=st.session_state.get("rate_limit_delay", 0.0),
                                   step=0.1,
                                   format="%.1f",
                                   help="Fixed delay between API calls (seconds)")

# Rate Limit Settings
st.subheader("Enhanced Rate Limit Settings")

# Use current values from session state as defaults, or use SDK defaults
default_max_retries = st.session_state.get("max_retries", 3)
default_base_retry_delay = st.session_state.get("base_retry_delay", 1.0)
default_max_retry_delay = st.session_state.get("max_retry_delay", 60.0)

col1, col2 = st.columns(2)

with col1:
    max_retries = st.number_input(
        "Max Retries",
        min_value=0,
        max_value=10,
        value=default_max_retries,
        help="Maximum number of retry attempts for rate-limited requests (default: 3)"
    )
    
    base_retry_delay = st.number_input(
        "Base Retry Delay (seconds)",
        min_value=0.1,
        max_value=10.0,
        value=default_base_retry_delay,
        step=0.1,
        format="%.1f",
        help="Initial delay in seconds before first retry (default: 1.0)"
    )

with col2:
    max_retry_delay = st.number_input(
        "Max Retry Delay (seconds)",
        min_value=1.0,
        max_value=300.0,
        value=default_max_retry_delay,
        step=1.0,
        format="%.1f",
        help="Maximum delay in seconds between retries (default: 60.0)"
    )
    
    # Add a checkbox to enable/disable exponential backoff visualization
    show_backoff_visualization = st.checkbox(
        "Show Backoff Visualization",
        value=False,
        help="Display a visualization of the exponential backoff strategy"
    )

# If the visualization is enabled, show it
if show_backoff_visualization:
    import numpy as np
    import matplotlib.pyplot as plt
    
    st.subheader("Exponential Backoff Visualization")
    
    # Calculate delay values (without jitter)
    retry_counts = range(11)  # 0 to 10
    delays = [min(base_retry_delay * (2 ** retry), max_retry_delay) for retry in retry_counts]
    
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Plot delay curve
    ax.plot(retry_counts, delays, 'o-', color='#FF4B4B', linewidth=2, markersize=8)
    
    # Add max retry delay line
    ax.axhline(y=max_retry_delay, color='#FF4B4B', linestyle='--', alpha=0.5, 
               label=f'Max Delay: {max_retry_delay}s')
    
    # Add vertical line for max retries
    if max_retries > 0:
        ax.axvline(x=max_retries, color='#808495', linestyle='--', alpha=0.7,
                   label=f'Max Retries: {max_retries}')
    
    # Format the plot
    ax.set_xlabel('Retry Attempt')
    ax.set_ylabel('Delay (seconds)')
    ax.set_title('Exponential Backoff Strategy')
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()
    
    # Set x-axis to integer values
    ax.set_xticks(retry_counts)
    
    # Display the plot
    st.pyplot(fig)
    
    st.info("""
    This visualization shows how the delay between retry attempts increases exponentially.
    The actual delay includes a random jitter of ±20% to prevent synchronized retries.
    
    Formula: `min(base_delay * (2^retry_count), max_delay) ± jitter`
    """)

# When saving settings, update the SDK with the new parameters
if st.button("Save Settings"):
    # Save all settings to session state
    st.session_state.client_id = client_id
    st.session_state.client_secret = client_secret
    st.session_state.base_url = base_url
    st.session_state.cache_enabled = cache_enabled
    st.session_state.rate_limit_delay = rate_limit_delay
    st.session_state.max_retries = max_retries
    st.session_state.base_retry_delay = base_retry_delay
    st.session_state.max_retry_delay = max_retry_delay
    
    # Show success message
    st.success("Settings saved successfully! The SDK will use these settings for future requests.")
    
    # Attempt to initialize SDK with new settings to verify they work
    try:
        sdk = S2Match(
            client_id=client_id if client_id else None,
            client_secret=client_secret if client_secret else None,
            base_url=base_url if base_url else None,
            cache_enabled=cache_enabled,
            rate_limit_delay=rate_limit_delay,
            max_retries=max_retries,
            base_retry_delay=base_retry_delay,
            max_retry_delay=max_retry_delay
        )
        # Test authentication
        token = sdk.get_access_token()
        st.success("✅ Authentication successful with the new settings!")
    except Exception as e:
        st.error(f"❌ Failed to initialize SDK with the new settings: {e}")
        logger.error(f"SDK initialization error: {e}") 