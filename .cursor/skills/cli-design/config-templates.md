# Config Templates

## pyproject.toml — Standard CLI

```toml
[project]
name = "my-cli"
version = "1.0.0"
description = "My CLI tool"
requires-python = ">=3.13"
dependencies = [
    "typer>=0.24",
    "rich>=14",
    "questionary>=2.1",
    "sqlmodel>=0.0.22",
    "pydantic-settings>=2.8",
]

[project.scripts]
mycli = "my_cli.cli:app"

[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[tool.setuptools.package-dir]
"my_cli" = "src"

[tool.ruff]
target-version = "py313"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "RUF"]

[tool.ruff.lint.isort]
known-first-party = ["my_cli"]

[tool.pyright]
pythonVersion = "3.13"
typeCheckingMode = "strict"
venvPath = "."
venv = ".venv"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

## pyproject.toml — Agent CLI (with pydantic-ai)

```toml
[project]
name = "my-agent-cli"
version = "1.0.0"
description = "AI agent CLI tool"
requires-python = ">=3.13"
dependencies = [
    "typer>=0.24",
    "rich>=14",
    "questionary>=2.1",
    "pydantic-ai>=1.78",
    "pydantic>=2.10",
    "pydantic-settings>=2.8",
    "sqlmodel>=0.0.22",
    "httpx>=0.28",
]

[project.scripts]
myagent = "my_agent_cli.cli:app"

[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[tool.setuptools.package-dir]
"my_agent_cli" = "src"

[tool.ruff]
target-version = "py313"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "RUF"]

[tool.pyright]
pythonVersion = "3.13"
typeCheckingMode = "strict"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

## pyproject.toml — Agent CLI with LangGraph

```toml
[project]
name = "my-langgraph-cli"
version = "1.0.0"
description = "LangGraph agent CLI"
requires-python = ">=3.13"
dependencies = [
    "typer>=0.24",
    "rich>=14",
    "questionary>=2.1",
    "langgraph>=0.4",
    "langchain-anthropic>=0.4",
    "pydantic>=2.10",
]

[project.scripts]
myagent = "my_langgraph_cli.cli:app"

[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[tool.setuptools.package-dir]
"my_langgraph_cli" = "src"

[tool.ruff]
target-version = "py313"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "RUF"]

[tool.pyright]
pythonVersion = "3.13"
typeCheckingMode = "strict"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

## pyproject.toml — Agent CLI with Textual TUI

```toml
[project]
name = "my-tui-cli"
version = "1.0.0"
description = "Rich terminal UI agent"
requires-python = ">=3.13"
dependencies = [
    "typer>=0.24",
    "rich>=14",
    "questionary>=2.1",
    "pydantic-ai>=1.78",
    "pydantic>=2.10",
    "textual>=8.2",
]

[project.optional-dependencies]
dev = [
    "textual-dev>=1.7",
    "pytest>=8",
    "pytest-asyncio>=0.24",
    "pytest-cov>=6",
]

[project.scripts]
mytui = "my_tui_cli.cli:app"

[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[tool.setuptools.package-dir]
"my_tui_cli" = "src"

[tool.ruff]
target-version = "py313"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "RUF"]

[tool.pyright]
pythonVersion = "3.13"
typeCheckingMode = "strict"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

## pyproject.toml — MCP Server

```toml
[project]
name = "my-mcp-server"
version = "1.0.0"
description = "MCP tool server"
requires-python = ">=3.13"
dependencies = [
    "mcp>=1.27",
    "pydantic>=2.10",
]

[project.scripts]
my-mcp-server = "mcp_server.server:mcp.run"

[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[tool.setuptools.package-dir]
"mcp_server" = "src"

[tool.ruff]
target-version = "py313"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "RUF"]

[tool.pyright]
pythonVersion = "3.13"
typeCheckingMode = "strict"
```

## pyproject.toml — Monorepo Workspace Root

```toml
[project]
name = "my-agent-system"
version = "0.0.0"
description = "Agent system monorepo"
requires-python = ">=3.13"

[dependency-groups]
dev = [
    "ruff>=0.11",
    "pyright>=1.1",
    "pytest>=8",
    "pytest-asyncio>=0.24",
    "pytest-cov>=6",
]

[tool.uv.workspace]
members = ["packages/*"]

[tool.ruff]
target-version = "py313"
line-length = 100
src = ["packages/*/src"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "RUF"]

[tool.pyright]
pythonVersion = "3.13"
typeCheckingMode = "strict"

[tool.pytest.ini_options]
testpaths = ["packages/*/tests"]
asyncio_mode = "auto"
```

## Cross-Platform Build Script

```python
#!/usr/bin/env python3
# scripts/build.py
"""Build single-binary executables for multiple platforms using Nuitka."""
import platform
import subprocess
import sys
from pathlib import Path

NAME = "mycli"
ENTRY = "src/__main__.py"
DIST = Path("dist")
DIST.mkdir(exist_ok=True)

CURRENT_OS = platform.system().lower()
CURRENT_ARCH = platform.machine()


def build_pyinstaller() -> None:
    """Build with PyInstaller (simpler, wider platform support)."""
    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--name", f"{NAME}-{CURRENT_OS}-{CURRENT_ARCH}",
            "--distpath", str(DIST),
            "--clean",
            ENTRY,
        ],
        check=True,
    )


def build_nuitka() -> None:
    """Build with Nuitka (better performance, C compilation)."""
    suffix = ".exe" if CURRENT_OS == "windows" else ""
    outfile = f"{NAME}-{CURRENT_OS}-{CURRENT_ARCH}{suffix}"
    subprocess.run(
        [
            sys.executable, "-m", "nuitka",
            "--standalone",
            "--onefile",
            f"--output-filename={outfile}",
            f"--output-dir={DIST}",
            ENTRY,
        ],
        check=True,
    )


if __name__ == "__main__":
    builder = sys.argv[1] if len(sys.argv) > 1 else "pyinstaller"
    {"pyinstaller": build_pyinstaller, "nuitka": build_nuitka}[builder]()
    print(f"Build complete: {DIST}/")
```

## Ruff Configuration Reference

Commonly used ruff rule sets:

| Code | Category | Description |
| :--- | :--- | :--- |
| `E` | pycodestyle errors | Basic style errors |
| `F` | Pyflakes | Unused imports, undefined names |
| `W` | pycodestyle warnings | Whitespace, line continuation |
| `I` | isort | Import ordering |
| `UP` | pyupgrade | Modernize syntax for target Python version |
| `B` | flake8-bugbear | Likely bugs and design problems |
| `SIM` | flake8-simplify | Simplifiable constructs |
| `RUF` | Ruff-specific | Ruff's own rules |
| `ANN` | flake8-annotations | Missing type annotations |
| `PTH` | flake8-use-pathlib | Prefer pathlib over os.path |
| `ASYNC` | flake8-async | Async anti-patterns |
