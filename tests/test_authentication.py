"""
Tests for the authentication functionality of the S2Match SDK.
"""

import time
import pytest
from unittest.mock import patch

import requests
from s2match import S2Match


def test_init_with_env_vars(mock_env_vars):
    """Test SDK initialization using environment variables."""
    sdk = S2Match()
    assert sdk.client_id == "test_client_id"
    assert sdk.client_secret == "test_client_secret"
    assert sdk.base_url == "https://api.test.rallyhere.com"
    assert sdk.cache_enabled is True
    assert sdk.rate_limit_delay == 0.0


def test_init_with_params():
    """Test SDK initialization using constructor parameters."""
    sdk = S2Match(
        client_id="param_client_id",
        client_secret="param_client_secret",
        base_url="https://param.api.com",
        cache_enabled=False,
        rate_limit_delay=1.5
    )
    assert sdk.client_id == "param_client_id"
    assert sdk.client_secret == "param_client_secret"
    assert sdk.base_url == "https://param.api.com"
    assert sdk.cache_enabled is False
    assert sdk.rate_limit_delay == 1.5
    assert sdk.cache is None


def test_init_missing_credentials():
    """Test SDK initialization with missing credentials."""
    with pytest.raises(ValueError) as excinfo:
        S2Match(client_id=None, client_secret=None, base_url=None)
    
    assert "Missing environment credentials" in str(excinfo.value)


def test_get_access_token(sdk, mock_requests_post, mock_access_token):
    """Test getting an access token."""
    token = sdk.get_access_token()
    
    # Verify the token is returned correctly
    assert token == "test_access_token"
    
    # Verify the request was made correctly
    mock_requests_post.assert_called_once()
    args, kwargs = mock_requests_post.call_args
    
    # Check the URL
    assert args[0] == "https://api.test.rallyhere.com/users/v2/oauth/token"
    
    # Check the headers
    assert "Authorization" in kwargs["headers"]
    assert kwargs["headers"]["Authorization"].startswith("Basic ")
    
    # Check the payload
    assert kwargs["json"] == {"grant_type": "client_credentials"}
    
    # Check that the token was stored in the SDK
    assert sdk._access_token == "test_access_token"
    assert sdk._token_expiry > 0


def test_access_token_caching(sdk, mock_requests_post):
    """Test that access tokens are cached and reused before expiry."""
    # Get a token initially
    token1 = sdk.get_access_token()
    assert mock_requests_post.call_count == 1
    
    # Get another token immediately - should use the cached one
    token2 = sdk.get_access_token()
    assert mock_requests_post.call_count == 1  # No additional call
    assert token1 == token2


def test_access_token_expiry(sdk, mock_requests_post):
    """Test that expired tokens are refreshed."""
    # Get a token initially
    token1 = sdk.get_access_token()
    assert mock_requests_post.call_count == 1
    
    # Manually expire the token
    sdk._token_expiry = time.time() - 10
    
    # Get another token - should request a new one
    token2 = sdk.get_access_token()
    assert mock_requests_post.call_count == 2  # Another call made
    assert token1 == token2  # In the test, the mock returns the same token


def test_access_token_error(sdk, mock_requests_post):
    """Test error handling when token request fails."""
    # Make the request raise an exception
    mock_requests_post.side_effect = requests.exceptions.RequestException("API Error")
    
    # Attempt to get a token
    with pytest.raises(requests.exceptions.RequestException) as excinfo:
        sdk.get_access_token()
    
    assert "API Error" in str(excinfo.value)


def test_rate_limiting():
    """Test that rate limiting delay is applied."""
    # Create SDK with a small delay
    sdk = S2Match(
        client_id="test_id",
        client_secret="test_secret",
        base_url="https://test.api.com",
        rate_limit_delay=0.1
    )
    
    # Patch time.sleep to verify it's called
    with patch('time.sleep') as mock_sleep:
        sdk._handle_rate_limiting()
        mock_sleep.assert_called_once_with(0.1)
        
    # Test with no delay (shouldn't call sleep)
    sdk.rate_limit_delay = 0
    with patch('time.sleep') as mock_sleep:
        sdk._handle_rate_limiting()
        mock_sleep.assert_not_called() 