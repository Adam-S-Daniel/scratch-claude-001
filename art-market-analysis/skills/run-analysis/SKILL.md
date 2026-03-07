---
name: run-analysis
description: Run market analysis using the art market analysis app. Use when the user wants to load data, generate reports, find buying opportunities, or analyze specific artists or categories.
compatibility: Python 3.11+
metadata:
  author: art-market-analysis
  version: "1.0"
---

# Running Market Analysis

## Quick Start — Seed Data Only (No Network)

```python
from src.data_loader import DataLoader

app = DataLoader().load_into_app()
print(app.generate_text_report())
```

## With Live Data Sources

```python
from src.data_loader import DataLoader

app = DataLoader().load_into_app(
    fetch_met=True,                    # Met Museum API (free, no key)
    met_queries=['portrait', 'landscape'],
    met_max=15,
    fetch_smithsonian=True,            # Smithsonian (requires key)
    smithsonian_key="your-key",        # or set SMITHSONIAN_API_KEY env var
    smithsonian_max=20,
    fetch_nga=True,                    # National Gallery of Art (free)
    nga_max=50,
    scrape_sites=["leland_little"],    # Auction house scrapers
    scrape_max=50,
)
```

## Available Analyses

| Method | Returns | Description |
|--------|---------|-------------|
| `app.get_regional_summary()` | dict | Mid-Atlantic market stats |
| `app.find_buying_opportunities()` | list[Opportunity] | Listings below auction avg |
| `app.find_promising_unidentified_works()` | list[PromisingWork] | Scored unattributed works |
| `app.find_market_gaps()` | list[MarketGap] | Categories where listings trail auctions |
| `app.compare_artist("Name")` | dict | Artist-specific comparison |
| `app.generate_report()` | dict | All analyses combined |
| `app.generate_text_report()` | str | Formatted printable report |

## Running from Command Line

```bash
cd art-market-analysis
python -c "
from src.data_loader import DataLoader
app = DataLoader().load_into_app()
print(app.generate_text_report())
"
```

## Scraper Keys

`leland_little`, `weschlers`, `quinns`, `alex_cooper`, `hilliard`, `potomack`, `bunch`, `headleys`, `ctbids`
