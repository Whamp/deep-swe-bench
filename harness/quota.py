"""Host-side provider quota checking for transient-limit auto-resume.

When a benchmark cell hits a subscription usage-limit error (e.g. the OpenAI
Codex 5h or weekly window exhausting), the harness pauses the batch. This
module queries the provider's usage API to find (a) which window is exhausted
and (b) when it resets, so ``run_batch`` can sleep until the reset and resume
automatically instead of requiring a manual command re-run.

Supports direct ZAI Coding Plan models through ZAI's subscription usage endpoint
and OpenAI Codex subscription models through the same endpoint and credential
path as ``@marckrenn/pi-sub-core``'s ``CodexProvider``.

ZAI uses ``GET https://api.z.ai/api/monitor/usage/quota/limit`` with
``ZAI_API_KEY``. OpenAI Codex uses:

    GET https://chatgpt.com/backend-api/wham/usage
    Authorization: Bearer <access>   (from ~/.pi/agent/auth.json["openai-codex"].access)
    ChatGPT-Account-Id: <accountId>  (from ~/.pi/agent/auth.json["openai-codex"].accountId)

The raw response shape is::

    {
      "rate_limit": {
        "primary_window":   {"reset_at": <unix s>, "limit_window_seconds": 18000, "used_percent": 100},
        "secondary_window": {"reset_at": <unix s>, "limit_window_seconds": 604800, "used_percent": 58}
      },
      "additional_rate_limits": [
        {"limit_name": "GPT-5.3-Codex-Spark", "rate_limit": {"primary_window": {...}, "secondary_window": {...}}}
      ]
    }
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

CODEX_USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"
ZAI_USAGE_URL = "https://api.z.ai/api/monitor/usage/quota/limit"
DEFAULT_AUTH_PATH = Path.home() / ".pi" / "agent" / "auth.json"
DEFAULT_SUBCORE_CACHE = Path.home() / ".pi" / "agent" / "cache" / "sub-core" / "cache.json"

# A window is "exhausted" (blocking further runs) at this used-percent threshold.
# A small margin below 100 catches windows reported at 99-100% that still reject calls.
EXHAUSTED_THRESHOLD = 95
HTTP_TIMEOUT_S = 10

# Markers that distinguish a transient error as a subscription *quota* exhaustion
# (wait for the window to reset, which may be hours/days) vs a short rate-limit
# (retry after a brief backoff) vs an unknown transient (manual resume).
SUBSCRIPTION_QUOTA_MARKERS = ("usage limit", "weekly limit", "weekly usage", "plan limit", "plan_limit")
RATE_LIMIT_MARKERS = ("rate limit", "too many requests", "temporarily rate limited")
RATE_LIMIT_REGEXES = (
    re.compile(r"(?:http\s*)?(?:status\s*)?(?:error\s*)?\b429\b", re.I),
)

# Substring that marks the separate GPT-5.3-Codex-Spark quota pool.
SPARK_MARKER = "spark"


@dataclass(frozen=True)
class Window:
    """One provider usage window (e.g. the Codex 5h or weekly window)."""

    label: str
    used_percent: float
    reset_at: datetime | None

    @property
    def is_spark(self) -> bool:
        return SPARK_MARKER in self.label.lower()

    @property
    def is_exhausted(self) -> bool:
        return self.used_percent >= EXHAUSTED_THRESHOLD


# --------------------------------------------------------------------------- #
# Pure parsing
# --------------------------------------------------------------------------- #


def _window_label(limit_window_seconds: float | None, fallback_seconds: float) -> str:
    s = (
        limit_window_seconds
        if isinstance(limit_window_seconds, (int, float)) and limit_window_seconds > 0
        else fallback_seconds
    )
    if not s or s <= 0:
        return "0h"
    hours = round(s / 3600)
    if hours >= 144:
        return "Week"
    if hours >= 24:
        return "Day"
    return f"{hours}h"


def _push_window(
    windows: list[Window],
    win: dict | None,
    fallback_seconds: float,
    prefix: str | None = None,
) -> None:
    if not win:
        return
    reset_at: datetime | None = None
    ra = win.get("reset_at")
    if isinstance(ra, (int, float)) and ra > 0:
        reset_at = datetime.fromtimestamp(ra, tz=timezone.utc)
    label = _window_label(win.get("limit_window_seconds"), fallback_seconds)
    if prefix:
        label = f"{prefix} {label}"
    windows.append(Window(label=label, used_percent=float(win.get("used_percent") or 0), reset_at=reset_at))


def _add_rate(windows: list[Window], rate: dict | None, prefix: str | None = None) -> None:
    if not rate:
        return
    _push_window(windows, rate.get("primary_window"), 18000, prefix)
    _push_window(windows, rate.get("secondary_window"), 604800, prefix)


def _zai_window_label(number: object, unit: object) -> str:
    """Name the ZAI Coding Plan duration units used by its quota endpoint."""
    count = number if isinstance(number, int | float) else 0
    if unit == 3:
        return f"{count:g}h"
    if unit == 4:
        return "Day" if count == 1 else f"{count:g} days"
    if unit == 5:
        return "Month" if count == 1 else f"{count:g} months"
    if unit == 6:
        return "Week" if count == 1 else f"{count:g} weeks"
    return f"ZAI unit {unit}"


def parse_zai_usage(data: dict) -> list[Window]:
    """Parse ZAI Coding Plan token windows without retaining account content."""
    payload = data.get("data")
    if not isinstance(payload, dict):
        return []
    windows: list[Window] = []
    for limit in payload.get("limits") or []:
        if not isinstance(limit, dict) or limit.get("type") != "TOKENS_LIMIT":
            continue
        percentage = limit.get("percentage")
        if not isinstance(percentage, int | float):
            continue
        reset_at: datetime | None = None
        reset_ms = limit.get("nextResetTime")
        if isinstance(reset_ms, int | float) and reset_ms > 0:
            reset_at = datetime.fromtimestamp(reset_ms / 1000, tz=timezone.utc)
        windows.append(
            Window(
                label=_zai_window_label(limit.get("number"), limit.get("unit")),
                used_percent=float(percentage),
                reset_at=reset_at,
            )
        )
    return windows


def parse_codex_usage(data: dict) -> list[Window]:
    """Parse a raw ``wham/usage`` response into Window objects.

    Mirrors ``CodexProvider.fetchUsage`` in ``@marckrenn/pi-sub-core``: the top
    ``rate_limit`` holds the main Codex Plan windows, and ``additional_rate_limits``
    holds the separate GPT-5.3-Codex-Spark pool (or any other metered feature).
    """
    windows: list[Window] = []
    _add_rate(windows, data.get("rate_limit"))
    for entry in data.get("additional_rate_limits") or []:
        if not isinstance(entry, dict):
            continue
        prefix = (
            str(entry.get("limit_name") or entry.get("metered_feature") or "Additional").strip()
        )
        _add_rate(windows, entry.get("rate_limit"), prefix=prefix)
    return windows


def relevant_windows(windows: list[Window], model: str) -> list[Window]:
    """Filter to the windows that govern ``model``.

    GPT-5.3-Codex-Spark draws from its own separate pool; every other
    ``openai-codex/*`` model draws from the main Codex Plan pool.
    """
    is_spark_model = SPARK_MARKER in model.lower()
    if is_spark_model:
        return [w for w in windows if w.is_spark]
    return [w for w in windows if not w.is_spark]


def exhausted_windows(windows: list[Window]) -> list[Window]:
    """Windows currently at or above the exhaustion threshold."""
    return [w for w in windows if w.is_exhausted]


def next_reset(windows: list[Window]) -> datetime | None:
    """The moment we must wait until: the latest reset among exhausted windows.

    Returns ``None`` when no window is exhausted (nothing to wait for). If some
    exhausted windows lack a ``reset_at``, they are skipped but a result is still
    returned from the ones that do carry a reset time; if none carry one, ``None``
    is returned so the caller can fall back to a fixed poll interval.
    """
    resets = [w.reset_at for w in exhausted_windows(windows) if w.reset_at is not None]
    return max(resets) if resets else None


def wait_seconds(reset_at: datetime | None, *, now: datetime, buffer_s: int = 60) -> int | None:
    """Whole seconds to sleep until ``reset_at`` plus a safety buffer.

    Returns ``None`` when ``reset_at`` is ``None`` (unknown reset). A non-negative
    integer otherwise (0 if the reset is already in the past).
    """
    if reset_at is None:
        return None
    delta = (reset_at - now).total_seconds() + buffer_s
    return max(0, int(delta))


def classify_transient(transient_msg: str | None) -> str:
    """Classify a transient-error message as quota / rate_limit / unknown."""
    if not transient_msg:
        return "unknown"
    low = transient_msg.lower()
    if any(m in low for m in SUBSCRIPTION_QUOTA_MARKERS):
        return "quota"
    if any(m in low for m in RATE_LIMIT_MARKERS) or any(r.search(transient_msg) for r in RATE_LIMIT_REGEXES):
        return "rate_limit"
    return "unknown"


# --------------------------------------------------------------------------- #
# Credential + network I/O
# --------------------------------------------------------------------------- #


def load_codex_credentials(auth_path: Path = DEFAULT_AUTH_PATH) -> dict | None:
    """Read the OpenAI Codex OAuth token from ``~/.pi/agent/auth.json``."""
    if not auth_path.exists():
        return None
    try:
        data = json.loads(auth_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    entry = data.get("openai-codex")
    if not isinstance(entry, dict) or not entry.get("access"):
        return None
    return {"access_token": entry["access"], "account_id": entry.get("accountId")}


def fetch_zai_usage(
    api_key: str,
    *,
    url: str = ZAI_USAGE_URL,
    timeout: float = HTTP_TIMEOUT_S,
) -> dict:
    """Call the ZAI Coding Plan quota endpoint and return parsed JSON."""
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(
        request,
        timeout=timeout,
    ) as response:
        return json.loads(response.read())


def zai_windows(
    *,
    api_key: str | None = None,
    fetcher=fetch_zai_usage,
) -> tuple[list[Window], str]:
    """Return ZAI Coding Plan token quota windows from the live usage API."""
    credential = api_key or os.environ.get("ZAI_API_KEY")
    if not credential:
        return [], "none"
    try:
        return parse_zai_usage(fetcher(credential)), "zai-api"
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        return [], "none"


def fetch_codex_usage(
    access_token: str,
    account_id: str | None = None,
    *,
    url: str = CODEX_USAGE_URL,
    timeout: float = HTTP_TIMEOUT_S,
) -> dict:
    """Call the Codex ``wham/usage`` endpoint and return the parsed JSON."""
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    if account_id:
        headers["ChatGPT-Account-Id"] = account_id
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (trusted https endpoint)
        return json.loads(resp.read())


def read_subcore_cache(cache_path: Path = DEFAULT_SUBCORE_CACHE) -> list[Window] | None:
    """Read the parsed windows from the pi-sub-core cache (fallback data source).

    The cache stores already-parsed windows under ``<provider_key>.usage.windows``
    with ``label`` / ``usedPercent`` / ``resetAt`` (ISO 8601) fields. Returns the
    Codex entry's windows, or ``None`` if the cache is absent / unreadable.
    """
    if not cache_path.exists():
        return None
    try:
        cache = json.loads(cache_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    entry = cache.get("codex")
    if not isinstance(entry, dict):
        return None
    windows: list[Window] = []
    for w in entry.get("usage", {}).get("windows", []) or []:
        reset_at: datetime | None = None
        ra = w.get("resetAt")
        if isinstance(ra, str) and ra:
            try:
                reset_at = datetime.fromisoformat(ra.replace("Z", "+00:00"))
            except ValueError:
                reset_at = None
        windows.append(
            Window(
                label=str(w.get("label", "?")),
                used_percent=float(w.get("usedPercent", 0)),
                reset_at=reset_at,
            )
        )
    return windows


def codex_windows(
    model: str,
    *,
    auth_path: Path = DEFAULT_AUTH_PATH,
    cache_path: Path = DEFAULT_SUBCORE_CACHE,
    fetcher=fetch_codex_usage,
) -> tuple[list[Window], str]:
    """Return ``(relevant_windows, source)`` for ``model``.

    Tries the live Codex usage API first (source ``"api"``), then falls back to
    the pi-sub-core cache (source ``"cache"``). If neither is available, returns
    an empty list with source ``"none"``.
    """
    creds = load_codex_credentials(auth_path)
    if creds:
        try:
            data = fetcher(creds["access_token"], creds.get("account_id"))
            return relevant_windows(parse_codex_usage(data), model), "api"
        except (urllib.error.URLError, OSError, ValueError, KeyError):
            pass
    cached = read_subcore_cache(cache_path)
    if cached:
        return relevant_windows(cached, model), "cache"
    return [], "none"


def provider_windows(model: str) -> tuple[list[Window], str]:
    """Query the subscription quota source selected by the model provider."""
    if model.startswith("zai/"):
        return zai_windows()
    if model.startswith("openai-codex/"):
        return codex_windows(model)
    return [], "unsupported-provider"


def describe_pause(windows: list[Window], *, now: datetime) -> str:
    """Human-readable one-liner for a quota pause, naming the exhausted windows."""
    ex = exhausted_windows(windows)
    parts = []
    for w in ex:
        eta = ""
        if w.reset_at:
            mins = max(0, int((w.reset_at - now).total_seconds() // 60))
            if mins >= 60:
                eta = f" resets in {mins // 60}h{mins % 60}m"
            else:
                eta = f" resets in {mins}m"
        parts.append(f"{w.label} @ {w.used_percent:.0f}%{eta}")
    return "; ".join(parts) if parts else "quota limit"
