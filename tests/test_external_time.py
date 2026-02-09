import os
import sys
from unittest.mock import patch, MagicMock
import pytest
import httpx

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from lib.external_time import (
    get_local_timezone_from_ip,
    get_valid_timezones,
    get_current_time_from_api,
    clear_cache,
)


@pytest.fixture(autouse=True)
def clean_cache_fixture():
    """Ensure cache is clean before each test."""
    clear_cache()
    yield
    clear_cache()


@patch("lib.external_time._get_http_client")
def test_get_local_timezone_from_ip_success(mock_get_client):
    # Enable API explicitly for this test
    with patch.dict(os.environ, {"USE_WORLDTIME_API": "true"}):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get.return_value.json.return_value = {
            "timezone": "Europe/Amsterdam"
        }
        mock_client.get.return_value.raise_for_status = MagicMock()

        result = get_local_timezone_from_ip()
        assert result == "Europe/Amsterdam"


def test_get_valid_timezones_static():
    """Test fetching timezones returns static list."""
    result = get_valid_timezones()
    # Should return full static list
    assert len(result) > 100
    assert "Europe/Amsterdam" in result
    assert "Africa/Cairo" in result
    assert "Asia/Tokyo" in result
    assert "America/New_York" in result
    assert "UTC" in result


@patch("lib.external_time._get_http_client")
def test_get_current_time_from_api_success(mock_get_client):
    with patch.dict(os.environ, {"USE_WORLDTIME_API": "true"}):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get.return_value.json.return_value = {
            "datetime": "2026-01-01T12:00:00+01:00"
        }
        mock_client.get.return_value.raise_for_status = MagicMock()

        result = get_current_time_from_api("Europe/Amsterdam")
        assert result == "2026-01-01T12:00:00+01:00"


def test_api_disabled_behavior():
    """Test that functions return None/empty when API is disabled (default or explicit)."""
    with patch.dict(os.environ, {"USE_WORLDTIME_API": "false"}):
        assert get_local_timezone_from_ip() is None
        # Should fallback to static aliases
        valid_zones = get_valid_timezones()
        assert len(valid_zones) > 0
        assert "Europe/Amsterdam" in valid_zones
        assert get_current_time_from_api("UTC") is None


@patch("lib.external_time.logger")
@patch("lib.external_time._get_http_client")
def test_get_current_time_from_api_http_error(mock_get_client, mock_logger):
    """Test that HTTPStatusError is handled gracefully and logged."""
    with patch.dict(os.environ, {"USE_WORLDTIME_API": "true"}):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Create a mock request and response to simulate a 404
        mock_request = httpx.Request("GET", "http://fakeurl/api/timezone/Invalid/Zone")
        mock_response = httpx.Response(status_code=404, request=mock_request)

        # Configure the `raise_for_status` method on the returned response mock
        mock_client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Client error '404 Not Found' for url 'http://fakeurl/api/timezone/Invalid/Zone'",
            request=mock_request,
            response=mock_response,
        )

        result = get_current_time_from_api("Invalid/Zone")

        assert result is None
        mock_logger.warning.assert_called_once()
        call_args, _ = mock_logger.warning.call_args
        assert "HTTP error fetching time for Invalid/Zone: 404" in call_args[0]
