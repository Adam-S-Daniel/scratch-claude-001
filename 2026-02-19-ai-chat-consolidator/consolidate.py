#!/usr/bin/env python3
"""
AI Conversation Consolidator
Gathers your chat history from ChatGPT, Claude, and Gemini into one place.

v2: ChatGPT and Claude can be fetched directly — no email export required.
    A session cookie you copy from your browser is all that's needed.
    Gemini still uses the manual Google Takeout / extension export path
    (no public API exists for listing conversation history).
"""

import json
import os
import sys
import time
import zipfile
import glob
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Dependency check — give a friendly error before anything else
# ---------------------------------------------------------------------------
def check_deps():
    missing = []
    for pkg in ["rich", "requests"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print("\n[!] Missing required packages. Please run:\n")
        print(f"    pip install {' '.join(missing)}\n")
        print("Then run this script again.\n")
        sys.exit(1)

check_deps()

# ---------------------------------------------------------------------------
# Imports that need rich
# ---------------------------------------------------------------------------
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.markdown import Markdown
from rich import box

console = Console()

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
class Message:
    def __init__(self, role: str, text: str, timestamp: Optional[str] = None):
        self.role = role          # "user" or "assistant"
        self.text = text
        self.timestamp = timestamp

class Conversation:
    def __init__(self, provider: str, title: str, messages: list[Message],
                 created_at: Optional[str] = None, conv_id: Optional[str] = None):
        self.provider = provider
        self.title = title
        self.messages = messages
        self.created_at = created_at
        self.conv_id = conv_id
        self.include = True          # may be flipped by filter pass
        self.filter_reason = ""

    @property
    def preview(self) -> str:
        """First user message, truncated."""
        for m in self.messages:
            if m.role == "user" and m.text.strip():
                return m.text.strip()[:150]
        return "(no preview)"

    @property
    def word_count(self) -> int:
        return sum(len(m.text.split()) for m in self.messages)


# ---------------------------------------------------------------------------
# Parsers  (file-based — used by the manual-export path)
# ---------------------------------------------------------------------------

def _iso_or_epoch(ts) -> Optional[str]:
    """Normalise a timestamp to a human-readable string."""
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        try:
            return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            return None
    return str(ts)


def parse_chatgpt(path: Path) -> list[Conversation]:
    """
    Parse a ChatGPT export.
    Accepts: ZIP file, folder containing conversations.json, or the JSON directly.
    """
    json_path = _resolve_json(path, "conversations.json")
    if json_path is None:
        return []
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return _parse_chatgpt_list(data)


def _parse_chatgpt_list(data: list[dict]) -> list[Conversation]:
    """Convert a list of raw ChatGPT conversation dicts → Conversation objects."""
    conversations = []
    for raw in data:
        title = raw.get("title") or "Untitled"
        created = _iso_or_epoch(raw.get("create_time"))
        conv_id = raw.get("id") or raw.get("conversation_id")
        mapping = raw.get("mapping", {})
        messages = _chatgpt_linearise(mapping)
        if messages:
            conversations.append(Conversation(
                provider="ChatGPT",
                title=title,
                messages=messages,
                created_at=created,
                conv_id=conv_id,
            ))
    return conversations


def _chatgpt_linearise(mapping: dict) -> list[Message]:
    """Walk the ChatGPT message tree to produce a flat, ordered list."""
    if not mapping:
        return []

    child_ids = set(mapping.keys())
    root_id = None
    for node_id, node in mapping.items():
        parent = node.get("parent")
        if parent is None or parent not in child_ids:
            root_id = node_id
            break
    if root_id is None:
        return []

    messages = []
    visited: set[str] = set()
    stack = [root_id]

    while stack:
        node_id = stack.pop(0)
        if node_id in visited or node_id not in mapping:
            continue
        visited.add(node_id)
        node = mapping[node_id]
        msg = node.get("message")
        if msg:
            role_raw = (msg.get("author") or {}).get("role", "")
            content = msg.get("content") or {}
            parts = content.get("parts") or []
            text = " ".join(str(p) for p in parts if isinstance(p, str)).strip()
            ts = _iso_or_epoch(msg.get("create_time"))
            if role_raw in ("user", "assistant") and text:
                messages.append(Message(role=role_raw, text=text, timestamp=ts))
        for child_id in node.get("children", []):
            stack.append(child_id)

    return messages


def parse_claude(path: Path) -> list[Conversation]:
    """
    Parse a Claude.ai export.
    Accepts ZIP, folder, or conversations.json directly.
    """
    json_path = _resolve_json(path, "conversations.json")
    if json_path is None:
        return []
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return _parse_claude_list(data)


def _parse_claude_list(data: list[dict]) -> list[Conversation]:
    """Convert a list of raw Claude conversation dicts → Conversation objects."""
    conversations = []
    for raw in data:
        title = raw.get("name") or "Untitled"
        created = raw.get("created_at")
        conv_id = raw.get("uuid")

        messages = []
        for m in raw.get("chat_messages", []):
            sender = m.get("sender", "")
            role = "user" if sender == "human" else "assistant"
            text = m.get("text") or m.get("content") or ""
            if isinstance(text, list):
                text = " ".join(
                    block.get("text", "") for block in text
                    if isinstance(block, dict)
                )
            text = text.strip()
            if text:
                messages.append(Message(role=role, text=text, timestamp=m.get("created_at")))

        if messages:
            conversations.append(Conversation(
                provider="Claude",
                title=title,
                messages=messages,
                created_at=created,
                conv_id=conv_id,
            ))
    return conversations


def parse_gemini(path: Path) -> list[Conversation]:
    """
    Parse a Gemini export (Google Takeout or third-party exporter).
    Accepts ZIP, folder, or .json directly.
    """
    json_path = (
        _resolve_json(path, "Gemini Apps Activity.json")
        or _resolve_json(path, "gemini_export.json")
        or _resolve_json(path, "conversations.json")
        or _resolve_json(path, "*.json")
    )
    if json_path is None:
        return []

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        if "conversations" in data:
            data = data["conversations"]
        elif "chunkedPrompt" in data or "messages" in data:
            data = [data]
        else:
            data = list(data.values()) if data else []

    conversations = []
    for raw in data:
        if not isinstance(raw, dict):
            continue
        title = raw.get("title") or raw.get("name") or "Untitled"
        created = raw.get("created_at") or raw.get("createTime")
        conv_id = raw.get("id")
        messages = []

        if "chunkedPrompt" in raw:
            for chunk in raw["chunkedPrompt"].get("chunks", []):
                role = "user" if chunk.get("role") == "user" else "assistant"
                text = chunk.get("text", "").strip()
                if text and not chunk.get("isThought", False):
                    messages.append(Message(role=role, text=text))
        elif "messages" in raw:
            for m in raw["messages"]:
                role_raw = m.get("role") or m.get("author") or ""
                role = "user" if role_raw in ("user", "human") else "assistant"
                text = (m.get("text") or m.get("content") or "").strip()
                if text:
                    messages.append(Message(role=role, text=text, timestamp=m.get("timestamp")))
        elif "turns" in raw:
            for turn in raw["turns"]:
                role = "user" if turn.get("role") == "user" else "assistant"
                text = (turn.get("text") or turn.get("content") or "").strip()
                if text:
                    messages.append(Message(role=role, text=text))

        if messages:
            conversations.append(Conversation(
                provider="Gemini",
                title=title,
                messages=messages,
                created_at=created,
                conv_id=conv_id,
            ))
    return conversations


def _resolve_json(path: Path, filename: str) -> Optional[Path]:
    """Find a JSON file inside a path (ZIP / folder / file)."""
    path = Path(path)
    if not path.exists():
        return None
    if path.is_file() and path.suffix == ".json":
        return path
    if path.is_file() and path.suffix == ".zip":
        extract_dir = path.parent / (path.stem + "_extracted")
        if not extract_dir.exists():
            with zipfile.ZipFile(path, "r") as zf:
                zf.extractall(extract_dir)
        return _resolve_json(extract_dir, filename)
    if path.is_dir():
        candidate = path / filename
        if candidate.exists():
            return candidate
        matches = list(path.rglob(filename if "*" in filename else f"**/{filename}"))
        if not matches and "*" in filename:
            matches = list(path.glob(filename))
        if matches:
            return matches[0]
    return None


# ---------------------------------------------------------------------------
# Auto-fetch helpers  (wraps auto_fetch.py with a rich progress UI)
# ---------------------------------------------------------------------------

def _try_import_fetchers():
    """Import auto_fetch lazily so a missing requests install gives a clean error."""
    try:
        from auto_fetch import ChatGPTFetcher, ClaudeFetcher, COOKIE_GUIDE, AuthError
        return ChatGPTFetcher, ClaudeFetcher, COOKIE_GUIDE, AuthError
    except ImportError as exc:
        console.print(f"\n[red]Could not import auto_fetch.py: {exc}[/red]")
        console.print("Make sure auto_fetch.py is in the same folder as consolidate.py.\n")
        return None, None, None, None


def show_cookie_guide(provider: str) -> None:
    """Print the step-by-step DevTools cookie instructions for a provider."""
    _, _, COOKIE_GUIDE, _ = _try_import_fetchers()
    if COOKIE_GUIDE is None:
        return
    guide = COOKIE_GUIDE[provider]
    console.print()
    console.print(Panel(
        f"[bold]How to copy your {provider} session cookie[/bold]\n\n"
        "[dim]This cookie is like a temporary login pass — it lets the tool\n"
        "read your conversations without storing your password.[/dim]",
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()
    for i, step in enumerate(guide["steps"], 1):
        console.print(f"  [cyan]{i}.[/cyan] {step}")
    console.print()
    console.print(
        f"  [dim]Cookie name:[/dim] [bold]{guide['cookie_name']}[/bold]\n"
        f"  [dim]Looks like:[/dim]  {guide['hint']}"
    )
    console.print()


def autofetch_chatgpt(session_token: str) -> list[Conversation]:
    """Authenticate and download all ChatGPT conversations with a progress display."""
    ChatGPTFetcher, _, _, AuthError = _try_import_fetchers()
    if ChatGPTFetcher is None:
        return []

    try:
        with console.status("[cyan]Authenticating with ChatGPT...[/cyan]"):
            fetcher = ChatGPTFetcher(session_token)
    except AuthError as exc:
        raise
    except Exception as exc:
        raise RuntimeError(f"Unexpected error connecting to ChatGPT: {exc}") from exc

    raw_conversations: list[dict] = []

    # Phase 1: list all conversation stubs
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as prog:
        list_task = prog.add_task("[cyan]Listing ChatGPT conversations...", total=None)

        def on_list(so_far: int, total: int) -> None:
            prog.update(list_task, description=f"[cyan]Listing ChatGPT conversations... ({so_far} / {total} found)")

        stubs = fetcher._list_stubs(on_page=on_list)

    console.print(f"  [green]✓[/green] Found [bold]{len(stubs)}[/bold] ChatGPT conversations")

    # Phase 2: fetch each conversation body
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as prog:
        fetch_task = prog.add_task(
            "[cyan]Downloading ChatGPT conversations...", total=len(stubs)
        )

        def on_fetch(so_far: int, total: int) -> None:
            prog.update(fetch_task, completed=so_far)

        raw_conversations = fetcher.fetch_all(
            on_list_progress=None,   # already done above
            on_fetch_progress=on_fetch,
        )

    return _parse_chatgpt_list(raw_conversations)


def autofetch_claude(session_key: str) -> list[Conversation]:
    """Authenticate and download all Claude.ai conversations with a progress display."""
    _, ClaudeFetcher, _, AuthError = _try_import_fetchers()
    if ClaudeFetcher is None:
        return []

    try:
        with console.status("[cyan]Authenticating with Claude.ai...[/cyan]"):
            fetcher = ClaudeFetcher(session_key)
    except AuthError as exc:
        raise
    except Exception as exc:
        raise RuntimeError(f"Unexpected error connecting to Claude.ai: {exc}") from exc

    with console.status("[cyan]Listing Claude conversations...[/cyan]"):
        stubs = fetcher._list_stubs()

    console.print(f"  [green]✓[/green] Found [bold]{len(stubs)}[/bold] Claude conversations")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as prog:
        fetch_task = prog.add_task(
            "[cyan]Downloading Claude conversations...", total=len(stubs)
        )

        def on_fetch(so_far: int, total: int) -> None:
            prog.update(fetch_task, completed=so_far)

        raw_conversations = fetcher.fetch_all(on_fetch_progress=on_fetch)

    return _parse_claude_list(raw_conversations)


# ---------------------------------------------------------------------------
# AI Filtering
# ---------------------------------------------------------------------------

def ai_filter_conversations(
    conversations: list[Conversation],
    criteria: str,
    api_key: str,
) -> list[Conversation]:
    """Use Claude to assess each conversation against the user's criteria."""
    try:
        import anthropic
    except ImportError:
        console.print("\n[yellow]The 'anthropic' package is not installed. Skipping AI filtering.[/yellow]")
        console.print("Run: [bold]pip install anthropic[/bold]\n")
        return conversations

    client = anthropic.Anthropic(api_key=api_key)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            "[cyan]Assessing conversations with AI...", total=len(conversations)
        )

        for conv in conversations:
            preview_messages = []
            for m in conv.messages[:6]:
                label = "User" if m.role == "user" else "Assistant"
                preview_messages.append(f"{label}: {m.text[:300]}")
            preview_text = "\n".join(preview_messages)

            prompt = f"""You are helping a user filter their AI conversation history.

The user wants to include conversations that match this criteria:
"{criteria}"

Here is a conversation to assess:
Title: {conv.title}
Provider: {conv.provider}
Date: {conv.created_at or 'unknown'}

--- Conversation preview ---
{preview_text}
--- End preview ---

Does this conversation match the user's criteria?

Reply with exactly one of:
INCLUDE - <brief one-sentence reason>
EXCLUDE - <brief one-sentence reason>"""

            try:
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=100,
                    messages=[{"role": "user", "content": prompt}],
                )
                result = response.content[0].text.strip()
                if result.upper().startswith("INCLUDE"):
                    conv.include = True
                    conv.filter_reason = result[len("INCLUDE"):].lstrip(" -").strip()
                else:
                    conv.include = False
                    conv.filter_reason = result[len("EXCLUDE"):].lstrip(" -").strip()
            except Exception as e:
                conv.include = True
                conv.filter_reason = f"(Assessment error: {e})"

            progress.advance(task)
            time.sleep(0.1)

    return conversations


# ---------------------------------------------------------------------------
# Markdown generator
# ---------------------------------------------------------------------------

def generate_markdown(
    conversations: list[Conversation],
    criteria: Optional[str],
    output_path: Path,
) -> None:
    included = [c for c in conversations if c.include]
    excluded = [c for c in conversations if not c.include]
    lines = []

    lines.append("# AI Conversation Archive\n")
    lines.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n")
    if criteria:
        lines.append(f"> **Filter applied:** {criteria}\n")

    lines.append("## Summary\n")
    by_provider: dict[str, int] = {}
    for c in included:
        by_provider.setdefault(c.provider, 0)
        by_provider[c.provider] += 1

    lines.append(f"- **Total conversations included:** {len(included)}")
    for provider, count in sorted(by_provider.items()):
        lines.append(f"  - {provider}: {count}")
    if excluded:
        lines.append(f"- **Conversations excluded by filter:** {len(excluded)}")
    lines.append("")

    lines.append("## Table of Contents\n")
    for i, conv in enumerate(included, 1):
        anchor = _make_anchor(f"{i}. {conv.provider} — {conv.title}")
        lines.append(f"{i}. [{conv.provider} — {conv.title}](#{anchor})")
    lines.append("")

    lines.append("---\n")
    lines.append("## Conversations\n")
    for i, conv in enumerate(included, 1):
        lines.append(f"### {i}. {conv.provider} — {conv.title}\n")
        if conv.created_at:
            lines.append(f"**Date:** {conv.created_at}  ")
        if conv.filter_reason:
            lines.append(f"**Why included:** {conv.filter_reason}  ")
        lines.append(f"**Messages:** {len(conv.messages)}  ")
        lines.append(f"**Words (approx):** {conv.word_count:,}  ")
        lines.append("")
        for msg in conv.messages:
            lines.append(f"**You:**" if msg.role == "user" else f"**{conv.provider}:**")
            lines.append("")
            for paragraph in msg.text.split("\n"):
                lines.append(paragraph)
            lines.append("")
            lines.append("---")
            lines.append("")

    if excluded:
        lines.append("---\n")
        lines.append("## Excluded Conversations\n")
        lines.append("_These conversations were assessed and excluded based on your filter criteria._\n")
        excl_table = ["| # | Provider | Title | Reason |", "|---|----------|-------|--------|"]
        for i, conv in enumerate(excluded, 1):
            reason = conv.filter_reason or "Did not match criteria"
            excl_table.append(
                f"| {i} | {conv.provider} | {conv.title.replace('|', chr(92)+'|')} "
                f"| {reason.replace('|', chr(92)+'|')} |"
            )
        lines.extend(excl_table)
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def _make_anchor(text: str) -> str:
    return (
        text.lower()
        .replace(" ", "-").replace(".", "").replace(",", "")
        .replace("(", "").replace(")", "").replace("/", "")
        .replace("'", "").replace('"', "").replace("—", "").replace(":", "")
    )


# ---------------------------------------------------------------------------
# Step 1 — Provider + method selection
# ---------------------------------------------------------------------------

# Providers that support direct API fetch
_AUTO_CAPABLE = {"ChatGPT", "Claude"}

PROVIDER_COLORS = {"ChatGPT": "green", "Claude": "blue", "Gemini": "yellow"}

MANUAL_EXPORT_INSTRUCTIONS = {
    "ChatGPT": {
        "steps": [
            "Open [bold]ChatGPT[/bold] (chat.openai.com) and log in",
            "Click your profile icon [bold]→ Settings → Data controls[/bold]",
            "Click [bold]Export data[/bold] and confirm",
            "Wait for the email from OpenAI — download the ZIP",
            "Place the ZIP (or extracted folder) in: [cyan]exports/chatgpt/[/cyan]",
        ],
        "folder": "exports/chatgpt",
        "what_to_drop": "ZIP file or folder containing conversations.json",
    },
    "Claude": {
        "steps": [
            "Open [bold]Claude.ai[/bold] and log in",
            "Click your profile icon [bold]→ Settings → Privacy[/bold]",
            "Click [bold]Export data[/bold]",
            "Wait for the email from Anthropic — download the ZIP",
            "Place the ZIP (or extracted folder) in: [cyan]exports/claude/[/cyan]",
        ],
        "folder": "exports/claude",
        "what_to_drop": "ZIP file or folder containing conversations.json",
    },
    "Gemini": {
        "steps": [
            "Go to [bold cyan]takeout.google.com[/bold cyan] and log in",
            "Click [bold]Deselect all[/bold], then find and check [bold]Gemini Apps Activity[/bold]",
            "Click [bold]Next step → Create export[/bold]",
            "Wait for Google's email — download the ZIP",
            "Place the ZIP (or JSON files) in: [cyan]exports/gemini/[/cyan]",
            "",
            "[dim]No Gemini option in Takeout? Try the [bold]Gemini Chat Exporter[/bold][/dim]",
            "[dim]Chrome extension and place the exported JSON in exports/gemini/ instead.[/dim]",
        ],
        "folder": "exports/gemini",
        "what_to_drop": "ZIP from Google Takeout or JSON from a Gemini exporter",
    },
}

PARSERS = {
    "ChatGPT": parse_chatgpt,
    "Claude": parse_claude,
    "Gemini": parse_gemini,
}


def print_welcome() -> None:
    console.print()
    console.print(Panel(
        Text.from_markup(
            "[bold white]AI Conversation Consolidator[/bold white]\n\n"
            "Gathers your chat history from [green]ChatGPT[/green], "
            "[blue]Claude[/blue], and [yellow]Gemini[/yellow]\n"
            "into a single, searchable Markdown file.\n\n"
            "[green]ChatGPT[/green] and [blue]Claude[/blue] can be fetched [bold]automatically[/bold] "
            "— just copy one cookie\n"
            "from your browser and this tool does the rest.\n\n"
            "[dim]No technical knowledge required. Just follow the steps![/dim]",
            justify="center",
        ),
        title="[bold cyan]Welcome[/bold cyan]",
        border_style="cyan",
        padding=(1, 4),
    ))
    console.print()


def ask_providers_and_methods() -> dict[str, str]:
    """
    Ask which providers the user has, and for auto-capable ones whether to
    auto-fetch or do a manual export.

    Returns a dict like:
        {"ChatGPT": "auto", "Claude": "manual", "Gemini": "manual"}
    """
    console.print(Rule("[bold]Step 1 of 3 — Choose your providers[/bold]"))
    console.print()
    console.print("Which AI chat services do you want to include?\n")

    plan: dict[str, str] = {}

    for provider in ["ChatGPT", "Claude", "Gemini"]:
        color = PROVIDER_COLORS[provider]
        if not Confirm.ask(f"  Include [{color}]{provider}[/{color}] conversations?", default=True):
            continue

        if provider in _AUTO_CAPABLE:
            console.print()
            console.print(
                f"  [bold]How would you like to get your {provider} conversations?[/bold]\n"
                f"\n"
                f"  [green]1. Auto-fetch (recommended)[/green]\n"
                f"     Copy one cookie from your browser — the tool fetches everything\n"
                f"     automatically. Takes about a minute. No files to download.\n"
                f"\n"
                f"  [dim]2. Manual export[/dim]\n"
                f"     Request a data export from {provider}, wait for an email,\n"
                f"     download a ZIP, and place it in the exports/ folder.\n"
            )
            choice = Prompt.ask(
                "  Your choice",
                choices=["1", "2"],
                default="1",
            )
            plan[provider] = "auto" if choice == "1" else "manual"
        else:
            # Gemini has no list-conversations API
            plan[provider] = "manual"

        console.print()

    return plan


# ---------------------------------------------------------------------------
# Step 2 — Collect conversations
# ---------------------------------------------------------------------------

def collect_all_providers(
    plan: dict[str, str],
    base_dir: Path,
) -> list[Conversation]:
    """
    For each provider in the plan, either auto-fetch or guide the user
    through the manual export process.  Returns all conversations combined.
    """
    console.print(Rule("[bold]Step 2 of 3 — Getting your conversations[/bold]"))
    console.print()

    # ---- Manual-export providers: show all instructions first, then wait ----
    manual_providers = [p for p, m in plan.items() if m == "manual"]
    if manual_providers:
        _show_manual_instructions(manual_providers, base_dir)

    # ---- Auto-fetch providers: handle one at a time ----
    auto_providers = [p for p, m in plan.items() if m == "auto"]

    all_convs: list[Conversation] = []

    for provider in auto_providers:
        convs = _collect_auto(provider)
        all_convs.extend(convs)

    # ---- Parse any manual exports that are ready ----
    if manual_providers:
        console.print()
        console.print(Rule("[dim]Reading manual exports[/dim]"))
        console.print()
        for provider in manual_providers:
            convs = _collect_manual(provider, base_dir)
            all_convs.extend(convs)

    return all_convs


def _show_manual_instructions(providers: list[str], base_dir: Path) -> None:
    """Print export instructions for all manual providers, then wait."""
    console.print(
        "The following service(s) need a manual export first — "
        "follow the steps below, then come back here.\n"
    )
    for provider in providers:
        info = MANUAL_EXPORT_INSTRUCTIONS[provider]
        color = PROVIDER_COLORS[provider]
        console.print(f"[bold underline {color}]{provider}[/bold underline {color}]")
        for j, step in enumerate(info["steps"], 1):
            if step:
                console.print(f"  [cyan]{j}.[/cyan] {step}")
            else:
                console.print()
        target = base_dir / info["folder"]
        console.print(f"\n  [green]Drop files here:[/green] [bold]{target}[/bold]\n")

    console.print("[dim]Take your time — this tool will wait.[/dim]")
    console.print()
    Prompt.ask(
        "[bold yellow]Press Enter once your export file(s) are in place[/bold yellow]",
        default="",
        show_default=False,
    )


def _collect_auto(provider: str) -> list[Conversation]:
    """
    Walk the user through copying their session cookie, then fetch.
    Retries on auth failure and offers a fallback to manual export.
    """
    _, _, _, AuthError = _try_import_fetchers()

    color = PROVIDER_COLORS[provider]
    console.print(f"[bold {color}]{provider}[/bold {color}] — auto-fetch")
    console.print()

    show_cookie_guide(provider)

    cookie_names = {"ChatGPT": "__Secure-next-auth.session-token", "Claude": "sessionKey"}
    cookie_name = cookie_names[provider]

    fetchers = {"ChatGPT": autofetch_chatgpt, "Claude": autofetch_claude}
    fetcher_fn = fetchers[provider]

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        token = Prompt.ask(
            f"  Paste your [bold]{cookie_name}[/bold] cookie value",
            password=True,
        ).strip()

        if not token:
            console.print("  [yellow]Nothing entered — skipping auto-fetch for this provider.[/yellow]\n")
            return []

        try:
            convs = fetcher_fn(token)
            console.print(
                f"  [green]✓[/green] Downloaded [bold]{len(convs)}[/bold] "
                f"{provider} conversations\n"
            )
            return convs

        except Exception as exc:
            err_msg = str(exc)
            is_auth = AuthError is not None and isinstance(exc, AuthError)

            if is_auth:
                console.print(f"\n  [red]Authentication failed:[/red] {err_msg}\n")
            else:
                console.print(f"\n  [red]Error:[/red] {err_msg}\n")

            if attempt < max_attempts:
                if Confirm.ask(
                    "  Would you like to try a different cookie value?",
                    default=True,
                ):
                    console.print()
                    continue
                else:
                    break
            else:
                console.print(
                    f"  [yellow]Could not authenticate after {max_attempts} attempts.[/yellow]"
                )

        # Offer fallback to manual
        console.print()
        console.print(
            f"  [dim]You can still get your {provider} conversations by doing a manual export.\n"
            f"  Skip for now and add the export file to exports/{provider.lower()}/ "
            f"then re-run the tool.[/dim]\n"
        )
        return []

    return []


def _collect_manual(provider: str, base_dir: Path) -> list[Conversation]:
    """Parse whatever files the user dropped in the manual export folder."""
    info = MANUAL_EXPORT_INSTRUCTIONS[provider]
    folder = base_dir / info["folder"]
    parser = PARSERS[provider]
    convs: list[Conversation] = []

    if folder.exists():
        items = [i for i in folder.iterdir() if not i.name.startswith(".")]
        for item in items:
            try:
                convs.extend(parser(item))
            except Exception:
                pass
        # Deduplicate
        seen: set[str] = set()
        unique: list[Conversation] = []
        for c in convs:
            key = c.conv_id or c.title
            if key not in seen:
                seen.add(key)
                unique.append(c)
        convs = unique

    color = PROVIDER_COLORS[provider]
    if convs:
        console.print(
            f"  [green]✓[/green] [{color}]{provider}[/{color}]: "
            f"[bold]{len(convs)}[/bold] conversations loaded"
        )
    else:
        console.print(
            f"  [yellow]![/yellow] [{color}]{provider}[/{color}]: "
            f"nothing found in [cyan]{folder}[/cyan]"
        )
        console.print(f"    [dim]Expected: {info['what_to_drop']}[/dim]")

    return convs


# ---------------------------------------------------------------------------
# Step 3 — Filter
# ---------------------------------------------------------------------------

def ask_filter_criteria() -> tuple[Optional[str], Optional[str]]:
    """Returns (criteria_text, api_key) or (None, None) to skip filtering."""
    console.print(Rule("[bold]Step 3 of 3 — Filter (optional)[/bold]"))
    console.print()
    console.print(
        "You can describe [italic]which conversations to include[/italic] in plain English.\n"
        "The tool will use AI to read each one and decide if it matches.\n"
    )
    console.print("[dim]Examples:[/dim]")
    console.print(
        "  [dim]• conversations about my job search[/dim]\n"
        "  [dim]• anything related to cooking or recipes[/dim]\n"
        "  [dim]• technical coding questions only[/dim]\n"
        "  [dim]• personal conversations, not work stuff[/dim]\n"
    )

    if not Confirm.ask("Would you like to filter conversations?", default=False):
        console.print()
        return None, None

    console.print()
    criteria = Prompt.ask(
        "[bold]Describe what to include[/bold]\n"
        "  [dim](plain English — as specific or broad as you like)[/dim]\n "
    ).strip()

    if not criteria:
        console.print("[yellow]Nothing entered — skipping filter.[/yellow]\n")
        return None, None

    console.print()
    console.print(
        "Filtering uses the [bold]Anthropic API[/bold] (Claude).\n"
        "[dim]Your key is used only locally and never stored.[/dim]\n"
        "[dim]Get a key at: console.anthropic.com → API Keys[/dim]\n"
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        console.print("[green]✓ Found ANTHROPIC_API_KEY in environment.[/green]\n")
    else:
        api_key = Prompt.ask(
            "Paste your Anthropic API key (or press Enter to skip filtering)",
            password=True,
            default="",
        ).strip()

    if not api_key:
        console.print("[yellow]No API key — skipping filter.[/yellow]\n")
        return criteria, None

    return criteria, api_key


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def show_summary_table(conversations: list[Conversation]) -> None:
    if not conversations:
        return
    table = Table(
        title="Conversations",
        box=box.ROUNDED,
        show_lines=False,
        header_style="bold cyan",
    )
    table.add_column("Provider", style="bold", width=10)
    table.add_column("Title", max_width=50, no_wrap=True)
    table.add_column("Date", width=12)
    table.add_column("Turns", justify="right", width=6)
    table.add_column("Include?", justify="center", width=8)

    for conv in conversations:
        c = PROVIDER_COLORS.get(conv.provider, "white")
        table.add_row(
            f"[{c}]{conv.provider}[/{c}]",
            conv.title[:50],
            (conv.created_at or "")[:10],
            str(len(conv.messages)),
            "[green]Yes[/green]" if conv.include else "[red]No[/red]",
        )
    console.print(table)
    console.print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    base_dir = Path(__file__).parent
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)

    print_welcome()

    # Step 1 — Providers + methods
    plan = ask_providers_and_methods()
    if not plan:
        console.print("[red]No providers selected. Nothing to do![/red]")
        return

    # Step 2 — Collect
    conversations = collect_all_providers(plan, base_dir)

    if not conversations:
        console.print(Panel(
            "[yellow]No conversations were found.\n\n"
            "• For auto-fetch: check that the cookie you pasted was correct and not expired.\n"
            "• For manual export: make sure your export file is in the exports/ subfolder.\n\n"
            "Run the script again once you've sorted it out.[/yellow]",
            title="Nothing found",
            border_style="yellow",
        ))
        return

    console.print(
        f"\n[bold green]Total conversations collected: {len(conversations)}[/bold green]\n"
    )

    # Step 3 — Filter
    criteria, api_key = ask_filter_criteria()

    if criteria and api_key:
        console.print(f"[bold]Filtering:[/bold] [italic]{criteria}[/italic]\n")
        conversations = ai_filter_conversations(conversations, criteria, api_key)
        included = sum(1 for c in conversations if c.include)
        excluded = sum(1 for c in conversations if not c.include)
        console.print(
            f"\n[green]✓ Included: {included}[/green]  "
            f"[red]✗ Excluded: {excluded}[/red]\n"
        )
    elif criteria and not api_key:
        console.print(
            "[yellow]Criteria noted but no API key provided — "
            "all conversations will be included.[/yellow]\n"
        )

    show_summary_table(conversations)

    # Output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"conversations_{timestamp}.md"

    with console.status("[cyan]Writing Markdown file...[/cyan]"):
        generate_markdown(conversations, criteria, output_file)

    included_count = sum(1 for c in conversations if c.include)

    console.print(Panel(
        f"[bold green]Done![/bold green]\n\n"
        f"[white]{included_count} conversation(s) saved to:[/white]\n"
        f"[bold cyan]{output_file}[/bold cyan]\n\n"
        f"[dim]Open it in any Markdown viewer, text editor, or Obsidian.[/dim]",
        title="[bold green]Complete[/bold green]",
        border_style="green",
        padding=(1, 4),
    ))
    console.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted. Goodbye![/yellow]\n")
        sys.exit(0)
