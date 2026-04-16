from __future__ import annotations

import socket
import webbrowser
from urllib.parse import urlencode

import httpx

from dex_cli.config import AccountConfig, CognitoConfig, get_account
from dex_cli.services.aws_access_manager import token_cache
from dex_cli.services.aws_access_manager.callback import wait_for_callback
from dex_cli.services.aws_access_manager.models import TokenSet
from dex_cli.utils.pkce import pkce_challenge

CALLBACK_PORT_RANGE = range(8400, 8411)
CALLBACK_PATH = "/callback"


def _find_available_port() -> int:
  """Return the first available port in the callback range."""
  for port in CALLBACK_PORT_RANGE:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
      if sock.connect_ex(("localhost", port)) != 0:
        return port
  raise RuntimeError(
    f"No available port in {CALLBACK_PORT_RANGE.start}–{CALLBACK_PORT_RANGE.stop - 1}"
  )


class AuthService:
  """Handles the full Cognito OAuth2 PKCE flow."""

  def fetch_cognito_config(self, account: AccountConfig) -> CognitoConfig:
    """Fetch remote Cognito configuration from the account's config URL."""
    response = httpx.get(account.config_url, timeout=10)
    response.raise_for_status()
    data = response.json()
    return CognitoConfig(
      client_id=data["clientId"],
      cognito_domain=data["cognitoDomain"],
      user_pool_id=data["userPoolId"],
    )

  def login(self, alias: str, *, force: bool = False) -> tuple[TokenSet, bool]:
    """Return tokens for the given account, using cache when possible.

    Args:
      alias: Account alias to authenticate.
      force: Skip the cache and always do a fresh browser login.

    Returns:
      ``(tokens, from_cache)`` — the token set and whether it was loaded
      from cache (``True``) or freshly obtained (``False``).
    """
    if not force:
      cached = token_cache.load(alias)
      if cached is not None:
        return cached, True

    account = get_account(alias)
    cognito = self.fetch_cognito_config(account)
    verifier, challenge = pkce_challenge()
    port = _find_available_port()
    redirect_uri = f"http://localhost:{port}{CALLBACK_PATH}"

    authorize_url = self._build_authorize_url(cognito, challenge, redirect_uri)
    webbrowser.open(authorize_url)

    code = wait_for_callback(port)
    tokens = self._exchange_code(cognito, code, verifier, redirect_uri)
    token_cache.save(alias, tokens)
    return tokens, False

  def logout(self, alias: str) -> None:
    """Clear cached tokens for the given account."""
    token_cache.clear(alias)

  def _build_authorize_url(
    self,
    cognito: CognitoConfig,
    code_challenge: str,
    redirect_uri: str,
  ) -> str:
    base = f"https://{cognito.cognito_domain}/oauth2/authorize"
    params = urlencode({
      "response_type": "code",
      "client_id": cognito.client_id,
      "redirect_uri": redirect_uri,
      "scope": "openid profile email",
      "code_challenge_method": "S256",
      "code_challenge": code_challenge,
    })
    return f"{base}?{params}"

  def _exchange_code(
    self,
    cognito: CognitoConfig,
    code: str,
    verifier: str,
    redirect_uri: str,
  ) -> TokenSet:
    """Exchange the authorization code for tokens via Cognito's token endpoint."""
    token_url = f"https://{cognito.cognito_domain}/oauth2/token"
    response = httpx.post(
      token_url,
      data={
        "grant_type": "authorization_code",
        "client_id": cognito.client_id,
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": verifier,
      },
      headers={"Content-Type": "application/x-www-form-urlencoded"},
      timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return TokenSet(
      access_token=data["access_token"],
      id_token=data["id_token"],
      refresh_token=data["refresh_token"],
      token_type=data["token_type"],
      expires_in=data["expires_in"],
    )
