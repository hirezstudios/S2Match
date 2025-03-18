"""
Pytest configuration file with shared fixtures.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the s2match module
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from s2match import S2Match


@pytest.fixture
def mock_env_vars():
    """
    Mock environment variables used by the SDK.
    """
    with patch.dict(os.environ, {
        "CLIENT_ID": "test_client_id",
        "CLIENT_SECRET": "test_client_secret",
        "RH_BASE_URL": "https://api.test.rallyhere.com"
    }):
        yield


@pytest.fixture
def mock_access_token():
    """
    Mock access token response.
    """
    return {
        "access_token": "test_access_token",
        "token_type": "Bearer",
        "expires_in": 3600
    }


@pytest.fixture
def mock_requests_post(mock_access_token):
    """
    Mock the requests.post method.
    """
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_access_token
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_requests_get():
    """
    Mock the requests.get method.
    """
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def sdk(mock_env_vars):
    """
    Create an instance of the S2Match SDK with mocked environment variables.
    """
    return S2Match()


@pytest.fixture
def sample_player_data():
    """
    Sample player data for testing.
    """
    return load_test_data('player_data.json')


@pytest.fixture
def sample_match_data():
    """
    Sample match data for testing.
    """
    return load_test_data('match_data.json')


@pytest.fixture
def sample_stats_data():
    """
    Sample stats data for testing.
    """
    return load_test_data('stats_data.json')


def load_test_data(filename):
    """
    Load test data from mock_responses directory.
    """
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'mock_responses', filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return default empty structure if file not found or invalid
        if 'player' in filename:
            return {"display_names": []}
        elif 'match' in filename:
            return []
        else:
            return {} 