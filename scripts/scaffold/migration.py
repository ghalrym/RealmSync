"""Migration: {MIGRATION_NAME}"""

from realm_sync_api.dependencies.postgres import get_postgres_client


async def up():
    """
    Apply migration.

    {DESCRIPTION}
    """
    postgres = get_postgres_client()

    # TODO: Add your migration SQL here
    # Example:
    # await postgres.execute("""
    #     CREATE TABLE IF NOT EXISTS example (
    #         id SERIAL PRIMARY KEY,
    #         name VARCHAR(255) NOT NULL
    #     );
    # """)


async def down():
    """
    Rollback migration.
    """
    postgres = get_postgres_client()

    # TODO: Add your rollback SQL here
    # Example:
    # await postgres.execute("DROP TABLE IF EXISTS example;")

