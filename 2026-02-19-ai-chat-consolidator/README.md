# AI Conversation Consolidator

Combine your conversation history from **ChatGPT**, **Claude**, and **Gemini** into a single, readable Markdown file — with optional AI-powered filtering so you only get the conversations that matter to you.

---

## What it does

1. Walks you step-by-step through exporting your chat history from each AI service
2. Reads and parses all the exports automatically
3. Optionally asks you to describe (in plain English) which conversations to keep
4. Uses AI to read each conversation and decide whether it matches your description
5. Produces a single clean Markdown file you can open, search, and keep forever

---

## Requirements

- **Python 3.11 or newer**
  Check by running: `python --version` or `python3 --version`
- An internet connection (only needed if you use the AI filtering feature)

---

## Quick start

### 1. Install dependencies

Open a terminal in this folder and run:

```bash
pip install -r requirements.txt
```

> **Not sure how?**
> - **Mac/Linux:** Open Terminal, type `cd `, then drag this folder into the window and press Enter. Then paste the command above.
> - **Windows:** Open Command Prompt or PowerShell, navigate to this folder, then paste the command above.

### 2. Run the tool

```bash
python consolidate.py
```

The script will guide you through everything interactively — no configuration files needed.

---

## What the script will ask you

1. **Which services do you use?**
   Pick any combination of ChatGPT, Claude, and Gemini.

2. **Export your data** (the script shows you exactly how for each service)
   You'll place the downloaded export files into the `exports/` folder.

3. **Do you want to filter conversations?** *(optional)*
   You can describe what to include in plain English, for example:
   - *"conversations about my job search"*
   - *"anything related to cooking or recipes"*
   - *"technical coding questions only"*
   - *"personal stuff, not work"*

   If you choose filtering, you'll need a free **Anthropic API key** (see below).

4. **Done!** Your consolidated Markdown file appears in the `output/` folder.

---

## AI filtering: getting an API key

The filtering feature uses Claude (via Anthropic's API) to read each conversation and decide whether it matches your criteria. To use it:

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Go to **API Keys** and create a new key
4. Paste it when the script asks (it is never stored anywhere)

**Alternatively**, you can set it as an environment variable so you don't have to paste it each time:

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
├── consolidate.py       ← the main script
├── requirements.txt     ← Python package list
├── README.md            ← you are here
├── exports/
│   ├── chatgpt/         ← put your ChatGPT export here
│   ├── claude/          ← put your Claude export here
│   └── gemini/          ← put your Gemini export here
└── output/              ← your consolidated Markdown file lands here
```

---

## Export format notes

| Service | How to export | What you get |
|---------|--------------|-------------|
| **ChatGPT** | Settings → Data controls → Export data | Email with a ZIP file |
| **Claude** | Settings → Privacy → Export data | Email with a ZIP file |
| **Gemini** | [takeout.google.com](https://takeout.google.com) → select Gemini Apps Activity | Email with a ZIP file |

You can drop the ZIP file directly into the relevant `exports/` subfolder — the script will unzip it for you. Or unzip it yourself first; either works.

> **Gemini note:** Google Takeout may not include Gemini in all regions yet. If it's missing, try the [Gemini Chat Exporter](https://chromewebstore.google.com/detail/gemini-chat-exporter) Chrome extension and place the downloaded JSON file in `exports/gemini/`.

---

## Output format

The Markdown file includes:

- A summary with counts per provider
- A table of contents
- Every conversation, formatted with clear **You:** / **Assistant:** labels
- If filtering was used: a table of excluded conversations and why

Open the file in any Markdown viewer — [Obsidian](https://obsidian.md), VS Code, GitHub, Typora, or even a plain text editor.

---

## Privacy

- Your conversation data never leaves your computer (except for the AI filtering step, which sends short previews to Anthropic's API)
- Your API key is used only for the current session and never written to disk
- The export files you place in `exports/` are read locally

---

## Troubleshooting

**"No conversations were found"**
Make sure the export file is in the correct subfolder (`exports/chatgpt/`, `exports/claude/`, or `exports/gemini/`). The script looks for ZIP files and JSON files. If you have a folder, drop the whole folder in.

**"pip: command not found"**
Try `pip3 install -r requirements.txt` instead.

**"python: command not found"**
Try `python3 consolidate.py` instead.

**The Gemini export is missing conversations**
Google Takeout sometimes has a delay or omits recent conversations. Wait 24 hours and try again, or use the Gemini Chat Exporter browser extension as an alternative.

**Filtering is slow**
Each conversation requires one API call. If you have hundreds of conversations, filtering may take a few minutes. The progress bar will show you where you are.
