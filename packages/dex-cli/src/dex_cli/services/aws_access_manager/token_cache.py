"""Persist and retrieve Cognito tokens on disk with expiry tracking."""

from __future__ import annotations

import json
import time
from pathlib import Path

from dex_cli.services.aws_access_manager.models import TokenSet

CACHE_DIR = Path.home() / ".config" / "dex" / "tokens"
EXPIRY_BUFFER_SECONDS = 60


def _cache_path(alias: str) -> Path:
  return CACHE_DIR / f"{alias}.json"


def save(alias: str, tokens: TokenSet) -> None:
  """Write tokens to disk with an ``expires_at`` timestamp."""
  CACHE_DIR.mkdir(parents=True, exist_ok=True)
  data = {
    "access_token": tokens.access_token,
    "id_token": tokens.id_token,
    "refresh_token": tokens.refresh_token,
    "token_type": tokens.token_type,
    "expires_in": tokens.expires_in,
    "expires_at": time.time() + tokens.expires_in,
  }
  _cache_path(alias).write_text(json.dumps(data), encoding="utf-8")


def load(alias: str) -> TokenSet | None:
  """Return cached tokens if they exist and haven't expired, else ``None``."""
  path = _cache_path(alias)
  if not path.exists():
    return None

  data = json.loads(path.read_text(encoding="utf-8"))
  expires_at = data.get("expires_at", 0)
  if time.time() >= expires_at - EXPIRY_BUFFER_SECONDS:
    path.unlink(missing_ok=True)
    return None

  return TokenSet(
    access_token=data["access_token"],
    id_token=data["id_token"],
    refresh_token=data["refresh_token"],
    token_type=data["token_type"],
    expires_in=data["expires_in"],
  )


def clear(alias: str) -> None:
  """Remove cached tokens for the given alias."""
  _cache_path(alias).unlink(missing_ok=True)
