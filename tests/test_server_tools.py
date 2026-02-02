import sys
import os
from unittest.mock import patch
import pytest

# Add project root to sys.path to allow importing server_main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server_main import get_world_time


def test_get_world_time_success():
    """Test successful retrieval of world time."""
    with (
        patch("server_main.normalize_timezone") as mock_normalize,
        patch("server_main.get_current_time_from_api") as mock_get_time,
    ):

        # Setup mocks
        city = "New York"
        mock_normalize.return_value = "America/New_York"
        mock_get_time.return_value = "2026-02-02T15:30:00-05:00"

        # Execute
        result = get_world_time(city)

        # Assertions
        assert result["city"] == city
        assert result["timezone"] == "America/New_York"
        assert result["current_time"] == "2026-02-02T15:30:00-05:00"
        assert result["source"] == "WorldTimeAPI"

        mock_normalize.assert_called_once_with(city)
        mock_get_time.assert_called_once_with("America/New_York")


def test_get_world_time_api_failure():
    """Test handling when API returns None (e.g. connection error or invalid zone)."""
    with (
        patch("server_main.normalize_timezone") as mock_normalize,
        patch("server_main.get_current_time_from_api") as mock_get_time,
    ):

        # Setup mocks
        city = "Atlantis"
        mock_normalize.return_value = "Ocean/Atlantis"
        mock_get_time.return_value = None

        # Execute
        result = get_world_time(city)

        # Assertions
        assert "error" in result
        assert "Could not fetch time" in result["error"]
        assert "Ocean/Atlantis" in result["error"]


def test_get_world_time_exception():
    """Test handling of unexpected exceptions."""
    with patch("server_main.normalize_timezone") as mock_normalize:
        # Setup mocks to raise exception
        mock_normalize.side_effect = Exception("Something went wrong")

        # Execute
        result = get_world_time("Error City")

        # Assertions
        assert "error" in result
        assert "Something went wrong" in result["error"]
