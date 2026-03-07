# Changelog

All notable changes to the Art Market Analysis app are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **MAJOR** — breaking changes to the public API (ArtMarketApp, DataLoader, models)
- **MINOR** — new features, data sources, or analyzers (backwards-compatible)
- **PATCH** — bug fixes, documentation updates, test additions

## [Unreleased]

### Changed
- Updated `notes/how-it-works.md` to document DataLoader, source registry, and risk filtering workflow
- Added AGENTS.md instructions requiring how-it-works.md to stay in sync with code changes
- Added versioning and changelog system
- Expanded how-it-works.md with detailed source registry configuration examples (risk tolerance, written agreements, API keys, custom registries)

## [0.4.0] - 2026-03-07

### Added
- `src/source_registry.py` — `SourceRegistry`, `SourceConfig`, and `RiskLevel` enum
- Risk-level filtering in `DataLoader`: each `load_*` method checks `registry.is_source_allowed()` before network calls
- Written agreement override: `registry.set_agreement(key, True)` bypasses risk level
- API key resolution from registry: Smithsonian key auto-read from `SMITHSONIAN_API_KEY` env var
- `skills/assess-risk/SKILL.md` — skill for assessing source license risk

### Changed
- `DataLoader.__init__()` now accepts `max_risk` (default HIGH) and optional `registry` parameter
- `load_scraped_records()` intersects explicit site keys with allowed list
- `load_into_app()` respects risk filtering across all source types

## [0.3.0] - 2026-03-07

### Added
- `notes/terms-of-service.md` — terms of service documentation for all 13 data sources
- Risk level assessments (NONE through HIGH) for each source

## [0.2.0] - 2026-03-07

### Added
- AGENTS.md with project guidelines, TDD practices, and architecture rules
- `skills/add-data-source/SKILL.md`, `skills/add-scraper/SKILL.md`, `skills/run-analysis/SKILL.md`
- `notes/` documentation suite (architecture, testing, data-loading, design-decisions, how-it-works, known-limitations, usage-guide)
- `src/scrapers.py` — 9 auction house web scrapers (Leland Little, Weschler's, Quinn's, Alex Cooper, Hilliard, Potomack, Bunch, Headley's, CTBids)
- Smithsonian Open Access API integration (`fetch_smithsonian_artworks`)
- National Gallery of Art open data integration (`fetch_nga_artworks`)
- Doyle auction house added to seed data

### Fixed
- Crash when Smithsonian API returns a dict instead of string for title field

## [0.1.0] - 2026-03-07

### Added
- Initial app: `ArtMarketApp` orchestrator, domain models, repositories
- `MidAtlanticAuctionTracker` for regional filtering and summary stats
- `OpportunityAnalyzer` for comparing listing prices against auction averages
- `UnidentifiedArtistAnalyzer` with 0-100 scoring for unattributed works
- `MarketGapDetector` for category/medium/artist gap analysis
- `DataLoader` with seed JSON files and Met Museum API integration
- Full pytest test suite
- Seed data: 20 auction houses, 38 auction records
