import inspect
import uuid
from collections.abc import Sequence
from typing import Any, TypeVar, get_args, get_origin

import asyncpg

from realm_sync_api.models._base import RealmSyncModel

T = TypeVar("T", bound=RealmSyncModel)


class _InternalPostgresClient:
    """Internal PostgreSQL client implementation using asyncpg."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        **kwargs: Any,
    ) -> None:
        """Initialize PostgreSQL client."""
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.kwargs = kwargs
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Create connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                **self.kwargs,
            )

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def fetch_one(self, query: str, *args: Any) -> dict[str, Any] | None:
        """Fetch a single row from the database."""
        if self._pool is None:
            await self.connect()

        assert self._pool is not None
        row = await self._pool.fetchrow(query, *args)
        if row is None:
            return None
        return dict(row)

    async def fetch_all(self, query: str, *args: Any) -> list[dict[str, Any]]:
        """Fetch all rows from the database."""
        if self._pool is None:
            await self.connect()

        assert self._pool is not None
        rows = await self._pool.fetch(query, *args)
        return [dict(row) for row in rows]

    async def execute(self, query: str, *args: Any) -> None:
        """Execute a query without returning results."""
        if self._pool is None:
            await self.connect()

        assert self._pool is not None
        await self._pool.execute(query, *args)


class RealmSyncDatabase:
    """PostgreSQL database class for managing connections and model operations."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        **kwargs: Any,
    ) -> None:
        """
        Initialize RealmSyncDatabase with connection parameters.

        Args:
            host: Database host
            port: Database port
            user: Database user
            password: Database password
            database: Database name
            **kwargs: Additional arguments passed to asyncpg.create_pool
        """
        self.postgres = _InternalPostgresClient(host, port, user, password, database, **kwargs)
        self._registered_models: dict[type[RealmSyncModel], str] = {}
        self._model_metadata: dict[type[RealmSyncModel], dict[str, Any]] = {}

    async def _ensure_connection(self) -> None:
        """Ensure PostgreSQL connection is open."""
        await self.postgres.connect()

    async def close(self) -> None:
        """Close the database connection pool."""
        await self.postgres.close()

    def _get_table_name(self, model_class: type[RealmSyncModel]) -> str:
        """Get table name for a model class (pluralized)."""
        return f"{model_class.__name__.lower()}s"

    def _get_pg_type(self, field_type: type[Any], field_info: Any) -> str:
        """
        Map Python/Pydantic types to PostgreSQL types.

        Args:
            field_type: The Python type
            field_info: Pydantic FieldInfo object

        Returns:
            PostgreSQL type string
        """
        origin = get_origin(field_type)
        args = get_args(field_type)

        # Handle Optional types
        if origin is type(None) or (origin is not None and type(None) in args):
            if origin is not None:
                # Get the non-None type
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    return self._get_pg_type(non_none_args[0], field_info)
            return "TEXT"

        # Handle list types
        if origin is list or origin is Sequence:
            if args:
                inner_type = args[0]
                # If it's a list of RealmSyncModel, we'll use junction table
                # For now, return JSONB for primitive lists
                if inspect.isclass(inner_type) and issubclass(inner_type, RealmSyncModel):
                    return "TEXT"  # Will be handled as FK in junction table
                return "JSONB"
            return "JSONB"

        # Handle dict types
        if origin is dict or field_type is dict:
            return "JSONB"

        # Handle primitive types
        if field_type is str or field_type is str | None:
            return "TEXT"
        if field_type is int or field_type is int | None:
            return "INTEGER"
        if field_type is float or field_type is float | None:
            return "DOUBLE PRECISION"
        if field_type is bool or field_type is bool | None:
            return "BOOLEAN"

        # Handle RealmSyncModel subclasses
        if inspect.isclass(field_type) and issubclass(field_type, RealmSyncModel):
            return "TEXT"  # Will store as FK reference

        # Default to TEXT
        return "TEXT"

    def _is_realm_sync_model(self, field_type: type[Any]) -> bool:
        """Check if a type is a RealmSyncModel subclass."""
        origin = get_origin(field_type)
        args = get_args(field_type)

        # Handle Optional
        if origin is not None and type(None) in args:
            non_none_args = [arg for arg in args if arg is not type(None)]
            if non_none_args:
                field_type = non_none_args[0]

        if inspect.isclass(field_type) and issubclass(field_type, RealmSyncModel):
            return True

        # Check if it's a list of RealmSyncModel
        if origin is list or origin is Sequence:
            if args:
                inner_type = args[0]
                if inspect.isclass(inner_type) and issubclass(inner_type, RealmSyncModel):
                    return True

        return False

    def _get_nested_model_class(self, field_type: type[Any]) -> type[RealmSyncModel] | None:
        """Extract RealmSyncModel class from a field type."""
        origin = get_origin(field_type)
        args = get_args(field_type)

        # Handle Optional
        if origin is not None and type(None) in args:
            non_none_args = [arg for arg in args if arg is not type(None)]
            if non_none_args:
                field_type = non_none_args[0]

        if inspect.isclass(field_type) and issubclass(field_type, RealmSyncModel):
            return field_type

        # Check if it's a list of RealmSyncModel
        if origin is list or origin is Sequence:
            if args:
                inner_type = args[0]
                if inspect.isclass(inner_type) and issubclass(inner_type, RealmSyncModel):
                    return inner_type

        return None

    async def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        await self._ensure_connection()
        result = await self.postgres.fetch_one(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = $1
            )
            """,
            table_name,
        )
        return result is not None and result.get("exists", False) if result else False

    async def _get_table_columns(self, table_name: str) -> dict[str, str]:
        """
        Get all columns and their types from a table.

        Returns:
            Dictionary mapping column name to PostgreSQL type
        """
        await self._ensure_connection()
        columns = await self.postgres.fetch_all(
            """
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = $1
            """,
            table_name,
        )
        result: dict[str, str] = {}
        for col in columns:
            col_name = col["column_name"]
            data_type = col["data_type"]
            udt_name = col.get("udt_name", "")
            # Map PostgreSQL types to our type system
            if data_type == "character varying" or data_type == "text":
                result[col_name] = "TEXT"
            elif data_type == "integer":
                result[col_name] = "INTEGER"
            elif data_type == "double precision" or data_type == "real":
                result[col_name] = "DOUBLE PRECISION"
            elif data_type == "boolean":
                result[col_name] = "BOOLEAN"
            elif data_type == "jsonb" or data_type == "json":
                result[col_name] = "JSONB"
            elif udt_name == "uuid":
                result[col_name] = "TEXT"
            else:
                result[col_name] = data_type.upper()
        return result

    async def register_model(self, model_class: type[T]) -> None:
        """
        Register a Pydantic model and create/update its database table.

        Args:
            model_class: Pydantic model class that inherits from RealmSyncModel

        Raises:
            ValueError: If model is not a RealmSyncModel subclass
            ValueError: If a new field has no default value
        """
        if not issubclass(model_class, RealmSyncModel):
            raise ValueError(f"Model {model_class.__name__} must inherit from RealmSyncModel")

        await self._ensure_connection()

        table_name = self._get_table_name(model_class)
        model_fields = model_class.model_fields
        nested_models: dict[str, type[RealmSyncModel]] = {}
        list_fields: dict[str, type[Any]] = {}

        # Analyze fields
        for field_name, field_info in model_fields.items():
            field_type = field_info.annotation
            nested_model = self._get_nested_model_class(field_type)
            if nested_model:
                nested_models[field_name] = nested_model
                # Register nested model first
                if nested_model not in self._registered_models:
                    await self.register_model(nested_model)

            # Check if it's a list field
            origin = get_origin(field_type)
            if origin is list or origin is Sequence:
                list_fields[field_name] = field_type

        # Store metadata
        self._model_metadata[model_class] = {
            "nested_models": nested_models,
            "list_fields": list_fields,
        }

        # Check if table exists
        table_exists = await self._table_exists(table_name)

        if not table_exists:
            # Create new table
            await self._create_table(model_class, table_name, nested_models)
        else:
            # Update existing table
            await self._update_table(model_class, table_name, nested_models)

        # Handle list fields - create junction tables
        for field_name, field_type in list_fields.items():
            await self._ensure_list_table(model_class, table_name, field_name, field_type)

        self._registered_models[model_class] = table_name

    async def _create_table(
        self,
        model_class: type[RealmSyncModel],
        table_name: str,
        nested_models: dict[str, type[RealmSyncModel]],
    ) -> None:
        """Create a new table for a model."""
        await self._ensure_connection()

        columns: list[str] = []
        model_fields = model_class.model_fields

        # Add id column (primary key)
        columns.append("id TEXT PRIMARY KEY")

        # Add soft_deleted column
        columns.append("soft_deleted BOOLEAN NOT NULL DEFAULT FALSE")

        # Add metadata column
        columns.append("metadata JSONB NOT NULL DEFAULT '{}'::jsonb")

        # Add other fields
        for field_name, field_info in model_fields.items():
            # Skip metadata as it's already added
            if field_name == "metadata":
                continue

            field_type = field_info.annotation

            # Handle nested models as foreign keys
            if field_name in nested_models:
                nested_table = self._get_table_name(nested_models[field_name])
                columns.append(f"{field_name}_id TEXT REFERENCES {nested_table}(id)")
                continue

            # Skip list fields (handled by junction tables)
            origin = get_origin(field_type)
            if origin is list or origin is Sequence:
                continue

            # Get PostgreSQL type
            pg_type = self._get_pg_type(field_type, field_info)

            # Build column definition
            col_def = f"{field_name} {pg_type}"

            # Add NOT NULL if field is required
            if field_info.is_required() and field_name not in ("id", "soft_deleted", "metadata"):
                col_def += " NOT NULL"

            # Add default if present
            if field_info.default is not inspect.Parameter.empty:
                default = field_info.default
                if isinstance(default, str):
                    col_def += f" DEFAULT '{default}'"
                elif isinstance(default, int | float | bool):
                    col_def += f" DEFAULT {default}"
                elif default is None:
                    col_def += " DEFAULT NULL"

            columns.append(col_def)

        # Create table
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        await self.postgres.execute(create_sql)

    async def _update_table(
        self,
        model_class: type[RealmSyncModel],
        table_name: str,
        nested_models: dict[str, type[RealmSyncModel]],
    ) -> None:
        """Update an existing table to match the model schema."""
        await self._ensure_connection()

        existing_columns = await self._get_table_columns(table_name)
        model_fields = model_class.model_fields

        # Track fields that should exist
        expected_columns: set[str] = {"id", "soft_deleted", "metadata"}

        # Check each model field
        for field_name, field_info in model_fields.items():
            if field_name == "metadata":
                continue

            field_type = field_info.annotation

            # Handle nested models
            if field_name in nested_models:
                fk_column = f"{field_name}_id"
                expected_columns.add(fk_column)
                if fk_column not in existing_columns:
                    # Add foreign key column
                    nested_table = self._get_table_name(nested_models[field_name])
                    await self.postgres.execute(
                        f"ALTER TABLE {table_name} ADD COLUMN {fk_column} TEXT REFERENCES {nested_table}(id)"
                    )
                continue

            # Skip list fields
            origin = get_origin(field_type)
            if origin is list or origin is Sequence:
                continue

            expected_columns.add(field_name)

            if field_name not in existing_columns:
                # New field - need to add it
                pg_type = self._get_pg_type(field_type, field_info)
                col_def = f"{field_name} {pg_type}"

                # Check for default value
                if field_info.default is inspect.Parameter.empty:
                    if field_info.is_required():
                        raise ValueError(
                            f"Cannot add required field '{field_name}' to existing table '{table_name}' without a default value"
                        )
                    col_def += " DEFAULT NULL"
                else:
                    default = field_info.default
                    if isinstance(default, str):
                        col_def += f" DEFAULT '{default}'"
                    elif isinstance(default, int | float | bool):
                        col_def += f" DEFAULT {default}"
                    elif default is None:
                        col_def += " DEFAULT NULL"

                await self.postgres.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_def}")

        # Remove columns that no longer exist in model
        for col_name in existing_columns:
            if col_name not in expected_columns and not col_name.endswith("_id"):
                # Check if it's a foreign key we should keep
                is_fk = False
                for field_name in nested_models:
                    if col_name == f"{field_name}_id":
                        is_fk = True
                        break
                if not is_fk:
                    await self.postgres.execute(
                        f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {col_name}"
                    )

    async def _ensure_list_table(
        self,
        model_class: type[RealmSyncModel],
        parent_table: str,
        field_name: str,
        field_type: type[Any],
    ) -> None:
        """Create or ensure junction table exists for a list field."""
        await self._ensure_connection()

        args = get_args(field_type)
        inner_type = args[0] if args else None

        # Determine junction table name
        if inspect.isclass(inner_type) and issubclass(inner_type, RealmSyncModel):
            # List of models - use junction table
            junction_table = f"{parent_table}_{field_name}"
            nested_table = self._get_table_name(inner_type)

            # Check if junction table exists
            if not await self._table_exists(junction_table):
                await self.postgres.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {junction_table} (
                        {parent_table}_id TEXT NOT NULL REFERENCES {parent_table}(id) ON DELETE CASCADE,
                        {nested_table}_id TEXT NOT NULL REFERENCES {nested_table}(id) ON DELETE CASCADE,
                        PRIMARY KEY ({parent_table}_id, {nested_table}_id)
                    )
                    """
                )
        else:
            # List of primitives - use separate table
            list_table = f"{parent_table}_{field_name}_items"

            if not await self._table_exists(list_table):
                pg_type = self._get_pg_type(inner_type if inner_type else str, None)
                await self.postgres.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {list_table} (
                        id SERIAL PRIMARY KEY,
                        {parent_table}_id TEXT NOT NULL REFERENCES {parent_table}(id) ON DELETE CASCADE,
                        value {pg_type} NOT NULL,
                        index INTEGER NOT NULL
                    )
                    """
                )

    async def select(
        self,
        model_class: type[T],
        filters: dict[str, Any] | None = None,
        include_deleted: bool = False,
    ) -> list[T]:
        """
        Select models from the database.

        Args:
            model_class: Model class to select
            filters: Dictionary of field names to values for filtering
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of model instances
        """
        if model_class not in self._registered_models:
            await self.register_model(model_class)

        await self._ensure_connection()

        table_name = self._registered_models[model_class]
        metadata = self._model_metadata.get(model_class, {})
        nested_models = metadata.get("nested_models", {})
        list_fields = metadata.get("list_fields", {})

        # Build SELECT query with JOINs
        select_fields: list[str] = [f"{table_name}.*"]
        joins: list[str] = []
        where_clauses: list[str] = []
        params: list[Any] = []
        param_index = 1

        # Add JOINs for nested models
        for field_name, nested_model_class in nested_models.items():
            nested_table = self._get_table_name(nested_model_class)
            joins.append(
                f"LEFT JOIN {nested_table} ON {table_name}.{field_name}_id = {nested_table}.id"
            )
            # Add nested model fields to select (with prefix to avoid conflicts)
            nested_fields = nested_model_class.model_fields.keys()
            for nested_field in nested_fields:
                select_fields.append(
                    f"{nested_table}.{nested_field} AS {field_name}__{nested_field}"
                )

        # Build WHERE clause
        if not include_deleted:
            where_clauses.append(f"{table_name}.soft_deleted = FALSE")

        if filters:
            for field_name, value in filters.items():
                if field_name in nested_models:
                    where_clauses.append(f"{table_name}.{field_name}_id = ${param_index}")
                else:
                    where_clauses.append(f"{table_name}.{field_name} = ${param_index}")
                params.append(value)
                param_index += 1

        # Build query
        query = f"SELECT {', '.join(select_fields)} FROM {table_name}"
        if joins:
            query += " " + " ".join(joins)
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        # Execute query
        rows = await self.postgres.fetch_all(query, *params)

        # Convert rows to model instances
        results: list[T] = []
        for row in rows:
            # Extract main model data
            model_data: dict[str, Any] = {}
            nested_data: dict[str, dict[str, Any]] = {}

            for key, value in row.items():
                # Check if this is a nested field (using double underscore separator)
                if "__" in key:
                    parts = key.split("__", 1)
                    if len(parts) == 2:
                        nested_field_name, nested_field = parts
                        if nested_field_name in nested_models:
                            if nested_field_name not in nested_data:
                                nested_data[nested_field_name] = {}
                            nested_data[nested_field_name][nested_field] = value
                            continue
                # Regular field
                model_data[key] = value

            # Reconstruct nested models
            for field_name, nested_model_class in nested_models.items():
                if field_name in nested_data:
                    nested_model_data = nested_data[field_name]
                    # Use the ID from the FK column if not in nested_data
                    if "id" not in nested_model_data or nested_model_data["id"] is None:
                        nested_model_data["id"] = model_data.get(f"{field_name}_id")
                    # Only create nested model if we have an ID
                    if nested_model_data.get("id"):
                        nested_model = nested_model_class(**nested_model_data)
                        model_data[field_name] = nested_model
                    else:
                        model_data[field_name] = None
                elif f"{field_name}_id" in model_data:
                    # FK exists but no nested data - set to None
                    model_data[field_name] = None

            # Remove _id fields from model_data
            for field_name in nested_models:
                model_data.pop(f"{field_name}_id", None)

            # Load list fields
            for field_name in list_fields:
                list_values = await self._load_list_field(
                    model_class, table_name, field_name, model_data["id"]
                )
                model_data[field_name] = list_values

            # Remove internal fields
            model_data.pop("soft_deleted", None) if not include_deleted else None

            try:
                instance = model_class(**model_data)
                results.append(instance)
            except Exception:
                # Skip rows that can't be converted
                continue

        return results

    async def _load_list_field(
        self, model_class: type[RealmSyncModel], table_name: str, field_name: str, parent_id: str
    ) -> list[Any]:
        """Load list field values from junction/array table."""
        await self._ensure_connection()

        list_fields = self._model_metadata.get(model_class, {}).get("list_fields", {})
        field_type = list_fields.get(field_name, list)
        args = get_args(field_type)
        inner_type = args[0] if args else None

        if inspect.isclass(inner_type) and issubclass(inner_type, RealmSyncModel):
            # Load from junction table
            junction_table = f"{table_name}_{field_name}"
            nested_table = self._get_table_name(inner_type)
            rows = await self.postgres.fetch_all(
                f"""
                SELECT {nested_table}.*
                FROM {junction_table}
                JOIN {nested_table} ON {junction_table}.{nested_table}_id = {nested_table}.id
                WHERE {junction_table}.{table_name}_id = $1
                """,
                parent_id,
            )
            return [inner_type(**dict(row)) for row in rows]
        else:
            # Load from array table
            list_table = f"{table_name}_{field_name}_items"
            rows = await self.postgres.fetch_all(
                f"""
                SELECT value FROM {list_table}
                WHERE {table_name}_id = $1
                ORDER BY index
                """,
                parent_id,
            )
            return [row["value"] for row in rows]

    async def create(self, instance: T) -> T:
        """
        Create a new model instance in the database.

        Args:
            instance: Model instance to create

        Returns:
            Created model instance with generated ID if needed
        """
        model_class = type(instance)
        if model_class not in self._registered_models:
            await self.register_model(model_class)

        await self._ensure_connection()

        table_name = self._registered_models[model_class]
        metadata = self._model_metadata.get(model_class, {})
        nested_models = metadata.get("nested_models", {})
        list_fields = metadata.get("list_fields", {})

        # Generate ID if not present
        if instance.id is None:
            instance.id = str(uuid.uuid4())

        # Handle nested models
        nested_fk_values: dict[str, str] = {}
        for field_name, nested_model_class in nested_models.items():
            nested_value = getattr(instance, field_name, None)
            if nested_value is not None:
                if isinstance(nested_value, RealmSyncModel):
                    # Ensure nested model exists
                    if nested_value.id is None:
                        nested_value = await self.create(nested_value)
                    else:
                        # Check if it exists, if not create it
                        existing = await self.select(nested_model_class, {"id": nested_value.id})
                        if not existing:
                            nested_value = await self.create(nested_value)
                    nested_fk_values[f"{field_name}_id"] = nested_value.id
                elif isinstance(nested_value, str):
                    nested_fk_values[f"{field_name}_id"] = nested_value

        # Prepare insert data
        insert_data: dict[str, Any] = {
            "id": instance.id,
            "soft_deleted": instance.soft_deleted,
            "metadata": instance.metadata,
        }

        # Add regular fields
        for field_name in model_class.model_fields:
            if field_name in ("id", "soft_deleted", "metadata"):
                continue
            if field_name in nested_models:
                continue
            if field_name in list_fields:
                continue

            value = getattr(instance, field_name, None)
            if value is not None:
                insert_data[field_name] = value

        # Add nested FK values
        insert_data.update(nested_fk_values)

        # Build INSERT query
        columns = list(insert_data.keys())
        placeholders = [f"${i + 1}" for i in range(len(columns))]
        values = list(insert_data.values())

        query = f"""
        INSERT INTO {table_name} ({", ".join(columns)})
        VALUES ({", ".join(placeholders)})
        """

        await self.postgres.execute(query, *values)

        # Handle list fields
        for field_name in list_fields:
            list_value = getattr(instance, field_name, None)
            if list_value:
                await self._save_list_field(table_name, field_name, instance.id, list_value)

        return instance

    async def _save_list_field(
        self, table_name: str, field_name: str, parent_id: str, values: list[Any]
    ) -> None:
        """Save list field values to junction/array table."""
        await self._ensure_connection()

        model_class = None
        for cls in self._model_metadata:
            if self._registered_models.get(cls) == table_name:
                model_class = cls
                break

        if not model_class:
            return

        list_fields = self._model_metadata.get(model_class, {}).get("list_fields", {})
        field_type = list_fields.get(field_name)

        if not field_type:
            return

        args = get_args(field_type)
        inner_type = args[0] if args else None

        if inspect.isclass(inner_type) and issubclass(inner_type, RealmSyncModel):
            # Save to junction table
            junction_table = f"{table_name}_{field_name}"
            nested_table = self._get_table_name(inner_type)

            # Delete existing relationships
            await self.postgres.execute(
                f"DELETE FROM {junction_table} WHERE {table_name}_id = $1",
                parent_id,
            )

            # Insert new relationships
            for value in values:
                if isinstance(value, RealmSyncModel):
                    nested_id = value.id
                    if nested_id is None:
                        value = await self.create(value)
                        nested_id = value.id
                    await self.postgres.execute(
                        f"""
                        INSERT INTO {junction_table} ({table_name}_id, {nested_table}_id)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                        """,
                        parent_id,
                        nested_id,
                    )
                elif isinstance(value, str):
                    await self.postgres.execute(
                        f"""
                        INSERT INTO {junction_table} ({table_name}_id, {nested_table}_id)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                        """,
                        parent_id,
                        value,
                    )
        else:
            # Save to array table
            list_table = f"{table_name}_{field_name}_items"

            # Delete existing values
            await self.postgres.execute(
                f"DELETE FROM {list_table} WHERE {table_name}_id = $1",
                parent_id,
            )

            # Insert new values
            for index, value in enumerate(values):
                await self.postgres.execute(
                    f"""
                    INSERT INTO {list_table} ({table_name}_id, value, index)
                    VALUES ($1, $2, $3)
                    """,
                    parent_id,
                    value,
                    index,
                )

    async def _save_list_field_with_conn(
        self,
        conn: asyncpg.Connection,
        table_name: str,
        field_name: str,
        parent_id: str,
        values: list[Any],
    ) -> None:
        """Save list field values to junction/array table using provided connection."""
        model_class = None
        for cls in self._model_metadata:
            if self._registered_models.get(cls) == table_name:
                model_class = cls
                break

        if not model_class:
            return

        list_fields = self._model_metadata.get(model_class, {}).get("list_fields", {})
        field_type = list_fields.get(field_name)

        if not field_type:
            return

        args = get_args(field_type)
        inner_type = args[0] if args else None

        if inspect.isclass(inner_type) and issubclass(inner_type, RealmSyncModel):
            # Save to junction table
            junction_table = f"{table_name}_{field_name}"
            nested_table = self._get_table_name(inner_type)

            # Delete existing relationships
            await conn.execute(
                f"DELETE FROM {junction_table} WHERE {table_name}_id = $1",
                parent_id,
            )

            # Insert new relationships
            for value in values:
                if isinstance(value, RealmSyncModel):
                    nested_id = value.id
                    if nested_id is None:
                        value = await self._create_with_conn(conn, value)
                        nested_id = value.id
                    await conn.execute(
                        f"""
                        INSERT INTO {junction_table} ({table_name}_id, {nested_table}_id)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                        """,
                        parent_id,
                        nested_id,
                    )
                elif isinstance(value, str):
                    await conn.execute(
                        f"""
                        INSERT INTO {junction_table} ({table_name}_id, {nested_table}_id)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                        """,
                        parent_id,
                        value,
                    )
        else:
            # Save to array table
            list_table = f"{table_name}_{field_name}_items"

            # Delete existing values
            await conn.execute(
                f"DELETE FROM {list_table} WHERE {table_name}_id = $1",
                parent_id,
            )

            # Insert new values
            for index, value in enumerate(values):
                await conn.execute(
                    f"""
                    INSERT INTO {list_table} ({table_name}_id, value, index)
                    VALUES ($1, $2, $3)
                    """,
                    parent_id,
                    value,
                    index,
                )

    async def _create_with_conn(self, conn: asyncpg.Connection, instance: T) -> T:
        """
        Create a new model instance in the database using the provided connection.

        Args:
            conn: Database connection to use
            instance: Model instance to create

        Returns:
            Created model instance with generated ID if needed
        """
        model_class = type(instance)
        if model_class not in self._registered_models:
            await self.register_model(model_class)

        table_name = self._registered_models[model_class]
        metadata = self._model_metadata.get(model_class, {})
        nested_models = metadata.get("nested_models", {})
        list_fields = metadata.get("list_fields", {})

        # Generate ID if not present
        if instance.id is None:
            instance.id = str(uuid.uuid4())

        # Handle nested models
        nested_fk_values: dict[str, str] = {}
        for field_name, nested_model_class in nested_models.items():
            nested_value = getattr(instance, field_name, None)
            if nested_value is not None:
                if isinstance(nested_value, RealmSyncModel):
                    # Ensure nested model exists
                    if nested_value.id is None:
                        nested_value = await self._create_with_conn(conn, nested_value)
                    else:
                        # Check if it exists using the connection
                        row = await conn.fetchrow(
                            f"SELECT id FROM {self._registered_models[nested_model_class]} WHERE id = $1",
                            nested_value.id,
                        )
                        if row is None:
                            nested_value = await self._create_with_conn(conn, nested_value)
                    nested_fk_values[f"{field_name}_id"] = nested_value.id
                elif isinstance(nested_value, str):
                    nested_fk_values[f"{field_name}_id"] = nested_value

        # Prepare insert data
        insert_data: dict[str, Any] = {
            "id": instance.id,
            "soft_deleted": instance.soft_deleted,
            "metadata": instance.metadata,
        }

        # Add regular fields
        for field_name in model_class.model_fields:
            if field_name in ("id", "soft_deleted", "metadata"):
                continue
            if field_name in nested_models:
                continue
            if field_name in list_fields:
                continue

            value = getattr(instance, field_name, None)
            if value is not None:
                insert_data[field_name] = value

        # Add nested FK values
        insert_data.update(nested_fk_values)

        # Build INSERT query
        columns = list(insert_data.keys())
        placeholders = [f"${i + 1}" for i in range(len(columns))]
        values = list(insert_data.values())

        query = f"""
        INSERT INTO {table_name} ({", ".join(columns)})
        VALUES ({", ".join(placeholders)})
        """

        await conn.execute(query, *values)

        # Handle list fields
        for field_name in list_fields:
            list_value = getattr(instance, field_name, None)
            if list_value:
                await self._save_list_field_with_conn(
                    conn, table_name, field_name, instance.id, list_value
                )

        return instance

    async def bulk_create(self, instances: list[T]) -> list[T]:
        """
        Create multiple model instances in a transaction.

        Args:
            instances: List of model instances to create

        Returns:
            List of created model instances
        """
        if not instances:
            return []

        # Use the first instance's class
        model_class = type(instances[0])

        # Ensure all instances are of the same type
        for instance in instances:
            if type(instance) is not model_class:
                raise ValueError("All instances must be of the same model class")

        # Ensure connection pool is available
        await self._ensure_connection()

        # Acquire a connection from the pool
        assert self.postgres._pool is not None
        conn = await self.postgres._pool.acquire()

        try:
            # Wrap all inserts in a single transaction
            async with conn.transaction():
                results: list[T] = []
                for instance in instances:
                    result = await self._create_with_conn(conn, instance)
                    results.append(result)
                return results
        finally:
            # Release the connection back to the pool
            await self.postgres._pool.release(conn)

    async def soft_delete(self, model_class: type[T], instance_id: str) -> None:
        """
        Soft delete a model instance.

        Args:
            model_class: Model class
            instance_id: ID of the instance to delete
        """
        if model_class not in self._registered_models:
            await self.register_model(model_class)

        await self._ensure_connection()

        table_name = self._registered_models[model_class]
        await self.postgres.execute(
            f"UPDATE {table_name} SET soft_deleted = TRUE WHERE id = $1",
            instance_id,
        )


# Global postgres client management
POSTGRES_CLIENT: RealmSyncDatabase | None = None


def set_postgres_client(postgres_client: RealmSyncDatabase) -> None:
    """Set the global postgres client."""
    global POSTGRES_CLIENT
    POSTGRES_CLIENT = postgres_client


def get_postgres_client() -> RealmSyncDatabase:
    """Get the global postgres client."""
    global POSTGRES_CLIENT
    if POSTGRES_CLIENT is None:
        raise ValueError("Postgres client not found")
    return POSTGRES_CLIENT
