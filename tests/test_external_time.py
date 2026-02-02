import pytest
from unittest.mock import patch, MagicMock
from lib.external_time import (
    get_local_timezone_from_ip,
    get_valid_timezones,
    get_current_time_from_api,
    clear_cache,
)


@pytest.fixture
def mock_httpx_client():
    """Mocks the httpx.Client context manager."""
    with patch("lib.external_time.httpx.Client") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        # Mock de context manager (__enter__ en __exit__)
        mock_instance.__enter__.return_value = mock_instance
        yield mock_instance


@pytest.fixture(autouse=True)
def reset_cache():
    """Clears the cache before and after each test to ensure isolation."""
    clear_cache()
    yield
    clear_cache()


def test_get_local_timezone_from_ip_success(mock_httpx_client):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {"timezone": "Europe/Amsterdam"}
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.get.return_value = mock_response

    # Run function
    result = get_local_timezone_from_ip()

    # Assertions
    assert result == "Europe/Amsterdam"
    mock_httpx_client.get.assert_called_once()
    assert "ip" in mock_httpx_client.get.call_args[0][0]


def test_get_local_timezone_from_ip_failure(mock_httpx_client):
    # Setup mock to raise exception
    mock_httpx_client.get.side_effect = Exception("Connection error")

    result = get_local_timezone_from_ip()

    assert result is None


def test_get_valid_timezones_success(mock_httpx_client):
    mock_response = MagicMock()
    mock_response.json.return_value = ["Africa/Abidjan", "Europe/Amsterdam"]
    mock_httpx_client.get.return_value = mock_response

    result = get_valid_timezones()

    assert len(result) == 2
    assert "Europe/Amsterdam" in result


def test_get_valid_timezones_empty_on_error(mock_httpx_client):
    mock_httpx_client.get.side_effect = Exception("Timeout")
    result = get_valid_timezones()
    assert result == []


def test_get_current_time_from_api_success(mock_httpx_client):
    mock_response = MagicMock()
    # WorldTimeAPI returns a 'datetime' field in ISO format
    mock_response.json.return_value = {"datetime": "2026-01-01T12:00:00+01:00"}
    mock_httpx_client.get.return_value = mock_response

    result = get_current_time_from_api("Europe/Amsterdam")

    assert result == "2026-01-01T12:00:00+01:00"
    # Check if timezone was part of the URL
    args, _ = mock_httpx_client.get.call_args
    assert "Europe/Amsterdam" in args[0]


def test_get_current_time_from_api_failure(mock_httpx_client):
    mock_httpx_client.get.side_effect = Exception("404 Not Found")
    result = get_current_time_from_api("Invalid/Zone")
    assert result is None
