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

## Streamlit Companion App Development

### Implementation Process
We've developed a Streamlit companion app to provide an interactive interface for exploring the S2Match SDK. The development process involved:

1. **Planning the Application Structure**
   - Defined key pages based on SDK functionality
   - Created a consistent navigation system
   - Designed a modular component structure

2. **Building Core Functionality**
   - Implemented SDK initialization and authentication
   - Created data retrieval and visualization components
   - Developed interactive forms for parameter input

3. **Creating Data Visualizations**
   - Implemented charts and graphs for match performance
   - Developed network visualizations for linked accounts
   - Created interactive tables for data exploration

4. **Adding Demo Mode**
   - Implemented mock data generation for all pages
   - Created realistic sample responses
   - Ensured seamless switching between demo and live modes

5. **Enhancing User Experience**
   - Added code examples on all pages
   - Implemented detailed tooltips and documentation
   - Provided raw JSON viewers for developers

### Key Learnings from Streamlit Implementation

1. **Data Structure Complexity**
   - The nested structure of the SDK responses required careful handling in Streamlit
   - Data transformation was often needed to make responses more suitable for visualization

2. **Enhanced Error Handling Needs**
   - Building the UI highlighted the importance of detailed error messages
   - We added context-specific error handling throughout the app

3. **Performance Considerations**
   - Session state management is critical for performance in Streamlit
   - Caching helps reduce unnecessary API calls

4. **API Response Variations**
   - Some API endpoints return inconsistent data structures
   - The app needed to handle missing or unexpected data gracefully

5. **Visualization Requirements**
   - Different data types required specific visualization approaches
   - Interactive visualizations provided the best user experience

### Streamlit-Specific Techniques Used

1. **Session State Management**
   - Used st.session_state for persistent storage across page navigation
   - Cached API responses to improve performance

2. **Dynamic UI Components**
   - Implemented conditional rendering based on data availability
   - Created expandable sections for detailed information

3. **Data Visualization**
   - Used Plotly for interactive charts and graphs
   - Implemented NetworkX with Plotly for relationship visualization
   - Created custom styled components with HTML/CSS via st.markdown

4. **Form Handling**
   - Implemented validation for user inputs
   - Created dynamic parameter forms based on method signatures

5. **Error Handling and Logging**
   - Added comprehensive logging throughout the app
   - Implemented user-friendly error messages with suggestions

## Streamlit Companion App Observations and SDK Improvement Ideas

While developing the Streamlit companion app, we've identified several potential improvements for the SDK:

### Data Structure Improvements
1. **Simplify Response Nesting**: The player lookup response structure (`display_names` → list of dicts → player arrays) is overly complex to navigate. Consider providing a helper method to flatten this into a simpler list of player objects.

2. **Consistent Return Structures**: Methods like `fetch_player_with_displayname` and `fetch_matches_by_player_uuid` return differently structured data. More consistency would improve developer experience.

3. **Type Hints Expansion**: While the SDK has basic type hints, expand them to cover nested structures and provide more detailed documentation of response formats.

### Additional Helper Methods
1. **Extract Player UUID**: Add a helper method to easily extract player UUIDs from the complex player lookup response structure.

2. **Match Filtering**: Add methods to filter match data by date range, game mode, god/character, etc. to avoid client-side filtering.

3. **Data Aggregation**: Provide methods for common aggregations like K/D/A averages, win rates by god/role, etc.

4. **Cross-Method Integration**: Add methods that combine data from multiple endpoints into useful aggregates (e.g., match history + player stats).

### User Experience Enhancements
1. **Error Handling**: Enhance error messages to be more specific about what went wrong and provide suggestions for resolution.

2. **Rate Limit Handling**: Add exponential backoff for rate limit errors instead of just configurable delays.

3. **Data Validation**: Add validation for input parameters to catch common errors before making API calls.

4. **Progress Callbacks**: For methods that make multiple API calls, provide a way to track progress.

### Performance Optimizations
1. **Batch Requests**: Allow batching of requests for multiple players or matches to reduce API call overhead.

2. **Selective Field Retrieval**: Add options to only retrieve specific fields to reduce data transfer.

3. **Async Support**: Consider adding async versions of methods for better performance in concurrent contexts.

### Documentation Improvements
1. **Concrete Examples**: Add more concrete examples for each method showing common use cases.

2. **Visual Diagrams**: Include diagrams explaining the relationships between different data structures.

3. **Usage Patterns**: Document common patterns for working with the data, especially for complex nested structures.

## Future Reference
- The SDK includes caching functionality to improve performance
- Rate limiting can be configured through environment variables
- Item data is enriched using a local items.json file
- The Streamlit companion app provides a visual interface for exploring all SDK features 