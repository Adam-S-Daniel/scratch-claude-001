# AGENTS.md — Art Market Analysis

## Project Overview

Python 3.11+ CLI application for analyzing the mid-Atlantic secondary art market. Compares auction house results against current listings to find buying opportunities, score unattributed works, and detect market gaps.

**No external dependencies** — uses only Python stdlib (plus pytest for testing).

## Setup

```bash
cd art-market-analysis
# No install needed — pure stdlib Python
# Verify with:
python -m pytest tests/ -v
```

## Running Tests

```bash
# Full suite (205 tests, ~0.4s)
python -m pytest tests/ -v

# Single module
python -m pytest tests/test_scrapers.py -v

# With coverage summary
python -m pytest tests/ -v --tb=short
```

All tests must pass before committing. There are no linters or formatters configured — just pytest.

## Development Practices

### Red/Green TDD

**Always write tests before implementation.** This project was built entirely test-first:

1. Write a failing test that imports the new function/class (RED)
2. Run `pytest` to confirm the failure
3. Implement just enough code to make it pass (GREEN)
4. Refactor if needed, keeping tests green

Never skip the RED step — it catches test bugs early.

### Edge Case Testing

After implementing any new feature, test edge cases manually using `python -c`:

```bash
python -c "from src.scrapers import _parse_price; print(_parse_price(''))"
python -c "from src.scrapers import _extract_artist; print(_extract_artist(''))"
```

Common edge cases to test:
- Empty strings, None values
- Missing dict keys
- Malformed API responses (nested dicts where strings expected)
- Zero/negative prices
- Non-ASCII characters in titles/artist names
- Network errors (mocked in tests, but verify graceful handling)

### Code Style

- No external dependencies — stdlib only (urllib, json, csv, html.parser, re, dataclasses)
- Type hints on all function signatures
- Docstrings on public functions
- `from __future__ import annotations` at top of each module
- Private helpers prefixed with `_`
- Each source module has a matching `test_` file

## Project Structure

```
src/
├── models.py           Domain objects (AuctionHouse, AuctionRecord, ArtListing)
├── repositories.py     In-memory data storage and querying
├── tracker.py          Mid-Atlantic regional filtering
├── opportunity.py      Price comparison analysis
├── unidentified.py     Unattributed work scoring (0-100 scale)
├── gap_detector.py     Market gap detection
├── app.py              ArtMarketApp orchestrator + reports
├── data_loader.py      Multi-source data loading (seed, Met, Smithsonian, NGA)
├── source_registry.py  Risk levels, agreements, API key config per source
└── scrapers.py         9 auction house web scrapers

tests/                  pytest suite, 205 tests total
data/                  Seed JSON files (houses.json, auction_records.json)
notes/                 Project documentation (keep updated!)
skills/                Agent skills (agentskills.io format)
```

## Key Architectural Rules

1. **No database** — everything is in-memory via repositories
2. **No pip packages** — stdlib only for runtime
3. **Graceful degradation** — all network calls return empty on failure
4. **Optional sources** — DataLoader flags: `fetch_met`, `fetch_smithsonian`, `fetch_nga`, `scrape_sites`
5. **Categories**: `painting`, `works_on_paper`, `furniture`, `decorative_arts`, `textile`, `sculpture`
6. **Risk filtering** — DataLoader accepts `max_risk` (RiskLevel enum: NONE, LOW, MODERATE, HIGH). Sources above the max are skipped unless they have a written agreement (`registry.set_agreement(key, True)`). API keys configured via `api_key_env` on SourceConfig.

## Documentation Maintenance

### Keep notes/ Updated

After making changes, update the relevant notes files:

- `notes/architecture.md` — Module structure, test counts, dependency graph
- `notes/testing.md` — Test counts and module breakdown
- `notes/data-loading.md` — Data sources and usage examples
- `notes/usage-guide.md` — User-facing guide with code examples
- `notes/design-decisions.md` — Architectural rationale
- `notes/how-it-works.md` — End-to-end walkthrough (**see special rule below**)
- `notes/known-limitations.md` — Known issues and future work

When adding features, update test counts in `notes/testing.md` and `notes/architecture.md`.

### Always Keep how-it-works.md Up to Date

**`notes/how-it-works.md` must stay current with the actual codebase.** After any change that affects the data flow, analysis pipeline, source registry, DataLoader parameters, report format, or module interactions, update `notes/how-it-works.md` to reflect the new behavior. This includes:

- Adding or removing data sources or scrapers
- Changing the SourceRegistry, risk levels, or agreement logic
- Modifying DataLoader's `load_into_app()` signature or behavior
- Adding new analyzers or changing existing analysis methods
- Changing the report format (text or data)
- Modifying domain models (AuctionHouse, AuctionRecord, ArtListing)

If you're unsure whether a change affects the walkthrough, err on the side of updating it.

### Maintain the Changelog

After every user-visible change, add an entry to `CHANGELOG.md` under the `[Unreleased]` section. When cutting a release, move unreleased entries under a new version heading. See the changelog file for format details.

### Maintain This File (AGENTS.md)

When adding new modules, data sources, skills, or changing the architecture:
- Update the project structure section above
- Update the test count
- Add any new development practices or rules

### Use and Create Skills

Skills live in `skills/` following the [agentskills.io](https://agentskills.io/specification) format. Each skill is a directory with a `SKILL.md` file containing YAML frontmatter and markdown instructions.

Current skills:
- `skills/add-data-source/` — How to add a new museum API or data source
- `skills/run-analysis/` — How to run analyses and generate reports
- `skills/add-scraper/` — How to add a new auction house web scraper
- `skills/assess-risk/` — How to assess license risk levels and configure source agreements/API keys

When adding a new category of work (e.g., "add-analyzer", "deploy"), create a new skill with step-by-step instructions so future agents can follow the pattern.

## Data Sources

| Source | Type | Auth | Risk | Status |
|--------|------|------|------|--------|
| Seed JSON | Local files | None | NONE | Always loaded |
| Met Museum API | REST | None | NONE | Working |
| Smithsonian API | REST | api.data.gov key | NONE | Working |
| NGA Open Data | CSV/GitHub | None | NONE | Working |
| Leland Little | JSON API scraper | None | LOW | Working |
| Hilliard | HTML scraper | None | MODERATE | May need URL update |
| CTBids | HTML scraper | None | MODERATE | React SPA |
| Weschler's | HTML scraper | None | HIGH | Blocked by Cloudflare |
| Quinn's | HTML scraper | None | HIGH | HiBid JS rendering |
| Alex Cooper | HTML scraper | None | HIGH | Auction Mobility platform |
| Potomack | HTML scraper | None | HIGH | Blocked by Cloudflare |
| Bunch | HTML scraper | None | HIGH | Auction Mobility platform |
| Headley's | HTML scraper | None | HIGH | HiBid JS rendering |

## PR / Commit Guidelines

- Commit messages should be concise and describe the "why" not the "what"
- Run `python -m pytest tests/ -v` before every commit
- Verify all tests pass (currently 205)
- Group related changes into single commits (e.g., "Add Smithsonian API integration" not separate commits for code + tests)
