# Contributing to Time Range Parser MCP

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Development Setup

1. **Prerequisites**:
   - Python 3.12 or higher
   - uv package manager (recommended) or pip

2. **Clone and setup**:
   ```bash
   git clone <repo-url>
   cd time_range_parser
   chmod +x scripts/bootstrap.sh && ./scripts/bootstrap.sh
   ```

3. **Install dependencies**:
   ```bash
   uv sync                    # Install all dependencies
   ```

## Project Architecture

For a comprehensive understanding of the codebase architecture, parsing flow, and design decisions, see [CLAUDE.md](../CLAUDE.md). This document covers:

- Core parsing pipeline and waterfall strategy
- Specialized parser modules and their responsibilities
- Time resolution rules and deterministic parsing
- Important patterns (Dutch time notation, weekday ranges, etc.)
- Testing philosophy and file organization

**Recommended reading** before making significant changes to the parser logic.

## Development Workflow

### Running Tests

```bash
uv run pytest                              # Run all tests
uv run pytest tests/test_time_range_parser.py  # Specific test file
uv run pytest -k "test_function_name"      # Specific test
uv run pytest --cov=date_textparser        # With coverage
```

### Code Quality

Before submitting a PR, ensure your code passes all checks:

```bash
uv run ruff format src/        # Format code
uv run ruff check src/ --fix   # Lint and auto-fix
uv run mypy src/               # Type checking
```

### Running the Server Locally

```bash
# STDIO mode (for Claude Desktop)
uv run python server_main.py

# SSE mode (for HTTP clients)
uv run python server_main.py --sse
```

## Git Workflow

### Branches

- `main`: Stable production branch
- Feature branches: `feature/<description>` or `fix/<description>`

### Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "Clear description of changes"
   ```

3. Push to your fork:
   ```bash
   git push -u origin feature/your-feature-name
   ```

4. Open a Pull Request on GitHub

### Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Be descriptive but concise
- Reference issues when applicable (#123)

## Adding New Parsers

1. Create parser function in appropriate `src/date_textparser/parsers/*.py` file
2. Add to `specialized_parsers` list in `core.py:_parse_time_range_internal()`
3. Add comprehensive tests with various phrasings
4. Update `src/date_textparser/vocabulary.py` if adding new keywords

## Testing Philosophy

- Tests are organized by feature area, not by file structure
- Use the `fixed_now` fixture from `conftest.py` for reproducible tests
- Aim for comprehensive coverage of edge cases (year boundaries, timezones, etc.)

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add tests for new functionality
4. Keep PRs focused on a single concern
5. Respond to review feedback promptly

## Questions?

Open an issue for:
- Bug reports
- Feature requests
- General questions

Thank you for contributing! 🎉
