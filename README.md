# RealmSync API

A FastAPI-based API framework for managing game data with Redis and PostgreSQL support.

## Features

- 🚀 FastAPI-based REST API framework
- 🔄 Redis integration for caching and data storage
- 🗄️ PostgreSQL support for persistent data
- 🎨 Built-in web management interface
- 📝 Automatic API documentation with Swagger UI (dark mode)
- 🔌 Hook system for event-driven architecture
- 📦 Easy to install and use

## Installation

Install from PyPI (when published):

```bash
pip install realm-sync-api
```

## Quick Start

```python
from realm_sync_api import RealmSyncApi
from realm_sync_api.models import Player
from realm_sync_api.hooks import RealmSyncHook
from realm_sync_api.dependencies.redis import RealmSyncRedis

# Create the API instance
app = RealmSyncApi(web_manager_perfix="/admin")

# Set up Redis client
app.set_redis_client(RealmSyncRedis(host="localhost", port=6379, db=0))

# Register hooks
@app.hook(RealmSyncHook.PLAYER_CREATED)
def player_created(player: Player):
    print(f"Player created: {player.name}")

# Run with uvicorn
# uvicorn main:app --reload
```

## Requirements

- Python 3.11+
- FastAPI
- Redis (optional, for caching)
- PostgreSQL (optional, for persistent storage)

## Testing

### Installation

To run tests, first install the development dependencies:

```bash
pip install -e ".[dev]"
```

### Running Tests

After installation, you can run tests using the `runtests` command:

```bash
runtests
```

This will run all tests with coverage reporting and enforce a 95% coverage requirement.

### Additional Test Options

You can also pass any pytest arguments to `runtests`:

```bash
runtests -v                    # Verbose output
runtests tests/test_specific.py # Run specific test file
runtests -k "test_name"        # Run tests matching a pattern
runtests --tb=short            # Shorter traceback format
```

Alternatively, you can run tests directly with pytest:

```bash
pytest tests/
```

### Coverage

The project maintains a 95% code coverage requirement. Coverage reports are generated in both terminal and XML formats:

- Terminal output: Shows coverage summary and missing lines
- XML report: Saved to `coverage.xml` for CI/CD integration

To view an HTML coverage report:

```bash
pytest tests/ --cov=realm_sync_api --cov-report=html
# Then open htmlcov/index.html in your browser
```

## Linting

The project uses several linting tools to maintain code quality:

- **Ruff**: Fast Python linter and formatter with multiple rule sets (pycodestyle, pyflakes, isort, etc.)
- **MyPy**: Static type checker
- **Custom Import Checker**: Checks for imports inside functions

### Running Linters

Run all linting checks:

```bash
rs-lint
```

Or run individual tools:

```bash
ruff check .          # Linting
ruff format --check . # Formatting check
mypy realm_sync_api   # Type checking
```

### Custom Import Checker

The project includes a custom linter that detects imports inside functions instead of at the module level. This helps maintain code quality by ensuring imports are at the top of files.

After installing the package (with `pip install -e ".[dev]"`), you can use the `check-imports` command:

```bash
# Check all files
check-imports .

# Check specific files or directories
check-imports tests/ realm_sync_api/

# Use ruff-compatible output format
check-imports . --format ruff

# Exclude additional patterns
check-imports . --exclude htmlcov --exclude dist
```

You can also run it directly as a Python module:

```bash
python -m realm_sync_api.check_imports .
```

The checker will report any imports found inside function definitions and suggest moving them to the module level. You can ignore specific imports by adding `# noqa: I001` or `# noqa` comments on the same line.

## Documentation

API documentation is automatically available at `/docs` when running the application.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

