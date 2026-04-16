from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from rich.console import Console

CONFIG_DIR = Path.home() / ".config" / "dex"
ACCOUNTS_FILE = CONFIG_DIR / "accounts.json"


@dataclass(frozen=True, slots=True)
class AccountConfig:
  name: str
  alias: str
  api_url: str
  config_url: str
  cognito_domain: str


@dataclass(frozen=True, slots=True)
class CognitoConfig:
  """Remote Cognito configuration fetched from ``config_url``."""
  client_id: str
  cognito_domain: str
  user_pool_id: str


ACCOUNTS: dict[str, AccountConfig] = {}


def _load_accounts() -> None:
  """Load accounts from the config file on disk."""
  ACCOUNTS.clear()
  if not ACCOUNTS_FILE.exists():
    return
  data = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
  for entry in data:
    cfg = AccountConfig(**entry)
    ACCOUNTS[cfg.alias] = cfg


def _save_accounts() -> None:
  """Persist all accounts to the config file."""
  CONFIG_DIR.mkdir(parents=True, exist_ok=True)
  data = [asdict(cfg) for cfg in ACCOUNTS.values()]
  ACCOUNTS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def add_account(config: AccountConfig) -> None:
  """Add or update an account and persist to disk."""
  ACCOUNTS[config.alias] = config
  _save_accounts()


def remove_account(alias: str) -> None:
  """Remove an account by alias and persist to disk."""
  if alias not in ACCOUNTS:
    raise ValueError(f"Unknown account '{alias}'")
  del ACCOUNTS[alias]
  _save_accounts()


def get_account(alias: str) -> AccountConfig:
  if alias not in ACCOUNTS:
    console = Console(stderr=True)
    available = ", ".join(sorted(ACCOUNTS))
    if available:
      console.print(f"[red]Account '{alias}' not found.[/] Available: [bold]{available}[/]")
    else:
      console.print("[red]No accounts configured.[/] Run [bold]dex init[/] to get started.")
    sys.exit(1)
  return ACCOUNTS[alias]


_load_accounts()
