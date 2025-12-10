# {PROJECT_NAME}

A RealmSync API project.

## Setup

### Option 1: Using Docker Compose (Recommended)

1. Review and update `.env` file if needed.

2. Start all services:
   ```bash
   docker-compose up -d
   ```

3. The API will be available at `http://localhost:8000`

### Option 2: Local Development

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Review and update `.env` file with your database settings.

3. Start the server:
   ```bash
   uvicorn {PACKAGE_NAME}.main:app --reload
   ```

