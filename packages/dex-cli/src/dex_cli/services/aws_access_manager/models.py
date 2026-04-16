from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TokenSet:
  access_token: str
  id_token: str
  refresh_token: str
  token_type: str
  expires_in: int
