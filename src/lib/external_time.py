import logging
import httpx
from typing import Any

logger = logging.getLogger(__name__)

WORLD_TIME_API_BASE = "http://worldtimeapi.org/api"


def get_local_timezone_from_ip() -> str | None:
    """
    Detects the server's timezone based on its public IP using WorldTimeAPI.
    Returns the IANA timezone string (e.g., "Europe/Amsterdam") or None if failed.
    """
    try:
        # Set a short timeout to avoid blocking startup too long
        with httpx.Client(timeout=2.0) as client:
            response = client.get(f"{WORLD_TIME_API_BASE}/ip")
            response.raise_for_status()
            data = response.json()
            return data.get("timezone")
    except Exception as e:
        logger.warning(f"Failed to detect local timezone via WorldTimeAPI: {e}")
        return None


def get_valid_timezones() -> list[str]:
    """
    Fetches a list of valid timezones from WorldTimeAPI.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{WORLD_TIME_API_BASE}/timezone")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.warning(f"Failed to fetch valid timezones: {e}")
        return []


def get_current_time_from_api(timezone: str) -> str | None:
    """
    Fetches the current time for a specific timezone from WorldTimeAPI.
    Returns ISO-8601 string or None if failed.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{WORLD_TIME_API_BASE}/timezone/{timezone}")
            response.raise_for_status()
            return response.json().get("datetime")
    except Exception as e:
        logger.warning(f"Failed to fetch current time for {timezone}: {e}")
        return None
