import os
import sys
from unittest.mock import patch
import pytest

# Ensure root is in path to import server_main
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from server_main import get_world_time


@patch("server_main.get_time_info_from_api")
def test_get_world_time_success(mock_get_info):
    with patch.dict(os.environ, {"USE_WORLDTIME_API": "true"}):
        mock_get_info.return_value = {
            "datetime": "2026-01-01T12:00:00+01:00",
            "utc_offset": "+01:00",
            "dst": False,
            "week_number": 1,
            "day_of_year": 1,
            "abbreviation": "CET",
        }

        result = get_world_time(city="Cairo")
        assert result["city"] == "Cairo"
        assert result["current_time"] == "2026-01-01T12:00:00+01:00"
        assert result["source"] == "WorldTimeAPI"


@patch("server_main.get_time_info_from_api")
def test_get_world_time_api_failure(mock_get_info):
    with patch.dict(os.environ, {"USE_WORLDTIME_API": "true"}):
        mock_get_info.return_value = None

        result = get_world_time(city="Unknown")
        assert "error" in result
        assert "Could not fetch time" in result["error"]


@patch("server_main.get_time_info_from_api")
def test_get_world_time_exception(mock_get_info):
    with patch.dict(os.environ, {"USE_WORLDTIME_API": "true"}):
        mock_get_info.side_effect = Exception("Something went wrong")

        result = get_world_time(city="ErrorCity")
        assert "error" in result
        assert "Something went wrong" in result["error"]


def test_get_world_time_disabled():
    with patch.dict(os.environ, {"USE_WORLDTIME_API": "false"}):
        result = get_world_time(city="Amsterdam")
        assert "error" in result
        assert "WorldTimeAPI is disabled" in result["error"]
