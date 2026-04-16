from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class TimeLeftConfig:
  days: bool = True
  hours: bool = True
  minutes: bool = False


DEFAULT_CONFIG = TimeLeftConfig()


def time_left(iso_timestamp: str, config: TimeLeftConfig = DEFAULT_CONFIG) -> str:
  """Human-readable time remaining until an ISO 8601 timestamp.

  Enabled units are shown from the highest enabled down to the lowest
  consecutive enabled unit. A disabled unit in between stops output,
  so ``days=True, hours=False, minutes=True`` shows only days.

  Returns ``"expired"`` when the timestamp is in the past, or an empty
  string if the input is empty or unparseable.
  """
  if not iso_timestamp:
    return ""
  try:
    target = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    total = int((target - datetime.now(timezone.utc)).total_seconds())
    if total <= 0:
      return "expired"
  except ValueError:
    return ""

  units: list[tuple[bool, str, int]] = [
    (config.days, "d", 86400),
    (config.hours, "h", 3600),
    (config.minutes, "m", 60),
  ]

  parts: list[str] = []
  remainder = total
  started = False

  for enabled, suffix, divisor in units:
    if not enabled:
      if started:
        break
      continue
    started = True
    value, remainder = divmod(remainder, divisor)
    if value:
      parts.append(f"{value}{suffix}")

  return " ".join(parts) or "< 1m"
