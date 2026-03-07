# Art Market Analysis — Usage Guide

*2026-03-07T03:06:44Z by Showboat 0.6.1*
<!-- showboat-id: 9be69a60-2072-4f0c-8843-13f4e400a68a -->

A practical guide to using the art market analysis app. This covers setup, data loading, running analyses, and interpreting results.

## Prerequisites

The app is pure Python 3.11+ with no external dependencies beyond pytest for testing. All you need is:

- Python 3.11 or later
- pytest (for running the test suite)

The app lives in the `art-market-analysis/` directory with source in `src/` and tests in `tests/`.

## Quick Start

The entry point is the `ArtMarketApp` class in `src/app.py`. Create an instance, load your data, and call analysis methods.

```python3

from src.app import ArtMarketApp

app = ArtMarketApp()

# 1. Register auction houses (name, location, region)
app.load_houses([
    {'name': "Freeman's", 'location': 'Philadelphia, PA', 'region': 'mid-atlantic'},
    {'name': "Weschler's", 'location': 'Washington, DC', 'region': 'mid-atlantic'},
])
print(f'Houses loaded: {app.house_count}')

# 2. Load past auction records
app.load_auction_data([
    {'lot_number': '101', 'title': 'River View', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'date_sold': '2024-03-15', 'hammer_price': 40000,
     'auction_house': "Freeman's", 'category': 'painting'},
])
print(f'Auction records: {app.auction_count}')

# 3. Load current listings
app.load_listing_data([
    {'listing_id': 'L1', 'title': 'Harbor Scene', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'asking_price': 22000, 'source': 'Gallery',
     'category': 'painting', 'date_listed': '2025-01-01'},
])
print(f'Listings: {app.listing_count}')
print('Ready to analyze!')

```

```output
Houses loaded: 2
Auction records: 1
Listings: 1
Ready to analyze!
```

## Data Format Reference

### Auction Houses

```python
{
    "name": "Freeman's",              # Auction house name
    "location": "Philadelphia, PA",   # City, State
    "region": "mid-atlantic"          # Region (mid-atlantic, northeast, etc.)
}
```

### Auction Records

```python
{
    "lot_number": "101",              # Lot identifier
    "title": "View of the Delaware",  # Work title
    "artist": "Thomas Birch",         # Artist name (or "Unknown Artist" etc.)
    "medium": "oil on canvas",        # Medium/material
    "date_sold": "2024-03-15",        # ISO date string
    "hammer_price": 42000,            # Final sale price (float)
    "auction_house": "Freeman's",     # Must match a loaded house name
    "category": "painting"            # painting, sculpture, furniture, etc.
}
```

### Art Listings

```python
{
    "listing_id": "CL001",            # Unique listing ID
    "title": "River Morning",         # Work title
    "artist": "Thomas Birch",         # Artist name
    "medium": "oil on canvas",        # Medium
    "asking_price": 25000,            # Current asking price (float)
    "source": "Schwarz Gallery",      # Where the listing is from
    "category": "painting",           # Category
    "date_listed": "2025-01-15"       # ISO date string
}
```

## Available Analysis Methods

### `app.get_regional_summary()`
Returns a dict with total records, houses, average/min/max prices, and category breakdown for mid-Atlantic auctions only.

### `app.find_buying_opportunities()`
Returns a list of `Opportunity` objects — current listings priced below their artist's average auction price. Sorted by discount percentage (best deals first). Each has `.listing`, `.avg_auction_price`, and `.discount_pct`.

### `app.find_promising_unidentified_works()`
Returns a list of `PromisingWork` objects — listings by unidentified artists in categories/mediums where similar unattributed works sold well at auction. Each has `.listing`, `.comparable_avg_price`, `.score` (0–100), and `.signals` (list of explanatory strings).

### `app.find_market_gaps()`
Returns a list of `MarketGap` objects — categories where listing prices systematically trail auction values. Each has `.segment`, `.avg_auction_price`, `.avg_listing_price`, and `.gap_pct`.

### `app.compare_artist(name)`
Returns a detailed dict for a specific artist: their auction history, current listings, and which listings are underpriced vs overpriced.

### `app.generate_report()`
Returns a structured dict with all analyses combined.

### `app.generate_text_report()`
Returns a formatted string report suitable for printing or saving to a file.

## Common Workflows

### Workflow 1: "Is this listing a good deal?"

Use `compare_artist()` to see how a listing compares to past auction results for that artist.

```python3

from src.app import ArtMarketApp

app = ArtMarketApp()
app.load_houses([{'name': "Freeman's", 'location': 'Philadelphia, PA', 'region': 'mid-atlantic'}])
app.load_auction_data([
    {'lot_number': '1', 'title': 'Landscape A', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'date_sold': '2023-06-01', 'hammer_price': 42000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '2', 'title': 'Landscape B', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'date_sold': '2024-01-15', 'hammer_price': 38000,
     'auction_house': "Freeman's", 'category': 'painting'},
])
app.load_listing_data([
    {'listing_id': 'L1', 'title': 'Harbor View', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'asking_price': 28000, 'source': 'Gallery X',
     'category': 'painting', 'date_listed': '2025-02-01'},
])

comp = app.compare_artist('Thomas Birch')
print(f'Artist: {comp["artist"]}')
print(f'Auction records: {comp["num_auction_records"]}')
print(f'Avg auction price: ${comp["avg_auction_price"]:,.0f}')
print(f'Current listings: {len(comp["current_listings"])}')
print(f'Underpriced: {len(comp["underpriced"])}')
if comp['underpriced']:
    l = comp['underpriced'][0]
    discount = (comp['avg_auction_price'] - l.asking_price) / comp['avg_auction_price'] * 100
    print(f'  -> {l.title} at ${l.asking_price:,.0f} ({discount:.0f}% below auction avg)')

```

```output
Artist: Thomas Birch
Auction records: 2
Avg auction price: $40,000
Current listings: 1
Underpriced: 1
  -> Harbor View at $28,000 (30% below auction avg)
```

### Workflow 2: "Find me the best unidentified artist deals"

Use `find_promising_unidentified_works()` to get scored listings by unknown artists, ranked by potential.

```python3

from src.app import ArtMarketApp

app = ArtMarketApp()
app.load_houses([
    {'name': "Freeman's", 'location': 'Philadelphia, PA', 'region': 'mid-atlantic'},
    {'name': "Weschler's", 'location': 'Washington, DC', 'region': 'mid-atlantic'},
])
app.load_auction_data([
    {'lot_number': '1', 'title': 'Valley Scene', 'artist': 'Unknown Artist',
     'medium': 'oil on canvas', 'date_sold': '2024-02-15', 'hammer_price': 8500,
     'auction_house': "Weschler's", 'category': 'painting'},
    {'lot_number': '2', 'title': 'Chippendale Chair', 'artist': 'Unknown Maker',
     'medium': 'mahogany', 'date_sold': '2024-04-10', 'hammer_price': 18500,
     'auction_house': "Freeman's", 'category': 'furniture'},
])
app.load_listing_data([
    {'listing_id': 'L1', 'title': 'Pastoral Scene', 'artist': 'Unknown Artist',
     'medium': 'oil on canvas', 'asking_price': 2800, 'source': 'eBay',
     'category': 'painting', 'date_listed': '2025-01-10'},
    {'listing_id': 'L2', 'title': 'Federal Table', 'artist': 'Unknown Maker',
     'medium': 'mahogany', 'asking_price': 6000, 'source': 'Local Dealer',
     'category': 'furniture', 'date_listed': '2025-02-01'},
])

promising = app.find_promising_unidentified_works()
for pw in promising:
    print(f'{pw.listing.title} — Score: {pw.score:.0f}/100')
    print(f'  Asking ${pw.listing.asking_price:,.0f} vs comparable avg ${pw.comparable_avg_price:,.0f}')
    for s in pw.signals:
        print(f'  -> {s}')
    print()

```

```output
Federal Table — Score: 87/100
  Asking $6,000 vs comparable avg $18,500
  -> 1 unidentified works in 'furniture' sold for avg $18,500 at auction
  -> Listed at $6,000, below comparable avg of $18,500

Pastoral Scene — Score: 54/100
  Asking $2,800 vs comparable avg $8,500
  -> 1 unidentified works in 'painting' sold for avg $8,500 at auction
  -> Listed at $2,800, below comparable avg of $8,500

```

### Workflow 3: "Generate a full market report"

Use `generate_text_report()` for a complete printed report, or `generate_report()` for structured data you can process programmatically.

```python3

from src.app import ArtMarketApp

app = ArtMarketApp()
app.load_houses([
    {'name': "Freeman's", 'location': 'Philadelphia, PA', 'region': 'mid-atlantic'},
    {'name': "Weschler's", 'location': 'Washington, DC', 'region': 'mid-atlantic'},
])
app.load_auction_data([
    {'lot_number': '1', 'title': 'Landscape', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'date_sold': '2024-01-15', 'hammer_price': 40000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '2', 'title': 'Portrait', 'artist': 'Unknown Artist',
     'medium': 'oil on canvas', 'date_sold': '2024-03-01', 'hammer_price': 7500,
     'auction_house': "Weschler's", 'category': 'painting'},
])
app.load_listing_data([
    {'listing_id': 'L1', 'title': 'River Morning', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'asking_price': 24000, 'source': 'Gallery',
     'category': 'painting', 'date_listed': '2025-01-15'},
    {'listing_id': 'L2', 'title': 'Pastoral', 'artist': 'Unknown Artist',
     'medium': 'oil on canvas', 'asking_price': 3000, 'source': 'Estate Sale',
     'category': 'painting', 'date_listed': '2025-02-01'},
])

# Structured report (for programmatic use)
report = app.generate_report()
print('Structured report keys:', list(report.keys()))
print(f'Buying opportunities: {len(report["buying_opportunities"])}')
print(f'Promising unidentified: {len(report["promising_unidentified"])}')
print(f'Market gaps: {len(report["market_gaps"])}')
print()

# Text report (for printing)
print(app.generate_text_report())

```

```output
Structured report keys: ['regional_summary', 'buying_opportunities', 'promising_unidentified', 'market_gaps', 'top_opportunities']
Buying opportunities: 2
Promising unidentified: 1
Market gaps: 1

============================================================
  Mid-Atlantic Art Market Analysis Report
============================================================

REGIONAL SUMMARY
----------------------------------------
  Tracked auction houses: 2
  Total auction records:  2
  Average hammer price:   $23,750
  Price range:            $7,500 - $40,000

BUYING OPPORTUNITIES (Underpriced Listings)
----------------------------------------
  Pastoral by Unknown Artist
    Asking: $3,000 | Avg Auction: $7,500 | Discount: 60.0%
    Source: Estate Sale
  River Morning by Thomas Birch
    Asking: $24,000 | Avg Auction: $40,000 | Discount: 40.0%
    Source: Gallery

PROMISING WORKS BY UNIDENTIFIED ARTISTS
----------------------------------------
  Pastoral (oil on canvas)
    Asking: $3,000 | Comparable Avg: $7,500 | Score: 48.0
    -> 1 unidentified works in 'painting' sold for avg $7,500 at auction
    -> Listed at $3,000, below comparable avg of $7,500

MARKET GAPS (Categories Below Auction Values)
----------------------------------------
  painting: Auction avg $23,750 vs Listing avg $13,500 (43.2% gap)

============================================================
```

## Using the DataLoader

The `DataLoader` class can pull from multiple museum APIs and open data sources:

```python
from src.data_loader import DataLoader

# All available sources
app = DataLoader().load_into_app(
    fetch_met=True,           # Metropolitan Museum (free, no key)
    fetch_smithsonian=True,   # Smithsonian Open Access (requires API key)
    smithsonian_key="key",    # or set SMITHSONIAN_API_KEY env var
    fetch_nga=True,           # National Gallery of Art (free CSV, no key)
    nga_max=50,               # limit NGA results
)
```

Available data sources:
- **Seed data**: Always loaded. 20 auction houses, 38 records.
- **Met Museum API**: Free, no key. American art objects as listings.
- **Smithsonian API**: Free, key from api.data.gov. 5.1M+ items across 21 museums (CC0).
- **NGA Open Data**: Free CSV from GitHub. 130K+ artworks (CC0).
- **Auction house scrapers**: 9 mid-Atlantic auction house websites. Returns past results as auction records.

### Using Scrapers

```python
from src.data_loader import DataLoader

# Scrape specific auction houses
app = DataLoader().load_into_app(
    scrape_sites=["leland_little", "weschlers", "potomack"],
    scrape_max=50,
)

# All 9 scrapers at once
app = DataLoader().load_into_app(
    scrape_sites=["leland_little", "weschlers", "quinns", "alex_cooper",
                  "hilliard", "potomack", "bunch", "headleys", "ctbids"],
    scrape_max=50,
)
```

Available scraper keys: `leland_little`, `weschlers`, `quinns`, `alex_cooper`, `hilliard`, `potomack`, `bunch`, `headleys`, `ctbids`.

## Running Tests

Run the full test suite to verify everything works:

```bash
pytest tests/ -v --tb=short 2>&1 | tail -5
```

The suite includes 143 tests across 9 test modules, covering all source modules including scrapers.
