"""Lightweight local HTTP server that captures the OAuth2 authorization code."""

from __future__ import annotations

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

SUCCESS_HTML = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Authenticated</title></head>
<body style="font-family:system-ui;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;background:#0d1117;color:#c9d1d9">
  <div style="text-align:center">
    <h1 style="color:#3fb950">&#10003; Authenticated</h1>
    <p>You can close this tab and return to the terminal.</p>
  </div>
</body>
</html>
"""

ERROR_HTML = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Authentication Failed</title></head>
<body style="font-family:system-ui;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;background:#0d1117;color:#c9d1d9">
  <div style="text-align:center">
    <h1 style="color:#f85149">&#10007; Authentication Failed</h1>
    <p>{error}</p>
  </div>
</body>
</html>
"""


class _CallbackHandler(BaseHTTPRequestHandler):
  """Handles a single GET to the callback path and extracts the code."""

  auth_code: str | None = None
  error: str | None = None

  def do_GET(self) -> None:
    qs = parse_qs(urlparse(self.path).query)

    if "error" in qs:
      _CallbackHandler.error = qs["error"][0]
      self._respond(400, ERROR_HTML.format(error=_CallbackHandler.error))
    elif "code" in qs:
      _CallbackHandler.auth_code = qs["code"][0]
      self._respond(200, SUCCESS_HTML)
    else:
      _CallbackHandler.error = "No authorization code in callback"
      self._respond(400, ERROR_HTML.format(error=_CallbackHandler.error))

  def _respond(self, status: int, body: str) -> None:
    self.send_response(status)
    self.send_header("Content-Type", "text/html; charset=utf-8")
    self.end_headers()
    self.wfile.write(body.encode())

  def log_message(self, format: str, *args: object) -> None:  # noqa: A002
    pass


def wait_for_callback(port: int, timeout: float = 120) -> str:
  """Start a local server and block until the OAuth2 callback arrives.

  Args:
    port: The port to listen on.
    timeout: Max seconds to wait before raising.

  Returns:
    The authorization code from the callback.

  Raises:
    TimeoutError: If no callback is received within *timeout* seconds.
    RuntimeError: If the callback contained an error or no code.
  """
  _CallbackHandler.auth_code = None
  _CallbackHandler.error = None

  server = HTTPServer(("localhost", port), _CallbackHandler)
  server.timeout = timeout

  thread = threading.Thread(target=server.handle_request, daemon=True)
  thread.start()
  thread.join(timeout=timeout)

  server.server_close()

  if _CallbackHandler.error:
    raise RuntimeError(f"OAuth2 callback error: {_CallbackHandler.error}")
  if _CallbackHandler.auth_code is None:
    raise TimeoutError("Timed out waiting for OAuth2 callback")
  return _CallbackHandler.auth_code
