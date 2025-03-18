import streamlit as st
import json
import os
import pandas as pd
from pathlib import Path
import base64

def load_css():
    """
    Load custom CSS styles for the app.
    """
    # Define custom CSS
    st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #f0f2f6;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #4e8df5;
            color: white;
        }
        div[data-testid="stExpander"] div[role="button"] p {
            font-size: 1.1rem;
            font-weight: 600;
        }
        .json-container {
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 10px;
            max-height: 500px;
            overflow: auto;
            font-family: monospace;
        }
        .code-header {
            background-color: #e6e9ef;
            padding: 8px 15px;
            border-radius: 5px 5px 0 0;
            font-weight: bold;
            margin-bottom: 0;
        }
        .code-container {
            margin-top: 0;
            border-radius: 0 0 5px 5px;
        }
        .tooltip {
            position: relative;
            display: inline-block;
            border-bottom: 1px dotted black;
        }
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 250px;
            background-color: #555;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -125px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
    </style>
    """, unsafe_allow_html=True)

def display_code_example(title, code, language="python"):
    """
    Display a code example with a title header.
    
    Args:
        title: The title for the code example
        code: The code to display
        language: The programming language for syntax highlighting
    """
    st.markdown(f'<div class="code-header">{title}</div>', unsafe_allow_html=True)
    st.code(code, language=language)
    
    # Add copy button
    if st.button(f"Copy {title} Code", key=f"copy_{hash(code)}"):
        st.toast("Code copied to clipboard!")

def format_json(data, indent=2):
    """
    Format JSON data for display.
    
    Args:
        data: The JSON data to format
        indent: The indentation level for formatting
        
    Returns:
        str: Formatted JSON string
    """
    if isinstance(data, str):
        try:
            # Try to parse if data is a JSON string
            data = json.loads(data)
        except:
            # Return as is if not valid JSON
            return data
    
    try:
        return json.dumps(data, indent=indent, sort_keys=False)
    except:
        # Fall back to string representation if JSON serialization fails
        return str(data)

def display_json_content(data, download_key=None):
    """
    Display the JSON content without creating an expander.
    
    Args:
        data: The JSON data to display
        download_key: Optional key for the download button
    """
    formatted_json = format_json(data)
    st.markdown(f'<div class="json-container">{formatted_json}</div>', unsafe_allow_html=True)
    
    # Add download button if a key is provided
    if download_key:
        if st.button("Download JSON", key=download_key):
            b64 = base64.b64encode(formatted_json.encode()).decode()
            download_name = "data.json"
            href = f'<a href="data:application/json;base64,{b64}" download="{download_name}">Download JSON File</a>'
            st.markdown(href, unsafe_allow_html=True)

def display_json(data, title="JSON Response", expanded=True, use_expander=True):
    """
    Display JSON data in an expandable container or directly.
    
    Args:
        data: The JSON data to display
        title: The title for the expander or section
        expanded: Whether the expander should be initially expanded
        use_expander: Whether to use an expander or display directly
    """
    download_key = f"download_{hash(str(data))}"
    
    if use_expander:
        with st.expander(title, expanded=expanded):
            display_json_content(data, download_key)
    else:
        st.write(f"**{title}**")
        display_json_content(data, download_key)

def json_to_df(json_data, flatten=True):
    """
    Convert JSON data to a pandas DataFrame.
    
    Args:
        json_data: The JSON data to convert
        flatten: Whether to flatten nested structures
        
    Returns:
        pandas.DataFrame: The converted DataFrame
    """
    try:
        if flatten:
            return pd.json_normalize(json_data)
        else:
            return pd.DataFrame(json_data)
    except Exception as e:
        st.error(f"Error converting JSON to DataFrame: {str(e)}")
        return pd.DataFrame()

def load_demo_data():
    """
    Load demo data for use when SDK is not initialized.
    
    Returns:
        dict: Dictionary containing demo data
    """
    demo_data = {
        "players": [
            {
                "display_name": "Weak3n",
                "player_uuid": "e3438d31-c3ee-5377-b645-5a604b0e2b0e",
                "platform": "Steam",
                "matches_played": 423,
                "winrate": 0.52
            },
            {
                "display_name": "PBM",
                "player_uuid": "f8f7f6f5-e4e3-d2d1-c0b9-a8a7a6a5a4a3",
                "platform": "XboxLive",
                "matches_played": 387,
                "winrate": 0.61
            },
            {
                "display_name": "fineokay",
                "player_uuid": "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
                "platform": "PlayStation",
                "matches_played": 502,
                "winrate": 0.58
            }
        ],
        "matches": [
            {
                "match_id": "8420DAB6-6AD6-4E6B-840C-81A28DE9964A",
                "player_uuid": "e3438d31-c3ee-5377-b645-5a604b0e2b0e",
                "god_name": "Vulcan",
                "team_id": 1,
                "mode": "Conquest",
                "map": "L_CQ_F2P_P",
                "match_start": "2023-06-01T15:20:30Z",
                "match_end": "2023-06-01T16:05:45Z",
                "basic_stats": {
                    "Kills": 6,
                    "Deaths": 7,
                    "Assists": 5,
                    "TotalDamage": 32450,
                    "TotalAllyHealing": 1200
                }
            },
            {
                "match_id": "4166D08C-B96C-4A8F-AAEE-DE579037A690",
                "player_uuid": "e3438d31-c3ee-5377-b645-5a604b0e2b0e",
                "god_name": "Bari",
                "team_id": 2,
                "mode": "Conquest",
                "map": "L_CQ_F2P_P",
                "match_start": "2023-06-01T14:10:20Z",
                "match_end": "2023-06-01T14:45:15Z",
                "basic_stats": {
                    "Kills": 26,
                    "Deaths": 5,
                    "Assists": 18,
                    "TotalDamage": 45720,
                    "TotalAllyHealing": 8500
                }
            },
            {
                "match_id": "9CAF7063-79FC-46B3-862A-FDF8A3E51B18",
                "player_uuid": "e3438d31-c3ee-5377-b645-5a604b0e2b0e",
                "god_name": "Anhur",
                "team_id": 1,
                "mode": "Conquest",
                "map": "L_CQ_F2P_P",
                "match_start": "2023-06-01T13:05:10Z",
                "match_end": "2023-06-01T13:35:45Z",
                "basic_stats": {
                    "Kills": 7,
                    "Deaths": 1,
                    "Assists": 7,
                    "TotalDamage": 28650,
                    "TotalAllyHealing": 0
                }
            }
        ],
        "stats": {
            "total_matches_played": 423,
            "total_wins": 220,
            "total_losses": 203,
            "game_mode_stats": [
                {
                    "mode": "Conquest",
                    "matches_played": 325,
                    "wins": 175,
                    "losses": 150
                },
                {
                    "mode": "Arena",
                    "matches_played": 98,
                    "wins": 45,
                    "losses": 53
                }
            ]
        }
    }
    
    return demo_data

def create_kda_chart(matches_data, player_name="Player"):
    """
    Create a K/D/A chart for a player's matches.
    
    Args:
        matches_data: List of match data dictionaries
        player_name: Name of the player for chart title
        
    Returns:
        plotly.graph_objects.Figure: The K/D/A chart
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import pandas as pd
    
    # Extract match data
    match_data = []
    for i, match in enumerate(matches_data[::-1]):  # Reverse to show oldest first
        basic_stats = match.get("basic_stats", {})
        match_data.append({
            "match_num": i+1,
            "match_id": match.get("match_id", f"Match {i+1}"),
            "god": match.get("god_name", "Unknown"),
            "kills": basic_stats.get("Kills", 0),
            "deaths": basic_stats.get("Deaths", 0),
            "assists": basic_stats.get("Assists", 0),
            "kda": (basic_stats.get("Kills", 0) + basic_stats.get("Assists", 0)) / max(basic_stats.get("Deaths", 1), 1),
            "mode": match.get("mode", "Unknown"),
            "team_id": match.get("team_id", 0)
        })
    
    df = pd.DataFrame(match_data)
    
    if df.empty:
        return None
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add traces
    fig.add_trace(
        go.Bar(
            x=df["match_num"],
            y=df["kills"],
            name="Kills",
            marker_color="#5D9CEC"
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Bar(
            x=df["match_num"],
            y=df["deaths"],
            name="Deaths",
            marker_color="#ED5565"
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Bar(
            x=df["match_num"],
            y=df["assists"],
            name="Assists",
            marker_color="#48CFAD"
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=df["match_num"],
            y=df["kda"],
            name="KDA Ratio",
            mode="lines+markers",
            marker=dict(size=8, color="#FFCE54"),
            line=dict(width=2, color="#FFCE54")
        ),
        secondary_y=True
    )
    
    # Add god/character labels
    god_labels = [f"Match {i+1}: {god}" for i, god in enumerate(df["god"])]
    
    # Add figure title and axis labels
    fig.update_layout(
        title=f"{player_name}'s Recent Match Performance",
        xaxis_title="Match Number",
        yaxis_title="Count",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        barmode="group",
        hoverlabel=dict(
            bgcolor="white",
            font_size=12
        ),
        hovermode="x unified"
    )
    
    # Format hover tooltips
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>%{y}<extra></extra>"
    )
    
    # Configure secondary y-axis
    fig.update_yaxes(
        title_text="KDA Ratio", 
        secondary_y=True,
        showgrid=False
    )
    
    # Add god labels as annotations on hover
    for i, god in enumerate(df["god"]):
        fig.add_annotation(
            x=i+1,
            y=0,
            text=god,
            showarrow=False,
            yshift=-30,
            font=dict(size=10),
            visible=False,
            hovertext=f"God: {god}"
        )
    
    return fig

def safe_get(data, keys, default=None):
    """
    Safely get nested values from a dictionary.
    
    Args:
        data: The dictionary to retrieve data from
        keys: List of keys to traverse
        default: Default value if the key path doesn't exist
        
    Returns:
        The value at the key path or the default value
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current 