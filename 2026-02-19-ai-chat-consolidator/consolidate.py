#!/usr/bin/env python3
"""
AI Conversation Consolidator
Gathers your chat history from ChatGPT, Claude, and Gemini into one place.
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
    try:
        import rich  # noqa: F401
    except ImportError:
        missing.append("rich")
    if missing:
        print("\n[!] Missing required packages. Please run:\n")
        print(f"    pip install {' '.join(missing)}\n")
        print("Then run this script again.\n")
        sys.exit(1)

check_deps()

# ---------------------------------------------------------------------------
# Imports that need rich/anthropic
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
# Parsers
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
    Accepts:
      - a ZIP file  (the downloaded export)
      - a folder containing conversations.json
      - conversations.json directly
    """
    json_path = _resolve_json(path, "conversations.json")
    if json_path is None:
        return []

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    conversations = []
    for raw in data:
        title = raw.get("title") or "Untitled"
        created = _iso_or_epoch(raw.get("create_time"))
        conv_id = raw.get("id") or raw.get("conversation_id")

        # Build an ordered list of messages by traversing the tree
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
    """Walk the ChatGPT message tree to produce a flat list."""
    if not mapping:
        return []

    # Find the root (node whose parent is not in the mapping, or parent is None)
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
    visited = set()
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
                messages.append(Message(
                    role=role_raw,
                    text=text,
                    timestamp=ts,
                ))
        # Follow children in order
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
                # Sometimes content is a list of blocks
                text = " ".join(
                    block.get("text", "") for block in text
                    if isinstance(block, dict)
                )
            text = text.strip()
            ts = m.get("created_at")
            if text:
                messages.append(Message(role=role, text=text, timestamp=ts))

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
    Parse a Gemini export.
    Tries several known formats:
      1. Google Takeout JSON (chunkedPrompt.chunks)
      2. Third-party exporter format
      3. Simple linear array format
    Accepts ZIP, folder, or .json file directly.
    """
    # Gemini Takeout may use different filenames
    json_path = (
        _resolve_json(path, "Gemini Apps Activity.json")
        or _resolve_json(path, "gemini_export.json")
        or _resolve_json(path, "conversations.json")
        or _resolve_json(path, "*.json")  # any json in folder/zip
    )
    if json_path is None:
        return []

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    # Normalise to a list
    if isinstance(data, dict):
        # Might be {"conversations": [...]} or a single conversation
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

        # Format 1: chunkedPrompt (Google Takeout-style)
        if "chunkedPrompt" in raw:
            chunks = raw["chunkedPrompt"].get("chunks", [])
            for chunk in chunks:
                role_raw = chunk.get("role", "")
                role = "user" if role_raw == "user" else "assistant"
                text = chunk.get("text", "").strip()
                if text and not chunk.get("isThought", False):
                    messages.append(Message(role=role, text=text))

        # Format 2: messages array
        elif "messages" in raw:
            for m in raw["messages"]:
                role_raw = m.get("role") or m.get("author") or ""
                role = "user" if role_raw in ("user", "human") else "assistant"
                text = (m.get("text") or m.get("content") or "").strip()
                if text:
                    messages.append(Message(role=role, text=text,
                                            timestamp=m.get("timestamp")))

        # Format 3: flat turns list
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
    """
    Given a path (ZIP / folder / file), find and return the path to a JSON file
    matching `filename`. If it's a ZIP, extract to a temp folder first.
    `filename` may contain a glob wildcard.
    """
    path = Path(path)

    if not path.exists():
        return None

    # Direct JSON file
    if path.is_file() and path.suffix == ".json":
        return path

    # ZIP file — extract and recurse
    if path.is_file() and path.suffix == ".zip":
        extract_dir = path.parent / (path.stem + "_extracted")
        if not extract_dir.exists():
            with zipfile.ZipFile(path, "r") as zf:
                zf.extractall(extract_dir)
        return _resolve_json(extract_dir, filename)

    # Directory — look for the named file
    if path.is_dir():
        # Exact match first
        candidate = path / filename
        if candidate.exists():
            return candidate
        # Recursive glob
        matches = list(path.rglob(filename if "*" in filename else f"**/{filename}"))
        # Also try direct glob pattern
        if not matches and "*" in filename:
            matches = list(path.glob(filename))
        if matches:
            return matches[0]

    return None


# ---------------------------------------------------------------------------
# AI Filtering
# ---------------------------------------------------------------------------

def ai_filter_conversations(
    conversations: list[Conversation],
    criteria: str,
    api_key: str,
) -> list[Conversation]:
    """
    Use Claude to assess each conversation against the user's criteria.
    Updates conversation.include and conversation.filter_reason in-place.
    """
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
            # Build a compact summary for assessment
            preview_messages = []
            for m in conv.messages[:6]:  # first 6 turns to keep prompt short
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
                # On error, default to include and note it
                conv.include = True
                conv.filter_reason = f"(Assessment error: {e})"

            progress.advance(task)
            time.sleep(0.1)  # gentle rate limiting

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

    # Header
    lines.append("# AI Conversation Archive\n")
    lines.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n")

    if criteria:
        lines.append(f"> **Filter applied:** {criteria}\n")

    # Summary stats
    lines.append("## Summary\n")
    by_provider = {}
    for c in included:
        by_provider.setdefault(c.provider, 0)
        by_provider[c.provider] += 1

    lines.append(f"- **Total conversations included:** {len(included)}")
    for provider, count in sorted(by_provider.items()):
        lines.append(f"  - {provider}: {count}")
    if excluded:
        lines.append(f"- **Conversations excluded by filter:** {len(excluded)}")
    lines.append("")

    # Table of contents
    lines.append("## Table of Contents\n")
    for i, conv in enumerate(included, 1):
        anchor = _make_anchor(f"{i}. {conv.provider} — {conv.title}")
        lines.append(f"{i}. [{conv.provider} — {conv.title}](#{anchor})")
    lines.append("")

    # Conversations
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
            if msg.role == "user":
                lines.append(f"**You:**")
            else:
                lines.append(f"**{conv.provider}:**")
            lines.append("")
            # Indent each paragraph of the message
            for paragraph in msg.text.split("\n"):
                lines.append(paragraph)
            lines.append("")
            lines.append("---")
            lines.append("")

    # Excluded section
    if excluded:
        lines.append("---\n")
        lines.append("## Excluded Conversations\n")
        lines.append(
            "_These conversations were assessed and excluded based on your filter criteria._\n"
        )
        excl_table = ["| # | Provider | Title | Reason |",
                       "|---|----------|-------|--------|"]
        for i, conv in enumerate(excluded, 1):
            reason = conv.filter_reason or "Did not match criteria"
            safe_title = conv.title.replace("|", "\\|")
            safe_reason = reason.replace("|", "\\|")
            excl_table.append(f"| {i} | {conv.provider} | {safe_title} | {safe_reason} |")
        lines.extend(excl_table)
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def _make_anchor(text: str) -> str:
    """Convert a heading to a GitHub-flavored Markdown anchor."""
    return (
        text.lower()
        .replace(" ", "-")
        .replace(".", "")
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "")
        .replace("'", "")
        .replace('"', "")
        .replace("—", "")
        .replace(":", "")
    )


# ---------------------------------------------------------------------------
# Interactive UX helpers
# ---------------------------------------------------------------------------

PROVIDER_INSTRUCTIONS = {
    "ChatGPT": {
        "steps": [
            "Open [bold]ChatGPT[/bold] in your browser (chat.openai.com)",
            "Click your profile icon [bold]→ Settings[/bold]",
            "Go to [bold]Data controls[/bold]",
            "Click [bold]Export data[/bold], then confirm",
            "Wait for the email from OpenAI (usually arrives in minutes)",
            "Download the ZIP file from the email link",
            "Place the ZIP file (or extract and place the folder) here:\n      [cyan]exports/chatgpt/[/cyan]",
        ],
        "folder": "exports/chatgpt",
        "what_to_drop": "ZIP file or extracted folder containing conversations.json",
    },
    "Claude": {
        "steps": [
            "Open [bold]Claude.ai[/bold] in your browser",
            "Click your profile icon [bold]→ Settings[/bold]",
            "Go to [bold]Privacy[/bold]",
            "Click [bold]Export data[/bold]",
            "Wait for the email from Anthropic",
            "Download the ZIP file",
            "Place the ZIP file (or extracted folder) here:\n      [cyan]exports/claude/[/cyan]",
        ],
        "folder": "exports/claude",
        "what_to_drop": "ZIP file or extracted folder containing conversations.json",
    },
    "Gemini": {
        "steps": [
            "Visit [bold]takeout.google.com[/bold] and sign in",
            "Click [bold]Deselect all[/bold], then scroll to find [bold]Gemini Apps Activity[/bold]",
            "Check that box and click [bold]Next step → Create export[/bold]",
            "Wait for Google to email you a download link",
            "Download and place the ZIP file (or JSON files) here:\n      [cyan]exports/gemini/[/cyan]",
            "",
            "[dim]Tip: If Google Takeout doesn't include Gemini yet in your region,[/dim]",
            "[dim]try a browser extension like 'Gemini Chat Exporter' and place[/dim]",
            "[dim]the exported JSON file in exports/gemini/ instead.[/dim]",
        ],
        "folder": "exports/gemini",
        "what_to_drop": "ZIP from Google Takeout, or a JSON file from a Gemini exporter",
    },
}

PARSERS = {
    "ChatGPT": parse_chatgpt,
    "Claude": parse_claude,
    "Gemini": parse_gemini,
}


def print_welcome():
    console.print()
    console.print(Panel(
        Text.from_markup(
            "[bold white]AI Conversation Consolidator[/bold white]\n\n"
            "This tool gathers your chat history from [green]ChatGPT[/green], "
            "[blue]Claude[/blue], and [yellow]Gemini[/yellow]\n"
            "and combines them into a single, searchable Markdown file.\n\n"
            "You can optionally describe [italic]which conversations to include[/italic]\n"
            "and the tool will use AI to filter them for you.\n\n"
            "[dim]No technical knowledge required — just follow the steps![/dim]",
            justify="center",
        ),
        title="[bold cyan]Welcome[/bold cyan]",
        border_style="cyan",
        padding=(1, 4),
    ))
    console.print()


def ask_which_providers() -> list[str]:
    console.print(Rule("[bold]Step 1 of 4 — Choose your providers[/bold]"))
    console.print()
    console.print("Which AI chat services do you have accounts with?")
    console.print("(You can choose as many as apply)\n")

    all_providers = ["ChatGPT", "Claude", "Gemini"]
    chosen = []

    for p in all_providers:
        if Confirm.ask(f"  Include [bold]{p}[/bold] conversations?", default=True):
            chosen.append(p)

    console.print()
    return chosen


def guide_export(providers: list[str], base_dir: Path) -> None:
    console.print(Rule("[bold]Step 2 of 4 — Export your data[/bold]"))
    console.print()
    console.print(
        "You need to export your conversation history from each service.\n"
        "Follow the steps below for each one, then come back here.\n"
    )

    for provider in providers:
        info = PROVIDER_INSTRUCTIONS[provider]
        console.print(f"\n[bold underline]{provider}[/bold underline]")
        for j, step in enumerate(info["steps"], 1):
            if step:
                console.print(f"  [cyan]{j}.[/cyan] {step}")
            else:
                console.print()
        target_folder = base_dir / info["folder"]
        console.print(
            f"\n  [green]Place the exported file(s) in:[/green] "
            f"[bold]{target_folder}[/bold]"
        )

    console.print()
    console.print("[dim]Take your time — this tool will wait for you.[/dim]")
    console.print()
    Prompt.ask(
        "[bold yellow]Press Enter when you have placed all your export files and are ready to continue[/bold yellow]",
        default="",
        show_default=False,
    )
    console.print()


def load_conversations(providers: list[str], base_dir: Path) -> list[Conversation]:
    console.print(Rule("[bold]Step 3 of 4 — Reading your exports[/bold]"))
    console.print()

    all_convs = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        for provider in providers:
            task = progress.add_task(f"Reading {provider} export...", total=None)
            folder = base_dir / PROVIDER_INSTRUCTIONS[provider]["folder"]
            parser = PARSERS[provider]
            convs = []

            if folder.exists():
                # Try each item in the folder
                items = list(folder.iterdir())
                if items:
                    for item in items:
                        try:
                            parsed = parser(item)
                            convs.extend(parsed)
                        except Exception:
                            pass
                    # Deduplicate by conv_id
                    seen = set()
                    unique = []
                    for c in convs:
                        key = c.conv_id or c.title
                        if key not in seen:
                            seen.add(key)
                            unique.append(c)
                    convs = unique

            progress.stop_task(task)

            if convs:
                console.print(
                    f"  [green]✓[/green] [bold]{provider}[/bold]: "
                    f"found [bold]{len(convs)}[/bold] conversations"
                )
            else:
                console.print(
                    f"  [yellow]![/yellow] [bold]{provider}[/bold]: "
                    f"no conversations found in [cyan]{folder}[/cyan]"
                )
                console.print(
                    f"    [dim]Expected: {PROVIDER_INSTRUCTIONS[provider]['what_to_drop']}[/dim]"
                )

            all_convs.extend(convs)

    console.print()
    return all_convs


def ask_filter_criteria() -> tuple[Optional[str], Optional[str]]:
    """Returns (criteria_text, api_key) or (None, None) if skipping."""
    console.print(Rule("[bold]Step 4 of 4 — Filter (optional)[/bold]"))
    console.print()
    console.print(
        "You can optionally describe [italic]which conversations to include[/italic].\n"
        "The tool will use AI to read each conversation and decide whether it matches.\n"
    )
    console.print("[dim]Examples:[/dim]")
    console.print(
        "  [dim]• conversations about my job search[/dim]\n"
        "  [dim]• anything related to cooking or recipes[/dim]\n"
        "  [dim]• technical coding questions only[/dim]\n"
        "  [dim]• personal conversations, not work stuff[/dim]\n"
    )

    if not Confirm.ask("Would you like to filter conversations by topic or content?", default=False):
        console.print()
        return None, None

    console.print()
    criteria = Prompt.ask(
        "[bold]Describe what to include[/bold]\n"
        "  [dim](plain English, as specific or broad as you like)[/dim]\n "
    ).strip()

    if not criteria:
        console.print("[yellow]No criteria entered — skipping filter.[/yellow]\n")
        return None, None

    console.print()
    console.print(
        "To filter with AI, this tool needs your [bold]Anthropic API key[/bold].\n"
        "[dim](Your key is used only locally and never stored.)[/dim]\n"
        "[dim]Get a key at: console.anthropic.com → API Keys[/dim]\n"
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        console.print(f"[green]✓ Found ANTHROPIC_API_KEY in environment.[/green]\n")
    else:
        api_key = Prompt.ask(
            "Paste your Anthropic API key (or press Enter to skip filtering)",
            password=True,
            default="",
        ).strip()

    if not api_key:
        console.print("[yellow]No API key — skipping AI filter.[/yellow]\n")
        return criteria, None

    return criteria, api_key


def show_summary_table(conversations: list[Conversation]) -> None:
    if not conversations:
        return

    table = Table(
        title="Conversations found",
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
        include_str = "[green]Yes[/green]" if conv.include else "[red]No[/red]"
        provider_style = {
            "ChatGPT": "green",
            "Claude": "blue",
            "Gemini": "yellow",
        }.get(conv.provider, "white")

        table.add_row(
            f"[{provider_style}]{conv.provider}[/{provider_style}]",
            conv.title[:50],
            (conv.created_at or "")[:10],
            str(len(conv.messages)),
            include_str,
        )

    console.print(table)
    console.print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    base_dir = Path(__file__).parent
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)

    print_welcome()

    # Step 1 — Which providers?
    providers = ask_which_providers()
    if not providers:
        console.print("[red]No providers selected. Nothing to do![/red]")
        return

    # Step 2 — Guide export
    guide_export(providers, base_dir)

    # Step 3 — Load
    conversations = load_conversations(providers, base_dir)

    if not conversations:
        console.print(
            Panel(
                "[yellow]No conversations were found in any of the export folders.\n\n"
                "Please double-check that you placed your export files in the correct folders\n"
                "and run the script again.[/yellow]",
                title="Nothing found",
                border_style="yellow",
            )
        )
        return

    console.print(
        f"[bold green]Total conversations loaded: {len(conversations)}[/bold green]\n"
    )

    # Step 4 — Filter
    criteria, api_key = ask_filter_criteria()

    if criteria and api_key:
        console.print(f"\n[bold]Filtering with criteria:[/bold] [italic]{criteria}[/italic]\n")
        conversations = ai_filter_conversations(conversations, criteria, api_key)
        included = sum(1 for c in conversations if c.include)
        excluded = sum(1 for c in conversations if not c.include)
        console.print(
            f"\n[green]✓ Included: {included}[/green]  "
            f"[red]✗ Excluded: {excluded}[/red]\n"
        )
    elif criteria and not api_key:
        console.print(
            "[yellow]Filter criteria noted but no API key provided — "
            "all conversations will be included.[/yellow]\n"
        )

    # Show summary table
    show_summary_table(conversations)

    # Generate output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"conversations_{timestamp}.md"

    with console.status("[cyan]Writing Markdown file...[/cyan]"):
        generate_markdown(conversations, criteria, output_file)

    included_count = sum(1 for c in conversations if c.include)

    console.print(
        Panel(
            f"[bold green]Done![/bold green]\n\n"
            f"[white]{included_count} conversation(s) saved to:[/white]\n"
            f"[bold cyan]{output_file}[/bold cyan]\n\n"
            f"[dim]Open it in any Markdown viewer, text editor, or Obsidian.[/dim]",
            title="[bold green]Complete[/bold green]",
            border_style="green",
            padding=(1, 4),
        )
    )
    console.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted. Goodbye![/yellow]\n")
        sys.exit(0)
