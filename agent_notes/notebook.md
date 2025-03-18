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