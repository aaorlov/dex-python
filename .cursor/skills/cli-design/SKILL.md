---
name: cli-design
description: >-
  Design and scaffold CLI tools and AI agent systems using Python and uv.
  Use when building CLI applications, terminal tools, interactive prompts,
  agent-powered CLIs, MCP servers, or distributing Python packages.
---

# CLI & Agent Architect — Python 2026

Design and scaffold high-performance CLI tools using Python 3.13+,
prioritizing modularity for AI agent integration, interactive UIs,
and platform-agnostic business logic.

## Execution Environment

- **Runtime:** Python >= 3.13 (3.14t for free-threaded workloads)
- **Package Manager:** `uv` (>= 0.7) — replaces pip, poetry, pyenv, pipx
- **Project Config:** `pyproject.toml` (PEP 621)
- **Linting & Formatting:** `ruff` — replaces flake8, isort, black
- **Type Checking:** `pyright` (strict mode)
- **Distribution:** PyPI via `uv publish`, `shiv` (zipapp), or `PyInstaller`/`Nuitka` for single binary

---

## Package Stack

| Category | Package | Purpose |
| :--- | :--- | :--- |
| **Command Parsing** | `typer` >= 0.24 | Type-hint-driven CLI, subcommands, auto-help, shell completion |
| **Rich Output** | `rich` >= 14 | Colors, tables, panels, trees, progress bars, markdown rendering |
| **Interactivity** | `questionary` | Text, select, confirm, checkbox, autocomplete prompts |
| **TUI** | `textual` >= 8 | Component-driven terminal UIs, CSS styling, async, web export |
| **Validation** | `pydantic` >= 2.10 | Type-safe models, settings, serialization |
| **HTTP Client** | `httpx` | Async/sync HTTP, streaming, HTTP/2 support |
| **Shell** | `subprocess` / `asyncio` | Built-in process execution |
| **Local State / DB** | `sqlmodel` >= 0.0.22 | Pydantic + SQLAlchemy unified models — local SQLite or Postgres |
| **Config** | `pydantic-settings` >= 2.8 | Env vars, `.env` files, TOML/YAML config with type-safe validation |
| **Agent Framework** | `pydantic-ai` >= 1.78 | Type-safe AI agents, tool calling, streaming, MCP integration |
| **Tool Protocol** | `mcp` >= 1.27 | MCP server/client, stdio & Streamable HTTP transports |
| **Testing** | `pytest` + `pytest-asyncio` | Fixtures, parametrize, async tests, coverage via `pytest-cov` |

---

## Folder Structure

### Standard CLI

```text
my-cli/
├── src/
│   └── my_cli/
│       ├── __init__.py
│       ├── __main__.py          # Entry: `python -m my_cli`
│       ├── cli.py               # Typer app definition + global opts
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── init.py
│       │   ├── deploy.py
│       │   └── status.py
│       ├── services/            # Business logic, API clients
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   └── api.py
│       └── utils/               # Shared helpers, config loading
│           ├── __init__.py
│           └── config.py
├── tests/
│   ├── conftest.py
│   ├── test_deploy.py
│   └── test_status.py
├── pyproject.toml
├── uv.lock
└── README.md
```

### Agent System (Monorepo with uv Workspaces)

```text
my-agent-system/
├── packages/
│   ├── agent-core/              # Platform-agnostic agent logic
│   │   ├── src/agent_core/
│   │   │   ├── agent.py         # pydantic-ai Agent definition
│   │   │   ├── tools.py         # Tool functions
│   │   │   ├── models.py        # Pydantic state/result models
│   │   │   └── __init__.py
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   ├── mcp-server/              # MCP tool server
│   │   ├── src/mcp_server/
│   │   │   ├── tools/           # Tool handler implementations
│   │   │   └── server.py        # FastMCP server bootstrap
│   │   └── pyproject.toml
│   │
│   ├── client-cli/              # CLI client
│   │   ├── src/client_cli/
│   │   │   ├── cli.py           # Typer app & global config
│   │   │   ├── commands/        # Command handlers (chat, login, status)
│   │   │   ├── services/        # External integrations
│   │   │   └── utils/
│   │   └── pyproject.toml
│   │
│   └── client-web/              # Web client (optional)
│       ├── src/client_web/
│       └── pyproject.toml
│
├── pyproject.toml               # Root workspace
├── uv.lock
└── AGENTS.md                    # Agent architecture rules
```

---

## Entry Point

```python
# src/my_cli/cli.py
import typer
from rich.console import Console

from my_cli.commands import deploy, init, status

app = typer.Typer(
    name="mytool",
    help="My CLI tool",
    no_args_is_help=True,
)
app.add_typer(deploy.app, name="deploy")
app.add_typer(init.app, name="init")
app.add_typer(status.app, name="status")

console = Console()

@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")):
    """Global options applied before any subcommand."""
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
```

```python
# src/my_cli/__main__.py
from my_cli.cli import app

app()
```

---

## Examples

### 1. Request-Response Command

Standard command with options, confirmation prompt, spinner, and shell execution.

```python
# src/my_cli/commands/deploy.py
import subprocess
import typer
from rich.console import Console
from rich.prompt import Confirm

app = typer.Typer(help="Deploy to target environment")
console = Console()

@app.callback(invoke_without_command=True)
def deploy(
    target: str = typer.Argument(..., help="Deployment target"),
    env: str = typer.Option("production", "--env", "-e", help="Environment"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate deployment"),
):
    console.rule(f"[bold blue]Deploy: {target}[/]")

    if env == "production":
        if not Confirm.ask("[yellow]Deploy to production?[/]"):
            console.print("[yellow]Cancelled.[/]")
            raise typer.Exit()

    with console.status(f"Deploying {target} to {env}..."):
        if dry_run:
            console.print("[green]Dry run complete. No changes applied.[/]")
            raise typer.Exit()

        subprocess.run(
            ["kubectl", "apply", "-f", f"deploy/{target}.yaml"],
            check=True,
        )

    console.print("[bold green]Deployed successfully.[/]")
```

### 2. Service Layer with Shell Execution

Business logic separated from command handlers.

```python
# src/my_cli/services/aws.py
import json
import subprocess


class AwsService:
    @staticmethod
    def sso_login(profile: str) -> None:
        subprocess.run(["aws", "sso", "login", "--profile", profile], check=True)

    @staticmethod
    def whoami(profile: str) -> dict:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity", "--profile", profile],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
```

```python
# src/my_cli/commands/login.py
import typer
from rich.console import Console

from my_cli.services.aws import AwsService

app = typer.Typer(help="Authentication commands")
console = Console()

@app.callback(invoke_without_command=True)
def login(
    profile: str = typer.Option("default", "--profile", "-p", help="AWS profile name"),
):
    console.rule(f"[bold yellow]AWS SSO: {profile}[/]")

    with console.status(f"Initiating login for profile: {profile}"):
        try:
            AwsService.sso_login(profile)
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/]")
            raise typer.Exit(code=1)

    console.print("[bold green]Successfully authenticated.[/]")
```

### 3. Interactive Wizard (Multi-Step Prompts)

```python
# src/my_cli/commands/init.py
import subprocess
from pathlib import Path

import questionary
import typer
from rich.console import Console

app = typer.Typer(help="Initialize a new project")
console = Console()

@app.callback(invoke_without_command=True)
def init():
    console.rule("[bold magenta]New Project[/]")

    name = questionary.text(
        "Project name:",
        default="my-project",
        validate=lambda v: True if len(v) >= 1 else "Required",
    ).ask()

    template = questionary.select(
        "Template:",
        choices=[
            questionary.Choice("Minimal", value="minimal"),
            questionary.Choice("Full (with tests and linting)", value="full"),
            questionary.Choice("Agent (AI agent monorepo)", value="agent"),
        ],
    ).ask()

    features = questionary.checkbox(
        "Features:",
        choices=["Type checking (pyright)", "Linting (ruff)", "Testing (pytest)", "CI/CD (GitHub Actions)"],
    ).ask()

    use_git = questionary.confirm("Initialize git?", default=True).ask()

    with console.status("Scaffolding project..."):
        base = Path(name)
        (base / "src" / name.replace("-", "_") / "commands").mkdir(parents=True)
        (base / "src" / name.replace("-", "_") / "services").mkdir(parents=True)
        (base / "tests").mkdir(parents=True)

        if use_git:
            subprocess.run(["git", "init", str(base)], check=True, capture_output=True)

    console.print(f"[bold green]cd {name} && uv sync[/]")
```

### 4. Interactive Agent Chat with Streaming

Persistent conversation with real-time Rich.Live streaming — the official pydantic-ai pattern.

```python
# src/my_cli/commands/chat.py
import asyncio

import typer
from pydantic_ai import Agent
from rich.console import Console, ConsoleOptions, RenderResult
from rich.live import Live
from rich.markdown import CodeBlock, Markdown
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.text import Text

app = typer.Typer(help="AI chat commands")
console = Console()


def _prettier_code_blocks():
    """Nicer code blocks with language labels and syntax highlighting."""

    class SimpleCodeBlock(CodeBlock):
        def __rich_console__(
            self, console: Console, options: ConsoleOptions
        ) -> RenderResult:
            code = str(self.text).rstrip()
            yield Text(self.lexer_name, style="dim")
            yield Syntax(code, self.lexer_name, theme=self.theme, background_color="default", word_wrap=True)
            yield Text(f"/{self.lexer_name}", style="dim")

    Markdown.elements["fence"] = SimpleCodeBlock


async def _chat_loop(model: str):
    _prettier_code_blocks()
    agent = Agent(model, system_prompt="You are a helpful assistant.")
    console.rule("[bold cyan]Agent Session[/]")
    console.print("[dim]Type 'exit' to quit.[/]\n")

    message_history = []

    while True:
        user_input = Prompt.ask("[bold]You[/]")
        if not user_input or user_input.strip() == "exit":
            break

        # TTFT spinner — visible until the first token arrives
        status = console.status("Thinking...")
        status.start()
        first_token = True

        with Live(Markdown(""), console=console, vertical_overflow="visible") as live:
            async with agent.run_stream(
                user_input,
                message_history=message_history,
            ) as result:
                async for message in result.stream_output():
                    if first_token:
                        status.stop()
                        first_token = False
                    live.update(Markdown(message))

        console.print()
        message_history = result.all_messages()

    console.print("[dim]Session closed.[/]")


@app.callback(invoke_without_command=True)
def chat(
    model: str = typer.Option(
        "anthropic:claude-sonnet-4-20250514", "--model", "-m", help="Model ID"
    ),
):
    asyncio.run(_chat_loop(model))
```

### 5. MCP Server

```python
# packages/mcp-server/src/mcp_server/server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-tools")


@mcp.tool()
def search(query: str) -> str:
    """Search the knowledge base."""
    return f"Results for: {query}"


@mcp.tool()
def run_query(sql: str, database: str = "main") -> str:
    """Execute a database query."""
    return f"Executed on {database}: {sql}"


if __name__ == "__main__":
    mcp.run()
```

### 6. Local State with SQLModel

Persistent local storage for auth tokens, agent history, and config.
Same model pattern as production DB — Pydantic validation everywhere, no raw SQL strings.

```python
# src/my_cli/services/store.py
from datetime import datetime
from pathlib import Path

from sqlmodel import Field, Session, SQLModel, create_engine, select

CONFIG_DIR = Path.home() / ".config" / "mytool"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{CONFIG_DIR / 'state.db'}", connect_args={"check_same_thread": False})


class KV(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.now)


SQLModel.metadata.create_all(engine)


class Store:
    @staticmethod
    def get(key: str) -> str | None:
        with Session(engine) as session:
            row = session.get(KV, key)
            return row.value if row else None

    @staticmethod
    def set(key: str, value: str) -> None:
        with Session(engine) as session:
            session.merge(KV(key=key, value=value))
            session.commit()

    @staticmethod
    def append_message(role: str, content: str) -> None:
        with Session(engine) as session:
            session.add(Message(role=role, content=content))
            session.commit()

    @staticmethod
    def get_history(limit: int = 50) -> list[Message]:
        with Session(engine) as session:
            return list(session.exec(
                select(Message).order_by(Message.id.desc()).limit(limit)
            ))
```

### 7. Configuration with pydantic-settings

Type-safe config from env vars, `.env` files, and defaults — no manual `os.getenv()`.

```python
# src/my_cli/utils/config.py
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MYTOOL_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    anthropic_api_key: SecretStr
    default_model: str = "anthropic:claude-sonnet-4-20250514"
    database_url: str = "sqlite:///mytool.db"
    verbose: bool = False
    max_history: int = 50


settings = Settings()
```

---

## Build & Distribution

```bash
# Development
uv run python -m my_cli

# Dev with arguments
uv run python -m my_cli deploy staging --dry-run

# Run directly via script entry point
uv run mytool deploy staging --dry-run

# Install as a tool (global, isolated env)
uv tool install .

# Run without installing (like npx)
uvx mytool deploy staging

# Publish to PyPI
uv build && uv publish

# Zipapp (single .pyz file, requires Python on target)
uv run shiv -c mytool -o dist/mytool.pyz .

# Single binary (PyInstaller)
uv run pyinstaller --onefile --name mytool src/my_cli/__main__.py

# Single binary (Nuitka — better performance)
uv run nuitka --standalone --onefile --output-filename=mytool src/my_cli/__main__.py
```

---

## Additional Resources

- LangGraph agent orchestration and Textual TUI streaming chat: [examples-advanced.md](examples-advanced.md)
- `pyproject.toml` variants, ruff/pyright config, cross-platform build: [config-templates.md](config-templates.md)

---

## Best Practices

- One command module per file in `commands/`, registered via `app.add_typer()`
- Business logic in `services/`, never in command handlers
- Use `questionary` for multi-step interactive flows (text, select, confirm, checkbox)
- Use `rich` for all styled output — colors, tables, panels, spinners, markdown
- Use `subprocess.run()` for shell commands — explicit, safe, no shell injection, cross-platform
- Use `SQLModel` for all persistent state — local SQLite and production DB, same model pattern everywhere
- Use `pydantic-settings` for configuration — env vars, `.env` files, TOML with `SecretStr` for keys
- Use `pydantic` models for all data validation and API responses
- Use `textual` only when you need a stateful component-driven TUI (dashboards, live streams)
- Use `Rich.Live` + `Markdown` for real-time AI streaming — the official pydantic-ai pattern
- Agent logic (pydantic-ai) lives in `agent-core/`, CLI just invokes it
- MCP tools are a separate package — reusable across CLI, web, and other clients
- Always provide `--verbose` / `-v` global option for debugging
- Use prompts as fallback when CLI arguments are not provided
- Validate all inputs via Pydantic models
- Test with `pytest` — fixtures, parametrize, `pytest-asyncio` for async, `pytest-cov` for coverage
- Lint and format with `ruff` — single tool replaces flake8, isort, black
- Type check with `pyright` in strict mode
- Use `uv` for all dependency management — `uv add`, `uv sync`, `uv run`, `uv lock`
- Use `src/` layout (PEP 517) to prevent accidental imports from project root
- Target Python 3.13+ minimum; use 3.14t (free-threaded) for CPU-bound parallel workloads
