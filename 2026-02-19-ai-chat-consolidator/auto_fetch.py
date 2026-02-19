"""
auto_fetch.py — Direct API fetchers for ChatGPT and Claude.ai.

Both services have internal REST APIs used by their own web apps.
This module authenticates using a session cookie the user copies from
their browser, then retrieves all conversations automatically.

No credentials are stored anywhere — tokens are used only in memory
for the duration of the script.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Callable, Optional

import requests

if TYPE_CHECKING:
    # Avoid circular import; consolidate imports us, we reference its types only in hints
    from consolidate import Conversation, Message

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# Delay between individual conversation-fetch requests (seconds).
# Keeps us well within any informal rate limits.
_FETCH_DELAY = 0.15


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_session(extra_headers: Optional[dict] = None) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": _UA, "Accept": "application/json"})
    if extra_headers:
        s.headers.update(extra_headers)
    return s


def _get_with_retry(
    session: requests.Session,
    url: str,
    *,
    params: Optional[dict] = None,
    timeout: int = 25,
    max_retries: int = 3,
) -> requests.Response:
    """
    GET with simple exponential backoff on 429 / 5xx.
    Raises on final failure.
    """
    delay = 2
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            r = session.get(url, params=params, timeout=timeout)
            if r.status_code == 429:
                retry_after = int(r.headers.get("Retry-After", delay))
                time.sleep(retry_after)
                delay *= 2
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
    raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ChatGPT fetcher
# ---------------------------------------------------------------------------

class ChatGPTFetcher:
    """
    Fetches all conversations from chat.openai.com / chatgpt.com.

    Auth flow:
      1. User provides their __Secure-next-auth.session-token cookie.
      2. We exchange it for a short-lived Bearer JWT via /api/auth/session.
      3. All subsequent calls use that JWT in the Authorization header.
    """

    _BASE = "https://chatgpt.com"

    def __init__(self, session_token: str) -> None:
        self._session = _make_session()
        self._authenticate(session_token)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _authenticate(self, session_token: str) -> None:
        try:
            r = self._session.get(
                f"{self._BASE}/api/auth/session",
                cookies={"__Secure-next-auth.session-token": session_token},
                timeout=25,
            )
            r.raise_for_status()
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code in (401, 403):
                raise AuthError(
                    "ChatGPT rejected the session token.\n"
                    "It may have expired — please copy a fresh one from your browser."
                ) from exc
            raise

        data = r.json()
        bearer = data.get("accessToken")
        if not bearer:
            raise AuthError(
                "Couldn't find an access token in the ChatGPT response.\n"
                "Your session token may be expired — please copy a fresh one."
            )

        self._session.headers["Authorization"] = f"Bearer {bearer}"
        # Also preserve cookie for subsequent calls (some endpoints check it)
        self._session.cookies.set(
            "__Secure-next-auth.session-token", session_token, domain="chatgpt.com"
        )

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def _list_stubs(
        self, on_page: Optional[Callable[[int, int], None]] = None
    ) -> list[dict]:
        """Return metadata dicts for every conversation (paginated)."""
        stubs: list[dict] = []
        offset, limit = 0, 100

        while True:
            r = _get_with_retry(
                self._session,
                f"{self._BASE}/backend-api/conversations",
                params={"offset": offset, "limit": limit},
            )
            data = r.json()
            batch = data.get("items", [])
            stubs.extend(batch)
            total = data.get("total", 0)
            offset += limit
            if on_page:
                on_page(len(stubs), total)
            if offset >= total or not batch:
                break
            time.sleep(0.2)

        return stubs

    # ------------------------------------------------------------------
    # Fetching individual conversations
    # ------------------------------------------------------------------

    def _fetch_one_raw(self, conv_id: str) -> dict:
        r = _get_with_retry(
            self._session,
            f"{self._BASE}/backend-api/conversation/{conv_id}",
        )
        return r.json()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_all(
        self,
        on_list_progress: Optional[Callable[[int, int], None]] = None,
        on_fetch_progress: Optional[Callable[[int, int], None]] = None,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """
        Return a list of raw conversation dicts in the same shape as the
        ChatGPT export conversations.json — ready to be fed into the
        existing parse_chatgpt_raw() function.

        Args:
            on_list_progress: called as (fetched_so_far, total) while listing.
            on_fetch_progress: called as (fetched_so_far, total) while fetching bodies.
            limit: if set, only fetch this many conversations (newest first).
        """
        stubs = self._list_stubs(on_page=on_list_progress)
        if limit is not None:
            stubs = stubs[:limit]

        results: list[dict] = []
        total = len(stubs)

        for i, stub in enumerate(stubs, 1):
            conv_id = stub.get("id") or stub.get("conversation_id", "")
            if not conv_id:
                continue
            try:
                raw = self._fetch_one_raw(conv_id)
                # Merge stub fields in case the full response omits them
                raw.setdefault("id", conv_id)
                raw.setdefault("title", stub.get("title", "Untitled"))
                raw.setdefault("create_time", stub.get("create_time"))
                results.append(raw)
            except Exception:
                # Skip individual conversations that 404 or otherwise fail
                pass
            if on_fetch_progress:
                on_fetch_progress(i, total)
            time.sleep(_FETCH_DELAY)

        return results


# ---------------------------------------------------------------------------
# Claude.ai fetcher
# ---------------------------------------------------------------------------

class ClaudeFetcher:
    """
    Fetches all conversations from claude.ai.

    Auth flow:
      The sessionKey cookie is used directly — no separate token exchange
      step is required.  The cookie value starts with 'sk-ant-sid01-'.

    Endpoint shape:
      GET /api/organizations               → list orgs → grab first UUID
      GET /api/organizations/{id}/chat_conversations        → list all
      GET /api/organizations/{id}/chat_conversations/{id}  → full messages
    """

    _BASE = "https://claude.ai/api"

    def __init__(self, session_key: str) -> None:
        self._session = _make_session(
            extra_headers={
                "Referer": "https://claude.ai/",
                # Claude.ai also checks this anti-CSRF header on some endpoints
                "anthropic-client-platform": "web_claude_ai",
            }
        )
        # Set the cookie so it's sent with every request
        self._session.cookies.set("sessionKey", session_key, domain="claude.ai")
        self._org_id = self._get_org_id()

    # ------------------------------------------------------------------
    # Auth / org discovery
    # ------------------------------------------------------------------

    def _get_org_id(self) -> str:
        try:
            r = _get_with_retry(self._session, f"{self._BASE}/organizations")
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code in (401, 403):
                raise AuthError(
                    "Claude.ai rejected the session key.\n"
                    "It may have expired — please copy a fresh one from your browser."
                ) from exc
            raise

        orgs = r.json()
        if not orgs:
            raise AuthError(
                "No organisations found in your Claude.ai account.\n"
                "Make sure you're logged in before copying the cookie."
            )
        return orgs[0]["uuid"]

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def _list_stubs(self) -> list[dict]:
        r = _get_with_retry(
            self._session,
            f"{self._BASE}/organizations/{self._org_id}/chat_conversations",
        )
        return r.json()

    # ------------------------------------------------------------------
    # Fetching individual conversations
    # ------------------------------------------------------------------

    def _fetch_one_raw(self, conv_id: str) -> dict:
        r = _get_with_retry(
            self._session,
            f"{self._BASE}/organizations/{self._org_id}/chat_conversations/{conv_id}",
        )
        return r.json()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_all(
        self,
        on_fetch_progress: Optional[Callable[[int, int], None]] = None,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """
        Return a list of raw conversation dicts in the same shape as the
        Claude export conversations.json — ready for parse_claude_raw().

        Args:
            on_fetch_progress: called as (fetched_so_far, total).
            limit: if set, cap at this many conversations (newest first).
        """
        stubs = self._list_stubs()
        # Claude.ai returns newest-first; that's fine
        if limit is not None:
            stubs = stubs[:limit]

        results: list[dict] = []
        total = len(stubs)

        for i, stub in enumerate(stubs, 1):
            conv_id = stub.get("uuid", "")
            if not conv_id:
                continue
            try:
                raw = self._fetch_one_raw(conv_id)
                # Ensure the stub fields are present in case the full response is sparse
                raw.setdefault("uuid", conv_id)
                raw.setdefault("name", stub.get("name", "Untitled"))
                raw.setdefault("created_at", stub.get("created_at"))
                results.append(raw)
            except Exception:
                pass
            if on_fetch_progress:
                on_fetch_progress(i, total)
            time.sleep(_FETCH_DELAY)

        return results


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class AuthError(Exception):
    """Raised when a session token / cookie is rejected or malformed."""


# ---------------------------------------------------------------------------
# Cookie instruction strings (used by the UI layer)
# ---------------------------------------------------------------------------

COOKIE_GUIDE = {
    "ChatGPT": {
        "url": "https://chatgpt.com",
        "cookie_name": "__Secure-next-auth.session-token",
        "hint": "A long string that usually starts with [bold]eyJ[/bold]",
        "domain": "chatgpt.com",
        "steps": [
            "Open [bold cyan]https://chatgpt.com[/bold cyan] in your browser "
            "and make sure you're logged in",
            "Open Developer Tools:\n"
            "      [dim]• Chrome / Edge — press [bold]F12[/bold], or right-click → Inspect\n"
            "      • Firefox — press [bold]F12[/bold] or Ctrl+Shift+I\n"
            "      • Safari — Develop menu → Show Web Inspector\n"
            "        (enable it first: Safari → Settings → Advanced → Show Develop menu)[/dim]",
            "Click the [bold]Application[/bold] tab\n"
            "      [dim](Chrome/Edge — you may need to click [bold]»[/bold] to reveal it;\n"
            "      Firefox calls this tab [bold]Storage[/bold])[/dim]",
            "In the left sidebar, expand [bold]Cookies[/bold] and click\n"
            "      [bold cyan]https://chatgpt.com[/bold cyan]",
            "Find the row named [bold yellow]__Secure-next-auth.session-token[/bold yellow]",
            "Double-click the [bold]Value[/bold] cell for that row\n"
            "      Select all ([bold]Ctrl+A[/bold] / [bold]Cmd+A[/bold]) and copy",
            "Paste it into this terminal when prompted",
        ],
    },
    "Claude": {
        "url": "https://claude.ai",
        "cookie_name": "sessionKey",
        "hint": "Starts with [bold]sk-ant-sid01-[/bold]",
        "domain": "claude.ai",
        "steps": [
            "Open [bold blue]https://claude.ai[/bold blue] in your browser "
            "and make sure you're logged in",
            "Open Developer Tools:\n"
            "      [dim]• Chrome / Edge — press [bold]F12[/bold], or right-click → Inspect\n"
            "      • Firefox — press [bold]F12[/bold] or Ctrl+Shift+I\n"
            "      • Safari — Develop menu → Show Web Inspector[/dim]",
            "Click the [bold]Application[/bold] tab\n"
            "      [dim](Firefox calls this tab [bold]Storage[/bold])[/dim]",
            "In the left sidebar, expand [bold]Cookies[/bold] and click\n"
            "      [bold blue]https://claude.ai[/bold blue]",
            "Find the row named [bold blue]sessionKey[/bold blue]",
            "Double-click the [bold]Value[/bold] cell for that row\n"
            "      Select all ([bold]Ctrl+A[/bold] / [bold]Cmd+A[/bold]) and copy",
            "Paste it into this terminal when prompted",
        ],
    },
}
