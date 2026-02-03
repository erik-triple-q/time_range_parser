import logging
import time
import os
from typing import Any
import httpx

logger = logging.getLogger(__name__)

WORLD_TIME_API_BASE = "https://worldtimeapi.org/api"

# Simple in-memory cache: {key: (timestamp, value)}
_CACHE: dict[str, tuple[float, Any]] = {}

# Cache Time-To-Live in seconds
TTL_IP_TIMEZONE = 3600  # 1 hour
TTL_VALID_TIMEZONES = 86400  # 24 hours


def _is_api_enabled() -> bool:
    """Check if the WorldTimeAPI integration is enabled via environment variable."""
    return os.environ.get("USE_WORLDTIME_API", "false").lower() in ("true", "1", "yes")


def _get_from_cache(key: str, ttl: float) -> Any | None:
    """Retrieve value from cache if not expired."""
    if key in _CACHE:
        timestamp, value = _CACHE[key]
        if time.time() - timestamp < ttl:
            logger.debug(f"Cache hit for {key}")
            return value
        else:
            del _CACHE[key]
    return None


def _save_to_cache(key: str, value: Any) -> None:
    """Save value to cache with current timestamp."""
    _CACHE[key] = (time.time(), value)


def clear_cache() -> None:
    """Clear the internal cache."""
    _CACHE.clear()


def get_local_timezone_from_ip() -> str | None:
    """
    Detects the server's timezone based on its public IP using WorldTimeAPI.
    Returns the IANA timezone string (e.g., "Europe/Amsterdam") or None if failed.
    Results are cached for 1 hour.
    """
    if not _is_api_enabled():
        logger.debug("WorldTimeAPI is disabled by USE_WORLDTIME_API flag.")
        return None

    cache_key = "local_timezone_ip"
    cached = _get_from_cache(cache_key, TTL_IP_TIMEZONE)
    if cached:
        return str(cached)

    try:
        # Set a short timeout to avoid blocking startup too long
        with httpx.Client(timeout=2.0) as client:
            response = client.get(f"{WORLD_TIME_API_BASE}/ip")
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                tz = data.get("timezone")
                if isinstance(tz, str):
                    _save_to_cache(cache_key, tz)
                    return tz
            return None
    except Exception as e:
        logger.warning(f"Failed to detect local timezone via WorldTimeAPI: {e}")
        return None


def get_valid_timezones() -> list[str]:
    """
    Fetches a list of valid timezones from WorldTimeAPI.
    Results are cached for 24 hours.
    """
    if not _is_api_enabled():
        logger.debug("WorldTimeAPI is disabled by USE_WORLDTIME_API flag.")
        return []

    cache_key = "valid_timezones"
    cached = _get_from_cache(cache_key, TTL_VALID_TIMEZONES)
    if cached:
        return list(cached)

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{WORLD_TIME_API_BASE}/timezone")
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                result = [str(x) for x in data]
                _save_to_cache(cache_key, result)
                return result
            return []
    except Exception as e:
        logger.warning(f"Failed to fetch valid timezones: {e}")
        return []


def get_current_time_from_api(timezone: str) -> str | None:
    """
    Fetches the current time for a specific timezone from WorldTimeAPI.
    Returns ISO-8601 string or None if failed.
    """
    if not _is_api_enabled():
        logger.debug("WorldTimeAPI is disabled by USE_WORLDTIME_API flag.")
        return None

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{WORLD_TIME_API_BASE}/timezone/{timezone}")
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                dt = data.get("datetime")
                if isinstance(dt, str):
                    return dt
            return None
    except Exception as e:
        logger.warning(f"Failed to fetch current time for {timezone}: {e}")
        return None
