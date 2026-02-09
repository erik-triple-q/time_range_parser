#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Bootstrap Script for Time Range Parser MCP Server
# ============================================================================

echo "🚀 Starting project bootstrap..."
echo ""

# ============================================================================
# Section 1: Pre-flight Checks
# ============================================================================

echo "▶ Validating Python version..."

# Check if python3 is available
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python 3 not found. Please install Python 3.12 or higher."
  echo "   Install: https://www.python.org/downloads/"
  exit 1
fi

# Get current Python version
CURRENT_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
REQUIRED_VERSION="3.12"

# Compare versions (sort -V handles version comparison)
if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$CURRENT_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
  echo "❌ Python $REQUIRED_VERSION or higher required, found Python $CURRENT_VERSION"
  echo "   Install: https://www.python.org/downloads/"
  exit 1
fi

echo "✓ Python $CURRENT_VERSION detected (>= $REQUIRED_VERSION required)"

# ============================================================================
# Section 2: Environment Setup
# ============================================================================

echo ""
echo "▶ Setting up environment configuration..."

# Create .env.example if missing (already exists now, but check for safety)
if [ ! -f .env.example ]; then
  echo "  Creating .env.example template..."
  cat > .env.example <<'ENVEOF'
# Time Range Parser MCP Server Configuration
# Copy this file to .env and customize as needed

# General Settings
TZ=Europe/Amsterdam              # IANA timezone (e.g., America/New_York)
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
USE_WORLDTIME_API=false          # Enable WorldTimeAPI integration (true/false)
TRANSPORT_TYPE=stdio             # MCP transport: stdio, sse, or http

# Server Settings (SSE/HTTP mode only)
HOST=0.0.0.0                     # Server bind address
PORT=9000                        # Server port

# Docker Settings
DOCKER_PORT=9000                 # Docker host port mapping

# Cache Settings
CACHE_DIR=./cache                # WorldTimeAPI cache directory
ENVEOF
  echo "✓ Created .env.example"
else
  echo "✓ .env.example already exists"
fi

# Inform user about .env configuration if neither .env nor .env.prod exists
if [ ! -f .env ] && [ ! -f .env.prod ]; then
  echo ""
  echo "💡 Tip: Copy .env.example to .env to customize configuration:"
  echo "   cp .env.example .env"
fi

# Initialize cache directory
CACHE_DIR="${CACHE_DIR:-./cache}"
if [ ! -d "$CACHE_DIR" ]; then
  echo ""
  echo "▶ Creating cache directory: $CACHE_DIR"
  mkdir -p "$CACHE_DIR"
  echo "✓ Cache directory ready"
else
  echo "✓ Cache directory exists: $CACHE_DIR"
fi

# ============================================================================
# Section 3: Dependency Installation
# ============================================================================

echo ""
echo "▶ Installing dependencies..."

# Sync with uv if available
if command -v uv >/dev/null 2>&1; then
  echo "  Using uv to sync dependencies..."
  if ! uv sync; then
    echo "❌ Dependency sync failed. Possible causes:"
    echo "   - Lock file out of sync (try: uv lock)"
    echo "   - Network connectivity issues"
    echo "   - Incompatible Python version"
    exit 1
  fi
  echo "✓ Dependencies synced with uv"
else
  echo "⚠️  'uv' not found — skipping 'uv sync'. Install from: https://docs.astral.sh/uv/"
  echo "  Falling back to pip installation..."
fi

# Determine Python command to use
PY_CMD="uv run python"
if ! command -v uv >/dev/null 2>&1; then
  PY_CMD="python3"
  echo "  Using system python3 (uv not available)"
fi

# Ensure pip is available (|| true because it's optional on systems with pip pre-installed)
echo ""
echo "▶ Ensuring pip is available..."
$PY_CMD -m ensurepip --upgrade 2>/dev/null || true

# ============================================================================
# Section 4: Package Installation
# ============================================================================

echo ""
echo "▶ Installing package with dev dependencies..."

# Try using the project's python (via uv) first
if ! $PY_CMD -m pip install -e ".[dev]"; then
  echo "⚠️  First attempt failed — trying fallback 'python3 -m pip install -e \".[dev]\"'"
  if ! python3 -m pip install -e ".[dev]"; then
    echo "❌ Package installation failed. Check error messages above."
    exit 1
  fi
fi

echo "✓ Package installed successfully"

# ============================================================================
# Section 5: Post-Install Verification
# ============================================================================

echo ""
echo "▶ Verifying installation..."

# Test 1: Package imports
if $PY_CMD -c "import date_textparser; import pendulum; import mcp" 2>/dev/null; then
  echo "✓ Core packages imported successfully"
else
  echo "⚠️  Package import check failed - some dependencies may not be installed correctly"
  echo "   Try running: $PY_CMD -c 'import date_textparser'"
fi

# Test 2: Pytest available
if $PY_CMD -m pytest --version >/dev/null 2>&1; then
  echo "✓ Test framework ready"
else
  echo "⚠️  pytest not available"
fi

# ============================================================================
# Section 6: Success Message
# ============================================================================

cat <<'EOF'

✅ Bootstrap completed successfully!

📋 Next Steps:
  1. Configure environment (optional):
     cp .env.example .env && nano .env

  2. Run tests:
     uv run pytest

  3. Start MCP server:
     # For Claude Desktop (stdio):
     uv run python server_main.py

     # For web clients (SSE):
     uv run python server_main.py --sse

  4. Integration test:
     # Terminal 1: uv run python server_main.py --sse
     # Terminal 2: uv run python mcp_client_httpx.py

📚 Documentation:
  - README.md      - Getting started & features
  - TECHNICAL.md   - API reference & testing
  - DOCKER.md      - Container deployment
  - CLAUDE.md      - Developer guidelines

EOF
