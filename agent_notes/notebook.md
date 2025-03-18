# SMITE 2 Match Data SDK - Notebook

## Project Overview
This project is a Python SDK for interacting with the RallyHere Environment API to retrieve and transform SMITE 2 match data in a standardized format. The SDK is designed for external partners to easily access player statistics, match history, and related information.

## Key Observations
- The SDK successfully authenticates and retrieves data from the API
- Match data is properly transformed into a SMITE 2-friendly format
- The example script runs successfully and demonstrates key functionality
- The `.env` file contains the necessary credentials and configuration options

## API Credentials
The SDK uses the following environment variables for authentication:
- CLIENT_ID
- CLIENT_SECRET
- RH_BASE_URL

These are already configured in the `.env` file with valid credentials.

## Core Functionality
The SDK provides methods for:
- Authentication with the RallyHere Environment API
- Retrieving player information by platform and display name
- Fetching match history for specific players
- Getting player statistics
- Transforming raw data into a more accessible format

## RallyHere API Endpoints
The SDK interacts with the following RallyHere Environment API endpoints:

### Authentication
- `/users/v2/oauth/token` - Obtain access token for API requests

### Player Lookup
- `/users/v1/player` - Look up players by display name and platform
- `/users/v1/player/{player_id}/linked_portals` - Get linked portal accounts for a player
- `/users/v1/platform-user` - Find player by platform identity (e.g., Steam ID)

### Match Data
- `/match/v1/player/{player_uuid}/match` - Get match history for a specific player
- `/match/v1/match` - Get matches by instance ID

### Player Statistics
- `/match/v1/player/{player_uuid}/stats` - Get player statistics

### Ranking
- `/rank/v2/player/{player_uuid}/rank` - Get player's rank list
- `/rank/v3/rank/{rank_id}` - Get rank configuration
- `/rank/v2/player/{player_uuid}/rank/{rank_id}` - Get detailed rank information

## Testing Notes
Example execution confirmed the SDK can:
- Successfully authenticate with the API
- Retrieve player data by display name
- Fetch match history for a player
- Get comprehensive player data including linked accounts

## Future Reference
- The SDK includes caching functionality to improve performance
- Rate limiting can be configured through environment variables
- Item data is enriched using a local items.json file 