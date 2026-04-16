import base64
import hashlib
import secrets


def pkce_challenge(verifier_length: int = 64) -> tuple[str, str]:
  """Generate a PKCE code verifier and its S256 challenge.

  Returns:
    A ``(code_verifier, code_challenge)`` tuple.
  """
  verifier = secrets.token_urlsafe(verifier_length)
  digest = hashlib.sha256(verifier.encode("ascii")).digest()
  challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
  return verifier, challenge
