class RealmSyncPostgres: ...


POSTGRES_CLIENT: RealmSyncPostgres | None = None


def set_postgres_client(postgres_client: RealmSyncPostgres) -> None:
    global POSTGRES_CLIENT
    POSTGRES_CLIENT = postgres_client


def get_postgres_client() -> RealmSyncPostgres:
    global POSTGRES_CLIENT
    if POSTGRES_CLIENT is None:
        raise ValueError("Postgres client not found")
    return POSTGRES_CLIENT
