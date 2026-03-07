# Art Market Analysis — Design Decisions

*2026-03-07T03:02:23Z by Showboat 0.6.1*
<!-- showboat-id: fb6133ba-6f49-4ac3-88b1-ebadc515627a -->

This document walks through the key design decisions made while building the secondary market art analysis app, explaining the rationale behind each choice.

## 1. Domain-Driven Design with Immutable Value Objects

The core of the app is built around three domain models: `AuctionHouse`, `AuctionRecord`, and `ArtListing`. `AuctionHouse` is a frozen dataclass (immutable value object) because auction houses are reference data — they don't change during analysis. Records and listings are mutable dataclasses since they may need annotation during processing.

Each model carries a `from_dict()` factory method for loading from JSON/dict data, keeping serialization concerns close to the domain rather than in a separate layer.

```bash
head -12 src/models.py
```

```output
"""Core domain models for the art market analysis app."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date


_UNIDENTIFIED_PATTERNS = [
    r"(?i)^unknown",
    r"(?i)^unidentified",
    r"(?i)^anonymous",
```

## 2. Regex-Based Unidentified Artist Detection

Auction houses use wildly inconsistent labels for unattributed works: 'Unknown Artist', 'Unidentified', 'Anonymous', 'School of', 'Manner of', 'Attributed to Unknown', 'Circle of Unknown'. Rather than exact string matching, we use compiled regex patterns that cover all common variants. The patterns are compiled once at module load time for performance.

```python3

from src.models import _is_unidentified

test_labels = [
    'Unknown Artist', 'Unidentified', 'Anonymous',
    'School of', 'Manner of', 'Attributed to Unknown',
    'Circle of Unknown', 'Thomas Cole', 'Gilbert Stuart'
]
for label in test_labels:
    result = _is_unidentified(label)
    print(f'{label:30s} -> unidentified={result}')

```

```output
Unknown Artist                 -> unidentified=True
Unidentified                   -> unidentified=True
Anonymous                      -> unidentified=True
School of                      -> unidentified=True
Manner of                      -> unidentified=True
Attributed to Unknown          -> unidentified=True
Circle of Unknown              -> unidentified=True
Thomas Cole                    -> unidentified=False
Gilbert Stuart                 -> unidentified=False
```

## 3. Repository Pattern for Data Access

Rather than passing raw lists around, all data goes through `AuctionRepository` and `ListingRepository`. This provides a single place for query logic (filter by artist, category, date range, price range) and keeps the analyzers decoupled from data storage. If we later switch from in-memory to a database, only the repositories change — the analyzers remain untouched.

## 4. Separate Analyzers for Each Concern

The analysis logic is split into four focused classes:

- **MidAtlanticAuctionTracker**: Regional filtering and summary stats. Knows which auction houses belong to the mid-Atlantic and only returns their records.
- **OpportunityAnalyzer**: Compares artist-level auction averages against current listing prices. Identifies underpriced (buying opportunities) and overpriced listings.
- **UnidentifiedArtistAnalyzer**: Specialized for unattributed works. Scores listings based on how well similar unidentified works have performed at auction, by category and medium.
- **MarketGapDetector**: Broad market-level analysis. Finds categories, mediums, and artists where listing prices systematically trail auction results.

This separation means each analyzer can be tested and reasoned about independently. The `ArtMarketApp` orchestrator composes them.

## 5. Scoring System for Unidentified Works

The `score_listing()` method produces a 0–100 score based on three weighted signals:

- **Category signal (up to 40 pts)**: If unidentified works in this category sold well at auction, the category itself carries value (e.g., painting vs. textile).
- **Medium signal (up to 30 pts)**: If the specific medium (oil on canvas, silver, etc.) has high-value unidentified sales, it's a positive signal.
- **Price gap signal (up to 30 pts)**: How far below comparable auction averages the listing is priced — the bigger the gap, the more upside.

This weighted approach avoids a single-factor trap. A cheap oil painting by an unknown artist in a category with strong unidentified sales scores highest.

```python3

from datetime import date
from src.models import ArtListing
from src.repositories import AuctionRepository, ListingRepository, AuctionRecord
from src.unidentified import UnidentifiedArtistAnalyzer

# Set up with some auction data
ar = AuctionRepository()
lr = ListingRepository()
ar.add(AuctionRecord('1', 'Landscape', 'Unknown Artist', 'oil on canvas', date(2024,1,1), 8500, 'Test', 'painting'))
ar.add(AuctionRecord('2', 'Portrait', 'Unidentified', 'oil on canvas', date(2024,2,1), 12000, 'Test', 'painting'))
ar.add(AuctionRecord('3', 'Quilt', 'Anonymous', 'textile', date(2024,3,1), 800, 'Test', 'textile'))

# Two listings to compare
painting = ArtListing('L1', 'River View', 'Unknown', 'oil on canvas', 3000, 'Dealer', 'painting', date(2025,1,1))
quilt = ArtListing('L2', 'Star Quilt', 'Anonymous', 'textile', 500, 'eBay', 'textile', date(2025,1,1))

lr.add(painting)
lr.add(quilt)

analyzer = UnidentifiedArtistAnalyzer(ar, lr)
print(f'Oil painting score: {analyzer.score_listing(painting):.1f}/100')
print(f'Textile quilt score: {analyzer.score_listing(quilt):.1f}/100')
print()
print('The painting scores higher because its category/medium have')
print('much higher comparable auction values.')

```

```output
Oil painting score: 62.2/100
Textile quilt score: 14.4/100

The painting scores higher because its category/medium have
much higher comparable auction values.
```

## 6. Red/Green TDD Discipline

Every component was built test-first:

1. Write a failing test file that imports a module that doesn't exist yet (RED)
2. Run pytest to confirm it fails with `ModuleNotFoundError` (RED verified)
3. Implement just enough code to make the tests pass (GREEN)
4. Fix any test expectation bugs found during GREEN (e.g., the price range count was 3 not 2)
5. Move to the next module

This approach caught a real bug in the test data itself — a price range test expected 2 results but 3 listings fell in range. The TDD cycle surfaced this immediately rather than letting a wrong assumption propagate.
