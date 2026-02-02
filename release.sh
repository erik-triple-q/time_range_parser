#!/bin/bash
set -e

# Extract version from pyproject.toml
VERSION="v$(grep -m1 '^version =' pyproject.toml | cut -d '"' -f 2)"
if [ -z "$VERSION" ] || [ "$VERSION" = "v" ]; then
    echo "❌ Error: Could not extract version from pyproject.toml"
    exit 1
fi

echo "🚀 Preparing release $VERSION..."

# Pre-check: Ensure git is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Error: Working directory is not clean. Please commit changes before releasing."
    exit 1
fi

# Pre-check: Ensure dependencies are in sync
echo "🔒 Verifying lockfile..."
uv sync --locked --all-extras

# 0. Linting & Type Checking
echo "🧹 Linting & Formatting..."
uv run ruff format src/
uv run ruff check src/ --fix

# Check if linting modified files
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Error: Linting/Formatting modified files. Please commit changes and run release again."
    exit 1
fi

echo "🔍 Type checking..."
uv run mypy src/

# 1. Run tests
echo "🧪 Running tests..."
uv run pytest --cov=date_textparser --cov-report=term-missing

# 2. Build Docker image
echo "🐳 Building Docker image..."
docker build -t mcp-time_range_parser:$VERSION .
docker tag mcp-time_range_parser:$VERSION mcp-time_range_parser:latest

# 3. Instructions
echo "✅ Build successful."
echo "To finish release, run:"
echo "  git tag -a $VERSION -m \"Release $VERSION\" && git push origin $VERSION"