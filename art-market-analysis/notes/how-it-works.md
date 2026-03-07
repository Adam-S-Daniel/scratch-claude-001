# Art Market Analysis — How It Works

This document walks through the app end-to-end, showing exactly how data flows from loading through analysis to a final report. We use realistic mid-Atlantic auction house data throughout.

> **Keep this file up to date.** Any change to the data flow, analysis pipeline, source registry, or report format must be reflected here. See AGENTS.md for the full policy.

## Step 0: Configure Source Registry and Risk Filtering

Before loading data, the `DataLoader` consults a `SourceRegistry` to decide which sources are allowed. Each source has a `RiskLevel` (NONE, LOW, MODERATE, HIGH) assessed from its terms of service. The caller sets a `max_risk` threshold — sources above that level are silently skipped unless they have a written agreement on file.

```python3

from src.source_registry import SourceRegistry, RiskLevel

# Default registry has all 13 sources pre-configured
registry = SourceRegistry()

# Check what's allowed at LOW risk
allowed = registry.allowed_sources(max_risk=RiskLevel.LOW)
print(f'Sources allowed at LOW risk: {[s.name for s in allowed]}')

# A written agreement overrides risk level
registry.set_agreement("weschlers", True)
print(f'Weschlers allowed after agreement: {registry.is_source_allowed("weschlers", max_risk=RiskLevel.LOW)}')

```

```output
Sources allowed at LOW risk: ['Seed Data', 'Metropolitan Museum of Art', 'Smithsonian Open Access', 'National Gallery of Art', 'Leland Little Auctions']
Weschlers allowed after agreement: True
```

Risk levels are defined in `src/source_registry.py` and documented in `notes/terms-of-service.md`:

| Risk | Meaning | Examples |
|------|---------|---------|
| NONE | CC0/open license with official API | Met Museum, Smithsonian, NGA, seed data |
| LOW | No explicit scraping prohibition found | Leland Little |
| MODERATE | Terms unknown/unretrievable, or technical barriers | Hilliard, CTBids |
| HIGH | Terms explicitly prohibit scraping/automated access | Weschler's, Quinn's, Alex Cooper, Potomack, Bunch, Headley's |

### Configuring Risk Tolerance

Pass `max_risk` to `DataLoader` to control which sources are used. Every `load_*` method silently skips sources above the threshold.

```python3

from src.data_loader import DataLoader
from src.source_registry import RiskLevel

# Conservative: only CC0/open-license sources (seed JSON, Met, Smithsonian, NGA)
loader_safe = DataLoader(max_risk=RiskLevel.NONE)

# Moderate: also includes Leland Little (no scraping prohibition found)
loader_mid = DataLoader(max_risk=RiskLevel.LOW)

# Permissive: includes Hilliard and CTBids (unknown/unretrievable terms)
loader_wide = DataLoader(max_risk=RiskLevel.MODERATE)

# Default: everything, including HIGH-risk scrapers
loader_all = DataLoader(max_risk=RiskLevel.HIGH)

# Show the scraper keys each loader would allow
for label, ldr in [("NONE", loader_safe), ("LOW", loader_mid),
                    ("MODERATE", loader_wide), ("HIGH", loader_all)]:
    keys = ldr.registry.allowed_scraper_keys(max_risk=ldr.max_risk)
    print(f'{label:>8}: {keys}')

```

```output
    NONE: []
     LOW: ['leland_little']
MODERATE: ['leland_little', 'hilliard', 'ctbids']
    HIGH: ['leland_little', 'hilliard', 'ctbids', 'weschlers', 'quinns', 'alex_cooper', 'potomack', 'bunch', 'headleys']
```

### Written Agreements

A written agreement overrides the risk check for a specific source. This lets you use a HIGH-risk scraper under a LOW-risk policy when you've negotiated permission with the auction house.

```python3

from src.source_registry import SourceRegistry, RiskLevel

registry = SourceRegistry()

# Weschler's is HIGH risk — blocked at LOW by default
print(f'Before agreement: {registry.is_source_allowed("weschlers", max_risk=RiskLevel.LOW)}')

# Record that we have a written agreement with Weschler's
registry.set_agreement("weschlers", True)
print(f'After agreement:  {registry.is_source_allowed("weschlers", max_risk=RiskLevel.LOW)}')

# Revoke the agreement
registry.set_agreement("weschlers", False)
print(f'After revocation: {registry.is_source_allowed("weschlers", max_risk=RiskLevel.LOW)}')

```

```output
Before agreement: False
After agreement:  True
After revocation: False
```

Pass a customized registry to `DataLoader` to use it:

```python3

from src.data_loader import DataLoader
from src.source_registry import SourceRegistry, RiskLevel

registry = SourceRegistry()
registry.set_agreement("weschlers", True)
registry.set_agreement("potomack", True)

# LOW risk, but Weschler's and Potomack are allowed via agreement
loader = DataLoader(max_risk=RiskLevel.LOW, registry=registry)
keys = loader.registry.allowed_scraper_keys(max_risk=loader.max_risk)
print(f'Allowed scrapers: {keys}')

```

```output
Allowed scrapers: ['leland_little', 'weschlers', 'potomack']
```

### API Key Configuration

API keys are resolved from environment variables configured on each `SourceConfig`. The Smithsonian source has `api_key_env="SMITHSONIAN_API_KEY"` — the DataLoader reads this from the environment automatically when the caller doesn't provide one explicitly.

```python3

from src.source_registry import SourceRegistry

registry = SourceRegistry()
si = registry.get("smithsonian")
print(f'Source:       {si.name}')
print(f'Requires key: {si.requires_api_key}')
print(f'Env var:      {si.api_key_env}')
print(f'Secret name:  {si.api_key_secret}')

# Configure a GitHub Secrets name for CI/CD
registry.set_api_key_secret("smithsonian", "SI_API_KEY_PROD")
print(f'Updated secret: {registry.get("smithsonian").api_key_secret}')

```

```output
Source:       Smithsonian Open Access
Requires key: True
Env var:      SMITHSONIAN_API_KEY
Secret name:  SMITHSONIAN_API_KEY
Updated secret: SI_API_KEY_PROD
```

To set the key at runtime, either export the environment variable before running the app, or pass it directly to `load_smithsonian_listings()`:

```bash
# Option A: environment variable (recommended for CI/CD)
export SMITHSONIAN_API_KEY="your-api-key-here"
python -c "from src.data_loader import DataLoader; DataLoader().load_into_app(fetch_smithsonian=True)"

# Option B: pass directly
python -c "
from src.data_loader import DataLoader
loader = DataLoader()
loader.load_smithsonian_listings(api_key='your-api-key-here')
"
```

### Custom Source Configurations

You can build a registry from scratch with only the sources you need:

```python3

from src.source_registry import SourceRegistry, SourceConfig, RiskLevel

custom_sources = {
    "seed": SourceConfig(
        key="seed", name="Seed Data", source_type="seed",
        risk_level=RiskLevel.NONE, license="Internal",
    ),
    "met_museum": SourceConfig(
        key="met_museum", name="Met Museum", source_type="api",
        risk_level=RiskLevel.NONE, license="CC0",
    ),
}

registry = SourceRegistry(sources=custom_sources)
print(f'Total sources: {len(registry.all_sources())}')
print(f'Names: {[s.name for s in registry.all_sources()]}')

```

```output
Total sources: 2
Names: ['Seed Data', 'Met Museum']
```

## Step 1: Load Data via DataLoader

The recommended way to load data is through `DataLoader`, which orchestrates all sources, applies risk filtering, and returns a ready-to-use `ArtMarketApp`. Each `load_*` method checks the registry before making any network calls.

```python3

from src.data_loader import DataLoader
from src.source_registry import RiskLevel

# Only allow NONE-risk sources (seed + museum APIs)
loader = DataLoader(max_risk=RiskLevel.NONE)
app = loader.load_into_app(fetch_met=True, met_max=5)

print(f'Loaded {app.house_count} houses, {app.auction_count} auction records, {app.listing_count} listings')

```

```output
Loaded 20 houses, 38 auction records, 15 listings
```

For direct control, you can also load data manually into `ArtMarketApp`:

```python3

from src.app import ArtMarketApp

app = ArtMarketApp()

# Register mid-Atlantic auction houses
app.load_houses([
    {'name': "Freeman's", 'location': 'Philadelphia, PA', 'region': 'mid-atlantic'},
    {'name': "Weschler's", 'location': 'Washington, DC', 'region': 'mid-atlantic'},
    {'name': 'Brunk Auctions', 'location': 'Asheville, NC', 'region': 'mid-atlantic'},
    {'name': 'Potomack Company', 'location': 'Alexandria, VA', 'region': 'mid-atlantic'},
    {'name': 'Alderfer Auction', 'location': 'Hatfield, PA', 'region': 'mid-atlantic'},
])

# Load past auction results
app.load_auction_data([
    {'lot_number': '101', 'title': 'View of the Delaware', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'date_sold': '2023-11-15', 'hammer_price': 42000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '102', 'title': 'Philadelphia Harbor', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'date_sold': '2024-03-10', 'hammer_price': 38000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '201', 'title': 'Portrait of a Statesman', 'artist': 'Charles Willson Peale',
     'medium': 'oil on canvas', 'date_sold': '2024-01-20', 'hammer_price': 95000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '301', 'title': 'Shenandoah Valley', 'artist': 'Unknown Artist',
     'medium': 'oil on canvas', 'date_sold': '2024-02-15', 'hammer_price': 8500,
     'auction_house': "Weschler's", 'category': 'painting'},
    {'lot_number': '302', 'title': 'Civil War Encampment', 'artist': 'Unidentified',
     'medium': 'oil on panel', 'date_sold': '2024-05-01', 'hammer_price': 6200,
     'auction_house': "Weschler's", 'category': 'painting'},
    {'lot_number': '401', 'title': 'Chippendale Chair', 'artist': 'Unknown Maker',
     'medium': 'mahogany', 'date_sold': '2024-04-10', 'hammer_price': 18500,
     'auction_house': "Freeman's", 'category': 'furniture'},
    {'lot_number': '501', 'title': 'Kirk Silver Repousse Pitcher', 'artist': 'Samuel Kirk',
     'medium': 'silver', 'date_sold': '2024-06-01', 'hammer_price': 14000,
     'auction_house': 'Potomack Company', 'category': 'decorative_arts'},
    {'lot_number': '502', 'title': 'Silver Serving Tray', 'artist': 'Unknown Maker',
     'medium': 'silver', 'date_sold': '2024-03-20', 'hammer_price': 4800,
     'auction_house': 'Brunk Auctions', 'category': 'decorative_arts'},
])

# Load current listings on the market
app.load_listing_data([
    {'listing_id': 'CL001', 'title': 'Delaware River Morning', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'asking_price': 25000, 'source': 'Schwarz Gallery',
     'category': 'painting', 'date_listed': '2025-01-15'},
    {'listing_id': 'CL002', 'title': 'Maryland Landscape', 'artist': 'Unknown Artist',
     'medium': 'oil on canvas', 'asking_price': 3500, 'source': 'Estate Sale',
     'category': 'painting', 'date_listed': '2025-01-20'},
    {'listing_id': 'CL003', 'title': 'Federal Card Table', 'artist': 'Unknown Maker',
     'medium': 'mahogany', 'asking_price': 7500, 'source': 'M.S. Rau',
     'category': 'furniture', 'date_listed': '2025-03-01'},
    {'listing_id': 'CL004', 'title': 'Kirk Silver Coffee Set', 'artist': 'Samuel Kirk',
     'medium': 'silver', 'asking_price': 9000, 'source': 'Spencer Marks',
     'category': 'decorative_arts', 'date_listed': '2025-02-20'},
])

print(f'Loaded {app.house_count} houses, {app.auction_count} auction records, {app.listing_count} listings')

```

```output
Loaded 5 houses, 8 auction records, 4 listings
```

## Step 2: Regional Tracking

The tracker filters to only mid-Atlantic auction houses and provides summary statistics for the regional market.

```python3

from src.app import ArtMarketApp
import json

app = ArtMarketApp()
app.load_houses([
    {'name': "Freeman's", 'location': 'Philadelphia, PA', 'region': 'mid-atlantic'},
    {'name': "Weschler's", 'location': 'Washington, DC', 'region': 'mid-atlantic'},
    {'name': 'Brunk Auctions', 'location': 'Asheville, NC', 'region': 'mid-atlantic'},
    {'name': 'Potomack Company', 'location': 'Alexandria, VA', 'region': 'mid-atlantic'},
])
app.load_auction_data([
    {'lot_number': '101', 'title': 'View of the Delaware', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'date_sold': '2023-11-15', 'hammer_price': 42000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '201', 'title': 'Portrait', 'artist': 'Charles Willson Peale',
     'medium': 'oil on canvas', 'date_sold': '2024-01-20', 'hammer_price': 95000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '301', 'title': 'Shenandoah Valley', 'artist': 'Unknown Artist',
     'medium': 'oil on canvas', 'date_sold': '2024-02-15', 'hammer_price': 8500,
     'auction_house': "Weschler's", 'category': 'painting'},
    {'lot_number': '501', 'title': 'Kirk Silver Pitcher', 'artist': 'Samuel Kirk',
     'medium': 'silver', 'date_sold': '2024-06-01', 'hammer_price': 14000,
     'auction_house': 'Potomack Company', 'category': 'decorative_arts'},
])

summary = app.get_regional_summary()
print(f'Tracked houses:  {summary["total_houses"]}')
print(f'Auction records: {summary["total_records"]}')
print(f'Avg hammer:      ${summary["avg_price"]:,.0f}')
print(f'Price range:     ${summary["min_price"]:,.0f} - ${summary["max_price"]:,.0f}')
print(f'Categories:      {summary["categories"]}')

```

```output
Tracked houses:  4
Auction records: 4
Avg hammer:      $39,875
Price range:     $8,500 - $95,000
Categories:      {'painting': 3, 'decorative_arts': 1}
```

## Step 3: Identify Buying Opportunities

The OpportunityAnalyzer compares each current listing's asking price against the average hammer price for that artist at auction. Listings priced below their artist's auction average are flagged as buying opportunities.

```python3

from src.app import ArtMarketApp

app = ArtMarketApp()
app.load_houses([
    {'name': "Freeman's", 'location': 'Philadelphia, PA', 'region': 'mid-atlantic'},
    {'name': "Weschler's", 'location': 'Washington, DC', 'region': 'mid-atlantic'},
])
app.load_auction_data([
    {'lot_number': '101', 'title': 'View of the Delaware', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'date_sold': '2023-11-15', 'hammer_price': 42000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '102', 'title': 'Philadelphia Harbor', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'date_sold': '2024-03-10', 'hammer_price': 38000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '301', 'title': 'Shenandoah Valley', 'artist': 'Unknown Artist',
     'medium': 'oil on canvas', 'date_sold': '2024-02-15', 'hammer_price': 8500,
     'auction_house': "Weschler's", 'category': 'painting'},
    {'lot_number': '501', 'title': 'Kirk Pitcher', 'artist': 'Samuel Kirk',
     'medium': 'silver', 'date_sold': '2024-06-01', 'hammer_price': 14000,
     'auction_house': "Freeman's", 'category': 'decorative_arts'},
])
app.load_listing_data([
    {'listing_id': 'CL001', 'title': 'Delaware River Morning', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'asking_price': 25000, 'source': 'Schwarz Gallery',
     'category': 'painting', 'date_listed': '2025-01-15'},
    {'listing_id': 'CL002', 'title': 'Maryland Landscape', 'artist': 'Unknown Artist',
     'medium': 'oil on canvas', 'asking_price': 3500, 'source': 'Estate Sale',
     'category': 'painting', 'date_listed': '2025-01-20'},
    {'listing_id': 'CL004', 'title': 'Kirk Coffee Set', 'artist': 'Samuel Kirk',
     'medium': 'silver', 'asking_price': 9000, 'source': 'Spencer Marks',
     'category': 'decorative_arts', 'date_listed': '2025-02-20'},
])

opps = app.find_buying_opportunities()
print('BUYING OPPORTUNITIES')
print('=' * 60)
for o in opps:
    print(f'  {o.listing.title} by {o.listing.artist}')
    print(f'    Asking: ${o.listing.asking_price:,.0f}  |  Avg Auction: ${o.avg_auction_price:,.0f}')
    print(f'    Discount: {o.discount_pct:.1f}%  |  Source: {o.listing.source}')
    print()

```

```output
BUYING OPPORTUNITIES
============================================================
  Maryland Landscape by Unknown Artist
    Asking: $3,500  |  Avg Auction: $8,500
    Discount: 58.8%  |  Source: Estate Sale

  Delaware River Morning by Thomas Birch
    Asking: $25,000  |  Avg Auction: $40,000
    Discount: 37.5%  |  Source: Schwarz Gallery

  Kirk Coffee Set by Samuel Kirk
    Asking: $9,000  |  Avg Auction: $14,000
    Discount: 35.7%  |  Source: Spencer Marks

```

## Step 4: Score Promising Unidentified Works

The UnidentifiedArtistAnalyzer looks at current listings by unattributed artists and scores them based on how well similar unidentified works have performed at auction. Each listing gets a 0–100 score with explanatory signals.

```python3

from src.app import ArtMarketApp

app = ArtMarketApp()
app.load_houses([
    {'name': "Freeman's", 'location': 'Philadelphia, PA', 'region': 'mid-atlantic'},
    {'name': "Weschler's", 'location': 'Washington, DC', 'region': 'mid-atlantic'},
])
app.load_auction_data([
    {'lot_number': '301', 'title': 'Shenandoah Valley', 'artist': 'Unknown Artist',
     'medium': 'oil on canvas', 'date_sold': '2024-02-15', 'hammer_price': 8500,
     'auction_house': "Weschler's", 'category': 'painting'},
    {'lot_number': '302', 'title': 'Civil War Scene', 'artist': 'Unidentified',
     'medium': 'oil on panel', 'date_sold': '2024-05-01', 'hammer_price': 6200,
     'auction_house': "Weschler's", 'category': 'painting'},
    {'lot_number': '401', 'title': 'Chippendale Chair', 'artist': 'Unknown Maker',
     'medium': 'mahogany', 'date_sold': '2024-04-10', 'hammer_price': 18500,
     'auction_house': "Freeman's", 'category': 'furniture'},
])
app.load_listing_data([
    {'listing_id': 'CL002', 'title': 'Maryland Landscape', 'artist': 'Unknown Artist',
     'medium': 'oil on canvas', 'asking_price': 3500, 'source': 'Estate Sale',
     'category': 'painting', 'date_listed': '2025-01-20'},
    {'listing_id': 'CL003', 'title': 'Federal Card Table', 'artist': 'Unknown Maker',
     'medium': 'mahogany', 'asking_price': 7500, 'source': 'M.S. Rau',
     'category': 'furniture', 'date_listed': '2025-03-01'},
])

promising = app.find_promising_unidentified_works()
print('PROMISING UNIDENTIFIED WORKS')
print('=' * 60)
for pw in promising:
    print(f'  {pw.listing.title} ({pw.listing.medium})')
    print(f'    Asking: ${pw.listing.asking_price:,.0f}  |  Comparable Avg: ${pw.comparable_avg_price:,.0f}')
    print(f'    Score: {pw.score:.1f}/100')
    for sig in pw.signals:
        print(f'    -> {sig}')
    print()

```

```output
PROMISING UNIDENTIFIED WORKS
============================================================
  Federal Card Table (mahogany)
    Asking: $7,500  |  Comparable Avg: $18,500
    Score: 84.8/100
    -> 1 unidentified works in 'furniture' sold for avg $18,500 at auction
    -> Listed at $7,500, below comparable avg of $18,500

  Maryland Landscape (oil on canvas)
    Asking: $3,500  |  Comparable Avg: $7,350
    Score: 47.4/100
    -> 2 unidentified works in 'painting' sold for avg $7,350 at auction
    -> Listed at $3,500, below comparable avg of $7,350

```

## Step 5: Detect Market Gaps

The MarketGapDetector compares average auction prices against average listing prices across categories, mediums, and individual artists. Categories where listings consistently trail auction values represent buying opportunities at scale.

```python3

from src.app import ArtMarketApp

app = ArtMarketApp()
app.load_houses([
    {'name': "Freeman's", 'location': 'Philadelphia, PA', 'region': 'mid-atlantic'},
    {'name': "Weschler's", 'location': 'Washington, DC', 'region': 'mid-atlantic'},
    {'name': 'Potomack Company', 'location': 'Alexandria, VA', 'region': 'mid-atlantic'},
])
app.load_auction_data([
    {'lot_number': '101', 'title': 'Landscape A', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'date_sold': '2023-11-15', 'hammer_price': 42000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '102', 'title': 'Landscape B', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'date_sold': '2024-03-10', 'hammer_price': 38000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '201', 'title': 'Portrait', 'artist': 'C.W. Peale',
     'medium': 'oil on canvas', 'date_sold': '2024-01-20', 'hammer_price': 95000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '401', 'title': 'Chippendale Chair', 'artist': 'Unknown',
     'medium': 'mahogany', 'date_sold': '2024-04-10', 'hammer_price': 18500,
     'auction_house': "Freeman's", 'category': 'furniture'},
    {'lot_number': '501', 'title': 'Kirk Pitcher', 'artist': 'Samuel Kirk',
     'medium': 'silver', 'date_sold': '2024-06-01', 'hammer_price': 14000,
     'auction_house': 'Potomack Company', 'category': 'decorative_arts'},
])
app.load_listing_data([
    {'listing_id': 'CL001', 'title': 'River Morning', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'asking_price': 25000, 'source': 'Gallery',
     'category': 'painting', 'date_listed': '2025-01-15'},
    {'listing_id': 'CL002', 'title': 'Pastoral', 'artist': 'Unknown',
     'medium': 'oil on canvas', 'asking_price': 3500, 'source': 'Estate Sale',
     'category': 'painting', 'date_listed': '2025-01-20'},
    {'listing_id': 'CL003', 'title': 'Card Table', 'artist': 'Unknown',
     'medium': 'mahogany', 'asking_price': 7500, 'source': 'Dealer',
     'category': 'furniture', 'date_listed': '2025-03-01'},
    {'listing_id': 'CL004', 'title': 'Kirk Coffee Set', 'artist': 'Samuel Kirk',
     'medium': 'silver', 'asking_price': 9000, 'source': 'Spencer Marks',
     'category': 'decorative_arts', 'date_listed': '2025-02-20'},
])

gaps = app.find_market_gaps()
print('MARKET GAPS (Categories Where Listings Trail Auction Values)')
print('=' * 60)
for g in gaps:
    print(f'  {g.segment}:')
    print(f'    Avg Auction: ${g.avg_auction_price:,.0f}  |  Avg Listing: ${g.avg_listing_price:,.0f}')
    print(f'    Gap: {g.gap_pct:.1f}%  ({g.num_auction_records} auctions, {g.num_listings} listings)')
    print()

```

```output
MARKET GAPS (Categories Where Listings Trail Auction Values)
============================================================
  painting:
    Avg Auction: $58,333  |  Avg Listing: $14,250
    Gap: 75.6%  (3 auctions, 2 listings)

  furniture:
    Avg Auction: $18,500  |  Avg Listing: $7,500
    Gap: 59.5%  (1 auctions, 1 listings)

  decorative_arts:
    Avg Auction: $14,000  |  Avg Listing: $9,000
    Gap: 35.7%  (1 auctions, 1 listings)

```

## Step 6: Generate Full Report

The `generate_text_report()` method produces a complete human-readable analysis combining all findings into a single document.

```python3

from src.app import ArtMarketApp

app = ArtMarketApp()
app.load_houses([
    {'name': "Freeman's", 'location': 'Philadelphia, PA', 'region': 'mid-atlantic'},
    {'name': "Weschler's", 'location': 'Washington, DC', 'region': 'mid-atlantic'},
    {'name': 'Brunk Auctions', 'location': 'Asheville, NC', 'region': 'mid-atlantic'},
    {'name': 'Potomack Company', 'location': 'Alexandria, VA', 'region': 'mid-atlantic'},
    {'name': 'Alderfer Auction', 'location': 'Hatfield, PA', 'region': 'mid-atlantic'},
])
app.load_auction_data([
    {'lot_number': '101', 'title': 'View of the Delaware', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'date_sold': '2023-11-15', 'hammer_price': 42000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '102', 'title': 'Philadelphia Harbor', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'date_sold': '2024-03-10', 'hammer_price': 38000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '201', 'title': 'Portrait of a Statesman', 'artist': 'Charles Willson Peale',
     'medium': 'oil on canvas', 'date_sold': '2024-01-20', 'hammer_price': 95000,
     'auction_house': "Freeman's", 'category': 'painting'},
    {'lot_number': '301', 'title': 'Shenandoah Valley', 'artist': 'Unknown Artist',
     'medium': 'oil on canvas', 'date_sold': '2024-02-15', 'hammer_price': 8500,
     'auction_house': "Weschler's", 'category': 'painting'},
    {'lot_number': '302', 'title': 'Civil War Encampment', 'artist': 'Unidentified',
     'medium': 'oil on panel', 'date_sold': '2024-05-01', 'hammer_price': 6200,
     'auction_house': "Weschler's", 'category': 'painting'},
    {'lot_number': '401', 'title': 'Chippendale Chair', 'artist': 'Unknown Maker',
     'medium': 'mahogany', 'date_sold': '2024-04-10', 'hammer_price': 18500,
     'auction_house': "Freeman's", 'category': 'furniture'},
    {'lot_number': '501', 'title': 'Kirk Silver Pitcher', 'artist': 'Samuel Kirk',
     'medium': 'silver', 'date_sold': '2024-06-01', 'hammer_price': 14000,
     'auction_house': 'Potomack Company', 'category': 'decorative_arts'},
    {'lot_number': '502', 'title': 'Silver Tray', 'artist': 'Unknown Maker',
     'medium': 'silver', 'date_sold': '2024-03-20', 'hammer_price': 4800,
     'auction_house': 'Brunk Auctions', 'category': 'decorative_arts'},
    {'lot_number': '701', 'title': 'Star Quilt', 'artist': 'Anonymous',
     'medium': 'textile', 'date_sold': '2024-02-28', 'hammer_price': 3200,
     'auction_house': 'Alderfer Auction', 'category': 'textile'},
])
app.load_listing_data([
    {'listing_id': 'CL001', 'title': 'Delaware River Morning', 'artist': 'Thomas Birch',
     'medium': 'oil on canvas', 'asking_price': 25000, 'source': 'Schwarz Gallery',
     'category': 'painting', 'date_listed': '2025-01-15'},
    {'listing_id': 'CL002', 'title': 'Maryland Landscape', 'artist': 'Unknown Artist',
     'medium': 'oil on canvas', 'asking_price': 3500, 'source': 'Estate Sale',
     'category': 'painting', 'date_listed': '2025-01-20'},
    {'listing_id': 'CL003', 'title': 'Virginia Gentleman', 'artist': 'Unidentified',
     'medium': 'oil on canvas', 'asking_price': 4200, 'source': 'Antique Shop',
     'category': 'painting', 'date_listed': '2025-02-10'},
    {'listing_id': 'CL004', 'title': 'Federal Card Table', 'artist': 'Unknown Maker',
     'medium': 'mahogany', 'asking_price': 7500, 'source': 'M.S. Rau',
     'category': 'furniture', 'date_listed': '2025-03-01'},
    {'listing_id': 'CL005', 'title': 'Kirk Silver Coffee Set', 'artist': 'Samuel Kirk',
     'medium': 'silver', 'asking_price': 9000, 'source': 'Spencer Marks',
     'category': 'decorative_arts', 'date_listed': '2025-02-20'},
    {'listing_id': 'CL006', 'title': 'Pastoral with Figures', 'artist': 'Anonymous',
     'medium': 'oil on panel', 'asking_price': 1800, 'source': 'eBay',
     'category': 'painting', 'date_listed': '2025-01-25'},
])

print(app.generate_text_report())

```

```output
============================================================
  Mid-Atlantic Art Market Analysis Report
============================================================

REGIONAL SUMMARY
----------------------------------------
  Tracked auction houses: 5
  Total auction records:  9
  Average hammer price:   $25,578
  Price range:            $3,200 - $95,000

BUYING OPPORTUNITIES (Underpriced Listings)
----------------------------------------
  Maryland Landscape by Unknown Artist
    Asking: $3,500 | Avg Auction: $8,500 | Discount: 58.8%
    Source: Estate Sale
  Pastoral with Figures by Anonymous
    Asking: $1,800 | Avg Auction: $3,200 | Discount: 43.8%
    Source: eBay
  Delaware River Morning by Thomas Birch
    Asking: $25,000 | Avg Auction: $40,000 | Discount: 37.5%
    Source: Schwarz Gallery
  Kirk Silver Coffee Set by Samuel Kirk
    Asking: $9,000 | Avg Auction: $14,000 | Discount: 35.7%
    Source: Spencer Marks
  Federal Card Table by Unknown Maker
    Asking: $7,500 | Avg Auction: $11,650 | Discount: 35.6%
    Source: M.S. Rau
  Virginia Gentleman by Unidentified
    Asking: $4,200 | Avg Auction: $6,200 | Discount: 32.3%
    Source: Antique Shop

PROMISING WORKS BY UNIDENTIFIED ARTISTS
----------------------------------------
  Federal Card Table (mahogany)
    Asking: $7,500 | Comparable Avg: $18,500 | Score: 84.8
    -> 1 unidentified works in 'furniture' sold for avg $18,500 at auction
    -> Listed at $7,500, below comparable avg of $18,500
  Pastoral with Figures (oil on panel)
    Asking: $1,800 | Comparable Avg: $7,350 | Score: 49.8
    -> 2 unidentified works in 'painting' sold for avg $7,350 at auction
    -> Listed at $1,800, below comparable avg of $7,350
  Maryland Landscape (oil on canvas)
    Asking: $3,500 | Comparable Avg: $7,350 | Score: 47.4
    -> 2 unidentified works in 'painting' sold for avg $7,350 at auction
    -> Listed at $3,500, below comparable avg of $7,350
  Virginia Gentleman (oil on canvas)
    Asking: $4,200 | Comparable Avg: $7,350 | Score: 44.6
    -> 2 unidentified works in 'painting' sold for avg $7,350 at auction
    -> Listed at $4,200, below comparable avg of $7,350

MARKET GAPS (Categories Below Auction Values)
----------------------------------------
  painting: Auction avg $37,940 vs Listing avg $8,625 (77.3% gap)
  furniture: Auction avg $18,500 vs Listing avg $7,500 (59.5% gap)
  decorative_arts: Auction avg $9,400 vs Listing avg $9,000 (4.3% gap)

============================================================
```

## Data Flow Summary

```
SourceRegistry (risk levels, agreements, API keys)
        │
        ▼
DataLoader(max_risk=RiskLevel.LOW, registry=...)
  ├─ load_seed_data()           → houses.json, auction_records.json
  ├─ load_met_listings()        → Met Museum Collection API  [risk: NONE]
  ├─ load_smithsonian_listings()→ Smithsonian Open Access API [risk: NONE, key required]
  ├─ load_nga_listings()        → NGA open data CSV           [risk: NONE]
  └─ load_scraped_records()     → 9 auction house scrapers    [risk: LOW–HIGH]
        │                         (filtered by max_risk + agreements)
        ▼
ArtMarketApp (orchestrator)
  ├─ MidAtlanticAuctionTracker  → regional summary
  ├─ OpportunityAnalyzer        → buying opportunities
  ├─ UnidentifiedArtistAnalyzer → promising unattributed works
  └─ MarketGapDetector          → category/medium/artist gaps
        │
        ▼
generate_text_report() / generate_report_data()
```

Each `load_*` method in DataLoader checks `registry.is_source_allowed(key, max_risk)` before making any network call. If the source is above the risk threshold and has no written agreement, the method returns immediately with no data. Scraper keys passed explicitly to `load_scraped_records()` are intersected with the allowed list, so even explicit requests for HIGH-risk scrapers are blocked when `max_risk` is set lower.
