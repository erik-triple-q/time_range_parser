"""Pytest configuration for calendar-textparser tests."""

import logging
import pytest
import sys
from pathlib import Path

# Voeg de project root toe aan het Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Early environment check: ensure required third-party dependencies are installed
import importlib

_required_deps = ["dateparser", "pendulum"]
_missing = []
for _pkg in _required_deps:
    try:
        importlib.import_module(_pkg)
    except Exception:
        _missing.append(_pkg)

if _missing:
    pytest.exit(
        "Missing required dependencies: {}. Install them with 'uv sync' or 'pip install -e .[dev]' and re-run tests.".format(
            ", ".join(_missing)
        ),
        returncode=2,
    )


def pytest_configure(config):
    """Configure pytest."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--show-logs",
        action="store_true",
        default=False,
        help="Show debug logs during test execution",
    )


@pytest.fixture(autouse=True)
def configure_logging(request):
    """Configure logging level based on command line option."""
    target_logger = "date_textparser.dateparser"
    if request.config.getoption("--show-logs"):
        logging.getLogger(target_logger).setLevel(logging.DEBUG)
    else:
        logging.getLogger(target_logger).setLevel(logging.WARNING)
