# Art Market Analysis — Known Limitations & Future Work

## Scraper Limitations

Several of the 9 auction house scrapers have known issues with real-world sites:

| Scraper | Platform | Issue |
|---------|----------|-------|
| weschlers | Cloudflare | Returns 403; needs Cloudflare bypass or Invaluable proxy |
| potomack | Cloudflare | Returns 403; same issue as Weschler's |
| quinns | HiBid | Content rendered client-side via JavaScript; HTML parser returns empty |
| headleys | HiBid | Same JS rendering issue as Quinn's |
| ctbids | React SPA | Client-side rendering; HTML parser returns empty |
| alex_cooper | Auction Mobility | Real URL is bid.alexcooper.com; current URL may not match |
| bunch | Auction Mobility | Real URL is bid.bunchauctions.com; current URL may not match |

All scrapers gracefully return empty lists on failure — the app works fine, just without those sources.

### Potential Fixes

- Use Invaluable or LiveAuctioneers APIs as proxies for blocked sites
- Add Playwright/Selenium support for JS-rendered sites
- Update Auction Mobility scrapers to use correct subdomain URLs
- Add rate limiting and retry logic for intermittent failures

## Data Quality

- **Price estimates**: Met/Smithsonian/NGA listings use algorithmic price estimates based on category averages, not real market prices. Useful for relative comparison but not accurate valuations.
- **Smithsonian title field**: Can be a dict `{"content": "...", "label": "Title"}` instead of a plain string. Code handles this but other nested fields may have similar issues.
- **NGA nationality filter**: Relies on the `nationality` CSV column which may be inconsistent or missing for some records.

## Analysis Limitations

- **Small sample sizes**: Seed data has only 38 records. Statistical analyses (averages, gaps) become unreliable with fewer than ~5 records per segment.
- **No time-based trends**: The app compares current listings to all-time auction averages. Market trends, seasonality, and inflation are not accounted for.
- **Artist matching**: Exact string match only. "C.W. Peale" and "Charles Willson Peale" are treated as different artists.
- **Category classification**: Keyword-based, not ML. Ambiguous items (e.g., "painted wooden box") may be miscategorized.
