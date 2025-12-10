#!/usr/bin/env python3
"""RealmSync CLI tool for project management and migrations."""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

app = typer.Typer(
    help="RealmSync CLI tool for project management and migrations",
    invoke_without_command=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    """Main callback for rs command."""
    if ctx.invoked_subcommand is None:
        # If no command provided, show help
        console.print("Use [bold cyan]rs start-project[/bold cyan] to create a new project")
        console.print("Use [bold cyan]rs --help[/bold cyan] for more information")
        raise typer.Exit()


def get_project_root() -> Path:
    """Get the project root directory."""
    script_dir = Path(__file__).parent
    return script_dir.parent


def get_scaffold_dir() -> Path:
    """Get the scaffold templates directory."""
    script_dir = Path(__file__).parent
    return script_dir / "scaffold"


@app.command("start-project")
def start_project() -> None:
    """Initialize a new RealmSync project with interactive prompts."""
    console.print(
        Panel.fit("[bold blue]🚀 RealmSync Project Setup[/bold blue]", border_style="blue")
    )
    console.print()

    # Basic project information
    console.print("[bold cyan]Project Information[/bold cyan]")
    name = Prompt.ask("Enter project name", default="my_realm_sync_project")
    # Generate directory name from project name: lowercase and replace spaces with hyphens
    directory = name.lower().replace(" ", "-").replace("_", "-")
    # Generate package name: lowercase and replace spaces/dashes with underscores
    package_name = name.lower().replace(" ", "_").replace("-", "_")
    console.print(f"[dim]Project directory: {directory}[/dim]")
    console.print(f"[dim]Package name: {package_name}[/dim]")
    console.print()

    # Configuration options
    console.print("[bold cyan]Configuration Options[/bold cyan]")
    use_redis = Confirm.ask("Include Redis client?", default=True)
    use_postgres = Confirm.ask("Include PostgreSQL client?", default=True)
    use_auth = Confirm.ask("Include authentication?", default=True)
    use_web_manager = Confirm.ask("Include web management interface?", default=True)

    web_manager_prefix = "/admin"
    if use_web_manager:
        web_manager_prefix = Prompt.ask("Web manager prefix", default="/admin")
    console.print()

    # Redis configuration
    redis_config = {}
    if use_redis:
        console.print("[bold cyan]Redis Configuration[/bold cyan]")
        redis_config["host"] = Prompt.ask("Redis host", default="localhost")
        redis_config["port"] = Prompt.ask("Redis port", default="6379")
        redis_config["db"] = Prompt.ask("Redis database", default="0")
        console.print()

    # PostgreSQL configuration
    postgres_config = {}
    if use_postgres:
        console.print("[bold cyan]PostgreSQL Configuration[/bold cyan]")
        postgres_config["host"] = Prompt.ask("PostgreSQL host", default="localhost")
        postgres_config["port"] = Prompt.ask("PostgreSQL port", default="5432")
        postgres_config["user"] = Prompt.ask("PostgreSQL user", default="realm_sync")
        postgres_config["password"] = Prompt.ask(
            "PostgreSQL password", default="realm_sync_password"
        )
        postgres_config["database"] = Prompt.ask("PostgreSQL database", default="realm_sync_db")
        console.print()

    # Confirm before creating
    console.print(
        Panel.fit(
            f"[yellow]Ready to create project '{name}' in '{directory}'[/yellow]",
            border_style="yellow",
        )
    )
    if not Confirm.ask("Continue with project creation?"):
        console.print("[red]❌ Project creation cancelled.[/red]")
        sys.exit(1)

    project_path = Path(directory).resolve()

    if project_path.exists() and any(project_path.iterdir()):
        if not Confirm.ask(
            f"[yellow]Directory {directory} already exists and is not empty. Overwrite?[/yellow]"
        ):
            console.print("[red]❌ Project creation cancelled.[/red]")
            sys.exit(1)

    project_path.mkdir(parents=True, exist_ok=True)

    # Create directory structure
    console.print()
    console.print(f"[green]📁 Creating project structure in {project_path}...[/green]")

    directories = [
        package_name,
        "tests",
    ]

    for dir_path in directories:
        (project_path / dir_path).mkdir(parents=True, exist_ok=True)

    # Create __init__.py files
    init_files = [
        f"{package_name}/__init__.py",
        "tests/__init__.py",
    ]

    for init_file in init_files:
        (project_path / init_file).touch()

    # Load scaffold templates
    scaffold_dir = get_scaffold_dir()

    # Create auth.py if authentication is enabled
    if use_auth:
        auth_template = (scaffold_dir / "auth.py").read_text()
        (project_path / package_name / "auth.py").write_text(auth_template)

    # Create redis.py if Redis is enabled
    if use_redis:
        redis_template = (scaffold_dir / "redis.py").read_text()
        (project_path / package_name / "redis.py").write_text(redis_template)

    # Create postgres.py if PostgreSQL is enabled
    if use_postgres:
        postgres_template = (scaffold_dir / "postgres.py").read_text()
        (project_path / package_name / "postgres.py").write_text(postgres_template)

    # Create main.py with custom configuration
    # Build main.py content based on selected options
    main_lines = ['"""Main application entry point."""', ""]
    main_lines.append("import os")
    main_lines.append("")

    imports = ["from realm_sync_api import RealmSyncApi"]
    if use_auth:
        imports.append("from realm_sync_api.dependencies.auth import RealmSyncAuth")
    if use_web_manager:
        imports.append("from realm_sync_api.dependencies.web_manager import WebManager")
    if use_redis:
        imports.append("from realm_sync_api import RealmSyncRedis")
    if use_postgres:
        imports.append("from realm_sync_api import RealmSyncDatabase")

    main_lines.extend(imports)
    main_lines.append("")

    if use_auth:
        main_lines.append("auth = RealmSyncAuth()")
        main_lines.append("")

    app_args = []
    if use_auth:
        app_args.append("    auth=auth,")
    if use_web_manager:
        web_manager_args = f'        prefix="{web_manager_prefix}",'
        if use_auth:
            web_manager_args += "\n        auth=auth,"
        app_args.append(f"    web_manager=WebManager(\n{web_manager_args}\n    ),")
    if use_redis:
        main_lines.append("redis_client = RealmSyncRedis(")
        main_lines.append('    host=os.getenv("REDIS_HOST", "localhost"),')
        main_lines.append('    port=int(os.getenv("REDIS_PORT", "6379")),')
        main_lines.append('    db=int(os.getenv("REDIS_DB", "0")),')
        main_lines.append(")")
        main_lines.append("")
        app_args.append("    redis_client=redis_client,")
    if use_postgres:
        main_lines.append("postgres_client = RealmSyncDatabase(")
        main_lines.append('    host=os.getenv("POSTGRES_HOST", "localhost"),')
        main_lines.append('    port=int(os.getenv("POSTGRES_PORT", "5432")),')
        main_lines.append('    user=os.getenv("POSTGRES_USER", "realm_sync"),')
        main_lines.append('    password=os.getenv("POSTGRES_PASSWORD", "realm_sync_password"),')
        main_lines.append('    database=os.getenv("POSTGRES_DB", "realm_sync_db"),')
        main_lines.append(")")
        main_lines.append("")
        app_args.append("    postgres_client=postgres_client,")

    main_lines.append("app = RealmSyncApi(")
    if app_args:
        main_lines.extend(app_args)
    main_lines.append(")")

    main_content = "\n".join(main_lines)
    (project_path / package_name / "main.py").write_text(main_content)

    # Create .env with custom configuration
    env_lines = []
    if use_redis:
        env_lines.append("# Redis Configuration")
        env_lines.append(f"REDIS_HOST={redis_config['host']}")
        env_lines.append(f"REDIS_PORT={redis_config['port']}")
        env_lines.append(f"REDIS_DB={redis_config['db']}")
        env_lines.append("")
    if use_postgres:
        env_lines.append("# PostgreSQL Configuration")
        env_lines.append(f"POSTGRES_HOST={postgres_config['host']}")
        env_lines.append(f"POSTGRES_PORT={postgres_config['port']}")
        env_lines.append(f"POSTGRES_USER={postgres_config['user']}")
        env_lines.append(f"POSTGRES_PASSWORD={postgres_config['password']}")
        env_lines.append(f"POSTGRES_DB={postgres_config['database']}")

    env_content = "\n".join(env_lines)
    (project_path / ".env").write_text(env_content)

    # Create pyproject.toml
    pyproject_template = (scaffold_dir / "pyproject.toml").read_text()
    pyproject_content = pyproject_template.replace("{PROJECT_NAME}", package_name.replace("_", "-"))
    pyproject_content = pyproject_content.replace("{PACKAGE_NAME}", package_name)
    (project_path / "pyproject.toml").write_text(pyproject_content)

    # Create Dockerfile
    dockerfile_template = (scaffold_dir / "Dockerfile").read_text()
    dockerfile_content = dockerfile_template.replace("{PACKAGE_NAME}", package_name)
    (project_path / "Dockerfile").write_text(dockerfile_content)

    # Create docker-compose.yml
    compose_lines = ["", "services:"]

    # Add app service
    compose_lines.append("  app:")
    compose_lines.append("    build:")
    compose_lines.append("      context: .")
    compose_lines.append("      dockerfile: Dockerfile")
    compose_lines.append(f"    container_name: {package_name}_app")
    compose_lines.append("    ports:")
    compose_lines.append('      - "8000:8000"')
    compose_lines.append("    environment:")

    app_depends_on = []
    if use_redis:
        compose_lines.append("      REDIS_HOST: redis")
        compose_lines.append(f"      REDIS_PORT: {redis_config['port']}")
        compose_lines.append(f"      REDIS_DB: {redis_config['db']}")
        app_depends_on.append("redis")

    if use_postgres:
        compose_lines.append("      POSTGRES_HOST: postgres")
        compose_lines.append(f"      POSTGRES_PORT: {postgres_config['port']}")
        compose_lines.append(f"      POSTGRES_USER: {postgres_config['user']}")
        compose_lines.append(f"      POSTGRES_PASSWORD: {postgres_config['password']}")
        compose_lines.append(f"      POSTGRES_DB: {postgres_config['database']}")
        app_depends_on.append("postgres")

    if app_depends_on:
        compose_lines.append("    depends_on:")
        for service in app_depends_on:
            compose_lines.append(f"      {service}:")
            compose_lines.append("        condition: service_healthy")
    compose_lines.append("    volumes:")
    compose_lines.append("      - .:/app")
    compose_lines.append("")

    # Add postgres service if enabled
    if use_postgres:
        compose_lines.append("  postgres:")
        compose_lines.append("    image: postgres:15-alpine")
        compose_lines.append(f"    container_name: {package_name}_postgres")
        compose_lines.append("    environment:")
        compose_lines.append(f"      POSTGRES_USER: {postgres_config['user']}")
        compose_lines.append(f"      POSTGRES_PASSWORD: {postgres_config['password']}")
        compose_lines.append(f"      POSTGRES_DB: {postgres_config['database']}")
        compose_lines.append("    ports:")
        compose_lines.append(f'      - "{postgres_config["port"]}:5432"')
        compose_lines.append("    volumes:")
        compose_lines.append("      - postgres_data:/var/lib/postgresql/data")
        compose_lines.append("    healthcheck:")
        compose_lines.append(
            f'      test: [ "CMD-SHELL", "pg_isready -U {postgres_config["user"]}" ]'
        )
        compose_lines.append("      interval: 10s")
        compose_lines.append("      timeout: 5s")
        compose_lines.append("      retries: 5")
        compose_lines.append("")

    # Add redis service if enabled
    if use_redis:
        compose_lines.append("  redis:")
        compose_lines.append("    image: redis:7-alpine")
        compose_lines.append(f"    container_name: {package_name}_redis")
        compose_lines.append("    ports:")
        compose_lines.append(f'      - "{redis_config["port"]}:6379"')
        compose_lines.append("    healthcheck:")
        compose_lines.append('      test: [ "CMD", "redis-cli", "ping" ]')
        compose_lines.append("      interval: 10s")
        compose_lines.append("      timeout: 5s")
        compose_lines.append("      retries: 5")
        compose_lines.append("")

    # Add volumes section if postgres is enabled
    if use_postgres:
        compose_lines.append("volumes:")
        compose_lines.append("  postgres_data:")

    compose_content = "\n".join(compose_lines)
    (project_path / "docker-compose.yml").write_text(compose_content)

    # Create .dockerignore
    dockerignore_template = (scaffold_dir / ".dockerignore").read_text()
    (project_path / ".dockerignore").write_text(dockerignore_template)

    # Create README.md
    readme_template = (scaffold_dir / "README.md").read_text()
    readme_content = readme_template.replace("{PROJECT_NAME}", name)
    readme_content = readme_content.replace("{PACKAGE_NAME}", package_name)
    (project_path / "README.md").write_text(readme_content)

    console.print()
    console.print(
        Panel.fit(
            f"[bold green]✅ Project '{name}' created successfully![/bold green]",
            border_style="green",
        )
    )
    console.print()
    console.print("[bold cyan]Next steps:[/bold cyan]")
    console.print(f"  1. [yellow]cd {directory}[/yellow]")
    console.print("  2. Review and update .env file if needed")
    console.print("  3. Start with Docker: [yellow]docker-compose up -d[/yellow]")
    console.print(f"     Or run locally: [yellow]uvicorn {package_name}.main:app --reload[/yellow]")


def main() -> None:
    """Main entry point for rs command."""
    app()


if __name__ == "__main__":
    main()
