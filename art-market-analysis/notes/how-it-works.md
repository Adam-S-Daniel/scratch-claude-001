# Art Market Analysis — How It Works

*2026-03-07T03:04:02Z by Showboat 0.6.1*
<!-- showboat-id: a5de2862-d9b4-450c-a163-78f4f74dcd9f -->

This document walks through the app end-to-end, showing exactly how data flows from loading through analysis to a final report. We use realistic mid-Atlantic auction house data throughout.

## Step 1: Load Data

The app consumes three types of data: auction house definitions, past auction sale records, and current art listings. Data can come from seed JSON files, the Met Museum API, the Smithsonian Open Access API, or National Gallery of Art open data. All data is loaded as dictionaries.

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
