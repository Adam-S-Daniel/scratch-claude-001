# AI Conversation Consolidator

Combine your conversation history from **ChatGPT**, **Claude**, and **Gemini** into a single, readable Markdown file — with optional AI-powered filtering so you only get the conversations that matter to you.

**ChatGPT and Claude can be fetched automatically** — no email, no waiting, no ZIP files. You copy one cookie value from your browser's Developer Tools and the tool retrieves everything directly. Gemini still uses a manual export (Google Takeout) since no public API exists for listing its conversation history.

---

## What it does

1. Asks which services you use and — for ChatGPT and Claude — whether to auto-fetch or do a manual export
2. **Auto-fetch path:** walks you through copying a session cookie from your browser, then downloads every conversation automatically with a live progress bar
3. **Manual path:** gives you exact step-by-step export instructions, waits while you download the file, and reads it the moment you press Enter
4. Optionally asks you to describe which conversations to keep, in plain English
5. Uses AI to assess each conversation against your description and decide INCLUDE or EXCLUDE
6. Produces a single clean Markdown file you can open, search, and keep forever

---

## Requirements

- **Python 3.11 or newer**
  Check: `python --version` or `python3 --version`
- An internet connection (for auto-fetch and optional AI filtering)

---

## Quick start

### 1. Install dependencies

Open a terminal in this folder and run:

```bash
pip install -r requirements.txt
```

> **Not sure how?**
> - **Mac/Linux:** Open Terminal, type `cd ` (with a space), then drag this folder into the window and press Enter. Then paste the command above.
> - **Windows:** Open Command Prompt or PowerShell, navigate to this folder, and paste the command above.

### 2. Run the tool

```bash
python consolidate.py
```

The script guides you through everything interactively — no config files needed.

---

## What the script will ask you

### Step 1 — Choose your providers and how to collect them

For each service you have an account with, you'll be asked:
- Include it? (yes/no)
- For **ChatGPT** and **Claude**: auto-fetch or manual export?

Gemini is always manual (Google Takeout only).

### Step 2 — Collect your conversations

**Auto-fetch (ChatGPT / Claude):**
The tool shows you a numbered guide for opening Developer Tools in your browser, navigating to the Cookies panel, and copying the right value. Paste it when prompted and the tool lists then downloads every conversation, one by one, with a progress bar. No files to manage.

**Manual export (any provider / Gemini):**
The tool shows you where to click in each service's settings to request a data export. Once you have the downloaded ZIP file, place it in the matching `exports/` subfolder and press Enter. The tool extracts and reads it automatically.

### Step 3 — Filter (optional)

Describe what you want to keep in plain English:

- *"conversations about my job search"*
- *"anything related to cooking or recipes"*
- *"technical coding questions only"*
- *"personal stuff, not work"*

The tool uses Claude (Haiku — fast and cheap) to read a preview of each conversation and decide INCLUDE or EXCLUDE with a one-line explanation. You'll need a free **Anthropic API key** for this step (see below).

---

## Getting an Anthropic API key (for auto-fetch auth check + filtering)

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Go to **API Keys** and create a new key
4. Paste it when the script asks — it is never stored anywhere

Or set it as an environment variable so you don't have to paste it each run:

```bash
# Mac/Linux
export ANTHROPIC_API_KEY=sk-ant-...

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

---

## Folder layout

```
2026-02-19-ai-chat-consolidator/
├── consolidate.py    ← main script — run this
├── auto_fetch.py     ← API fetcher module (used automatically)
├── requirements.txt  ← Python packages
├── README.md         ← you are here
├── exports/
│   ├── chatgpt/      ← manual export: drop ChatGPT ZIP here
│   ├── claude/       ← manual export: drop Claude ZIP here
│   └── gemini/       ← drop Google Takeout ZIP or Gemini JSON here
└── output/           ← your consolidated Markdown file appears here
```

---

## How auto-fetch works (under the hood)

Both ChatGPT and Claude.ai have internal REST APIs that their own web apps use. This tool authenticates with those APIs using a **session cookie** from your browser — the same cookie your browser uses to keep you logged in.

| Provider | Cookie name | What it looks like |
|----------|-------------|-------------------|
| ChatGPT | `__Secure-next-auth.session-token` | Long string starting with `eyJ` |
| Claude | `sessionKey` | Starts with `sk-ant-sid01-` |

The cookie is used only in memory during the run and is never written to disk. If it expires or is invalid, the tool will tell you and offer to try again.

**Gemini:** Google does not expose a public API for listing or retrieving Gemini conversation history. The only supported export path is [Google Takeout](https://takeout.google.com).

---

## Output format

The Markdown file includes:

- A summary with conversation counts per provider
- A clickable table of contents
- Every conversation, with clear **You:** / **Provider:** turn labels
- If filtering was used: a table of excluded conversations with reasons

Open it in [Obsidian](https://obsidian.md), VS Code, GitHub, Typora, or any plain text editor.

---

## Privacy

- The session cookies you paste are used only in memory and never written to disk
- Your conversation data stays on your computer (the auto-fetch step makes requests directly from your machine to the provider's servers, the same as your browser would)
- For the AI filtering step, short previews of each conversation are sent to Anthropic's API — the full text is not sent
- Your Anthropic API key is never stored

---

## Troubleshooting

**"Authentication failed" during auto-fetch**
The session cookie may have expired. Go back to your browser, copy it again (it refreshes when you load the page), and paste the new value.

**"No conversations were found" after manual export**
Make sure the file is in the right subfolder — `exports/chatgpt/`, `exports/claude/`, or `exports/gemini/`. The script handles both ZIP files and extracted folders.

**"pip: command not found"**
Try `pip3 install -r requirements.txt` instead.

**"python: command not found"**
Try `python3 consolidate.py` instead.

**The Gemini export is missing conversations**
Google Takeout sometimes has a delay or omits recent conversations. Wait 24 hours and try again, or try the [Gemini Chat Exporter](https://chromewebstore.google.com/detail/gemini-chat-exporter) Chrome extension and place the JSON file in `exports/gemini/`.

**Filtering is slow**
Each conversation requires one API call. With hundreds of conversations this takes a few minutes — the progress bar shows you where you are.
