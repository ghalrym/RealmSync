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

Or install from source:

```bash
git clone https://github.com/ghalrym/RealmSync.git
cd RealmSync
pip install -e .
```

## Quick Start

```python
from realm_sync_api import RealmSyncApi
from realm_sync_api.models import Player
from realm_sync_api.hooks import RealmSyncHook
from realm_sync_api.setup.redis import RealmSyncRedis

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

## Documentation

API documentation is automatically available at `/docs` when running the application.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

