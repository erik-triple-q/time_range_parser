#!/usr/bin/env bash
set -euo pipefail

echo "▶ Syncing dependency lock (if 'uv' is available)..."
if command -v uv >/dev/null 2>&1; then
  uv sync || true
else
  echo "⚠️  'uv' not found — skipping 'uv sync'. This is optional but recommended."
fi

PY_CMD="uv run python"
if ! command -v uv >/dev/null 2>&1; then
  # Fall back to system python; prefer using an activated venv.
  PY_CMD="python"
  echo "⚠️  Using plain 'python' because 'uv' is not available. Activate your venv if you have one."
fi

echo "▶ Ensuring pip is available in project's python environment..."
$PY_CMD -m ensurepip --upgrade || true

echo "▶ Installing editable package with dev extras (this installs runtime + test deps)..."
# Try using the project's python (via uv) first, fallback to system python.
if ! $PY_CMD -m pip install -e ".[dev]"; then
  echo "⚠️  First attempt failed — trying fallback 'python -m pip install -e \".[dev]\"'"
  python -m pip install -e ".[dev]"
fi

cat <<'EOF'

✅ Bootstrapped project environment.
You can now run tests with either:
  uv run pytest
or
  python -m pytest

EOF
