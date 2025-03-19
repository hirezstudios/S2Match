# S2Match SDK Streamlit Companion

An interactive web application to demonstrate the capabilities of the S2Match SDK for SMITE 2 match data.

> **Note**: This Streamlit companion app is currently a work in progress but already provides comprehensive functionality for exploring the S2Match SDK capabilities.

## Overview

This Streamlit application serves as a companion to the S2Match SDK, providing:

- Interactive examples of all SDK methods
- Visualizations of player and match data
- Code snippets for developers
- A playground for testing the SDK features

## Getting Started

### Installation

1. Clone the S2Match repository
2. Install the main SDK requirements:
   ```
   pip install -r requirements.txt
   ```
3. Install the Streamlit app requirements:
   ```
   pip install -r streamlit_app/requirements.txt
   ```

### Running the App

From the repository root directory, run:

```bash
streamlit run streamlit_app/Home.py
```

Or use the included shell script:

```bash
./run_streamlit_app.sh
```

The app will open in your default web browser at http://localhost:8501.

## Features

The Streamlit companion app includes the following pages:

1. **Home**: Overview of the SDK and configuration options
   - SDK initialization panel
   - Environment variable configuration
   - API authentication testing
   - SDK status monitoring

2. **Player Lookup**: Search for players by display name across platforms
   - Multi-platform search capability
   - Linked accounts discovery
   - Detailed player profile cards
   - Interactive network visualization for linked accounts

3. **Match History**: View detailed match data for a player
   - Match filtering and sorting
   - Performance visualizations (K/D/A, win rate, etc.)
   - God/role performance analysis
   - Item build display
   - Match timeline visualization

4. **Player Statistics**: Analyze player performance metrics
   - Win/loss distribution
   - Performance trends over time
   - God usage statistics
   - Combat performance metrics
   - Custom statistic calculations

5. **Full Player Data**: Comprehensive view of all player-related data
   - Combined profile, stats, ranks, and match history
   - Account relationship visualization
   - Cross-platform statistics comparison
   - Rank information with tier/division details
   - Performance charts and trends

6. **API Explorer**: Interactive interface for testing any SDK method
   - Method selection with parameter input
   - Documentation for each method
   - Response visualization
   - Performance metrics

Each page includes:
- Interactive forms for inputting parameters
- Visualizations of the returned data
- Raw JSON response viewers
- Copy-ready code examples
- Documentation on how to use the data

## Demo Mode

The app includes a demo mode that uses mock data when no SDK credentials are provided. This allows you to explore the interface and functionality without a live API connection.

To use demo mode, simply use the app without initializing the SDK in the Home page.

## Using Your Own Credentials

To use the app with your own RallyHere Environment API credentials:

1. Enter your credentials in the sidebar on the Home page
2. Click "Initialize SDK" to connect to the API
3. Navigate to any page to start using live data

## Current Status and Roadmap

### Implemented Features
- ✅ All major pages and navigation
- ✅ SDK integration and authentication
- ✅ Player search and profile display
- ✅ Match history visualization
- ✅ Player statistics analysis
- ✅ Full player data integration
- ✅ API explorer interface
- ✅ Code examples on all pages
- ✅ Demo mode with mock data
- ✅ Helper methods for common tasks (e.g., extract_player_uuids, filter_matches)

### Upcoming Features
- 📋 Enhanced data export options (CSV, Excel)
- 📋 More advanced visualizations
- 📋 Custom analysis tools
- 📋 Test coverage improvements
- 📋 Additional filtering options
- 📋 User feedback collection

## Development

### Project Structure

```
streamlit_app/
├── Home.py                # Main entry point
├── README.md              # This file
├── requirements.txt       # App-specific dependencies
├── pages/                 # Streamlit pages
│   ├── 1_Player_Lookup.py
│   ├── 2_Match_History.py
│   ├── 3_Player_Statistics.py
│   ├── 4_Full_Player_Data.py
│   └── 5_API_Explorer.py
├── utils/                 # Utility functions 
│   ├── __init__.py
│   ├── app_utils.py       # Helper functions for the app
│   ├── env_loader.py      # Environment variable management
│   └── logger.py          # Logging configuration
└── logs/                  # Application logs
```

### Adding New Features

To add a new page to the app:

1. Create a new file in the `pages/` directory with the naming format `N_Page_Name.py`
2. Import the required utilities from `utils.app_utils`
3. Follow the pattern of the existing pages for consistency

### Feedback and Improvements

This companion app is designed to identify potential improvements to the S2Match SDK. If you discover issues or have suggestions for additional features, please:

1. Open an issue in the repository
2. Include details about the improvement or issue
3. If possible, provide code examples or screenshots 