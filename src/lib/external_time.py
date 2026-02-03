import logging
import time
import json
import os
from typing import Any
import httpx

try:
    from date_textparser.vocabulary import TIMEZONE_ALIASES, TIMEZONES
except ImportError:
    TIMEZONE_ALIASES = {}
    TIMEZONES = []

logger = logging.getLogger(__name__)

WORLD_TIME_API_BASE = "https://worldtimeapi.org/api"

# --- File-based Cache Configuration ---
CACHE_DIR = os.environ.get("CACHE_DIR", "/cache")
CACHE_FILE = os.path.join(CACHE_DIR, "time_range_parser_cache.json")
_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_LOADED = False

# Cache Time-To-Live in seconds
TTL_IP_TIMEZONE = 3600  # 1 hour
TTL_TIME_INFO = 300  # 5 minutes


def _is_api_enabled() -> bool:
    """Check if the WorldTimeAPI integration is enabled via environment variable."""
    return os.environ.get("USE_WORLDTIME_API", "false").lower() in ("true", "1", "yes")


def _load_cache() -> None:
    """Load cache from disk if not already loaded."""
    global _CACHE_LOADED, _CACHE
    if _CACHE_LOADED:
        return

    os.makedirs(CACHE_DIR, exist_ok=True)
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                _CACHE = json.load(f)
            logger.info(f"Loaded cache from {CACHE_FILE}")
        except (IOError, json.JSONDecodeError) as e:
            logger.warning(
                f"Could not load cache file {CACHE_FILE}, starting fresh. Error: {e}"
            )
            _CACHE = {}
    _CACHE_LOADED = True


def _save_cache() -> None:
    """Save the entire cache to disk."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(_CACHE, f)
    except IOError as e:
        logger.warning(f"Could not write to cache file {CACHE_FILE}. Error: {e}")


def _get_from_cache(key: str, ttl: float) -> Any | None:
    """Retrieve value from cache if not expired."""
    _load_cache()
    if key in _CACHE:
        timestamp, value = _CACHE[key]
        if time.time() - timestamp < ttl:
            logger.debug(f"Cache hit for {key}")
            print(value)
            return value
        else:
            # Expired, remove from dict and save the change
            del _CACHE[key]
            _save_cache()
    return None


def _save_to_cache(key: str, value: Any) -> None:
    """Save value to cache with current timestamp and write to disk."""
    _load_cache()
    _CACHE[key] = (time.time(), value)
    _save_cache()


def clear_cache() -> None:
    """Clear the internal cache and delete the cache file."""
    global _CACHE, _CACHE_LOADED
    _CACHE = {}
    _CACHE_LOADED = True  # We've "loaded" an empty cache
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
            logger.info(f"Removed cache file {CACHE_FILE}")
        except IOError as e:
            logger.warning(f"Could not remove cache file {CACHE_FILE}. Error: {e}")


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
        logger.info(f"Retrieved local timezone '{cached}' from cache.")
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
    Returns a list of valid timezones.
    Uses local vocabulary definitions.
    """
    logger.debug("Using local timezone definitions.")
    return list(set(TIMEZONES) | set(TIMEZONE_ALIASES.values()))


def _fetch_timezone_data(timezone: str) -> dict[str, Any] | None:
    """Helper to fetch raw timezone data from API with error handling."""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{WORLD_TIME_API_BASE}/timezone/{timezone}")
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return data
            logger.warning(f"Unexpected response format for {timezone}: {type(data)}")
    except httpx.HTTPStatusError as e:
        logger.warning(
            f"HTTP error fetching time for {timezone}: {e.response.status_code} - {e}"
        )
    except httpx.RequestError as e:
        logger.warning(f"Network error fetching time for {timezone}: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error fetching time for {timezone}: {e}")
    return None


def get_current_time_from_api(timezone: str) -> str | None:
    """
    Fetches the current time for a specific timezone from WorldTimeAPI.
    Returns ISO-8601 string or None if failed.
    """
    if not _is_api_enabled():
        logger.debug("WorldTimeAPI is disabled by USE_WORLDTIME_API flag.")
        return None

    data = _fetch_timezone_data(timezone)
    if data:
        dt = data.get("datetime")
        if isinstance(dt, str):
            return dt
    return None


def get_time_info_from_api(timezone: str) -> dict[str, Any] | None:
    """
    Fetches detailed time info for a specific timezone from WorldTimeAPI.
    Returns dict with datetime, dst, utc_offset, etc. or None if failed.
    """
    if not _is_api_enabled():
        logger.debug("WorldTimeAPI is disabled by USE_WORLDTIME_API flag.")
        return None

    cache_key = f"time_info_{timezone}"
    cached = _get_from_cache(cache_key, TTL_TIME_INFO)
    if cached:
        logger.info(f"Retrieved time info for '{timezone}' from cache.")
        return dict(cached)

    data = _fetch_timezone_data(timezone)
    if data:
        _save_to_cache(cache_key, data)
        return data
    return None
