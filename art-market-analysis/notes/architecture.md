# Art Market Analysis — Architecture Reference

## Directory Structure

```
art-market-analysis/
├── src/                       Source modules
│   ├── __init__.py
│   ├── models.py              Domain objects (AuctionHouse, AuctionRecord, ArtListing)
│   ├── repositories.py        In-memory data storage and querying
│   ├── tracker.py             Mid-Atlantic regional filtering
│   ├── opportunity.py         Price comparison / buying opportunity analysis
│   ├── unidentified.py        Unattributed work scoring (0-100)
│   ├── gap_detector.py        Market gap detection by category/medium/artist
│   ├── app.py                 ArtMarketApp orchestrator + report generation
│   ├── data_loader.py         Multi-source data loading (seed, Met, Smithsonian, NGA)
│   ├── source_registry.py     Risk levels, agreements, API key config per source
│   └── scrapers.py            9 auction house web scrapers
├── tests/                     pytest test suite (205 tests)
│   ├── __init__.py
│   ├── test_models.py         11 tests
│   ├── test_repositories.py   15 tests
│   ├── test_tracker.py        6 tests
│   ├── test_opportunity.py    8 tests
│   ├── test_unidentified.py   8 tests
│   ├── test_gap_detector.py   7 tests
│   ├── test_data_loader.py    45 tests (includes 9 risk-filtering tests)
│   ├── test_source_registry.py 53 tests (risk levels, agreements, API keys, edge cases)
│   ├── test_app.py            9 tests
│   └── test_scrapers.py       45 tests
├── data/                      Seed data
│   ├── houses.json            20 auction houses (16 mid-Atlantic, 1 national, 3 northeast)
│   └── auction_records.json   38 historical auction records
├── notes/                     Project documentation
├── skills/                    Agent skills (agentskills.io format)
└── AGENTS.md                  Agent instructions
```

## Module Dependency Graph

```
data_loader.py ──→ app.py ──→ tracker.py ──→ repositories.py ──→ models.py
    │                │
    │                ├──→ opportunity.py ──→ repositories.py
    │                │
    │                ├──→ unidentified.py ──→ repositories.py
    │                │
    │                └──→ gap_detector.py ──→ repositories.py
    │
    ├──→ source_registry.py (risk levels, agreements, API key config)
    │
    └──→ scrapers.py (standalone, no internal deps)
```

## Key Patterns

- **Domain-Driven Design**: Frozen dataclasses for reference data, mutable for records/listings
- **Repository Pattern**: `AuctionRepository` and `ListingRepository` abstract data access
- **Strategy Pattern**: Separate analyzer classes for each concern
- **Factory Pattern**: `from_dict()` methods on domain objects
- **Registry Pattern**: `SCRAPERS` dict in scrapers.py for scraper lookup; `SourceRegistry` in source_registry.py for risk/agreement/API key management

## Data Flow

1. `DataLoader` loads seed JSON + optional API/scraper sources
2. Creates `ArtMarketApp` instance, loads houses → records → listings
3. App lazily initializes analyzers on first use
4. Each analyzer queries repositories independently
5. `generate_report()` / `generate_text_report()` combines all analyses

## Categories

The system uses these artwork categories: `painting`, `works_on_paper`, `furniture`, `decorative_arts`, `textile`, `sculpture`.

## External Dependencies

- **Runtime**: Python 3.11+ stdlib only (no pip packages)
- **Testing**: pytest with unittest.mock
- **Optional API keys**: Smithsonian (api.data.gov, free)
