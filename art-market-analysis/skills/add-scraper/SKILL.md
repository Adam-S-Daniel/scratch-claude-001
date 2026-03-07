---
name: add-scraper
description: Add a new auction house web scraper to the art market analysis app. Use when adding scraping support for a new auction house website.
compatibility: Python 3.11+ stdlib only (urllib, html.parser, json)
metadata:
  author: art-market-analysis
  version: "1.0"
---

# Adding a New Auction House Scraper

All scrapers live in `src/scrapers.py` and follow the same pattern.

## Steps

1. **Research the target site** to determine its architecture:
   - Static HTML with lot data in the DOM → use `_LotHTMLParser`
   - JSON API → use `_fetch_json_api` and parse manually
   - JavaScript SPA (React, Vue, HiBid) → document as a known limitation

2. **Write failing tests first** in `tests/test_scrapers.py`:
   ```python
   class TestScrapeNewHouse:
       @patch("src.scrapers._fetch_html")  # or _fetch_json_api
       def test_parses_results(self, mock_fetch):
           mock_fetch.return_value = """<html>...</html>"""
           results = scrape_new_house(max_results=10)
           assert len(results) >= 1
           assert results[0]["auction_house"] == "New House Name"

       @patch("src.scrapers._fetch_html")
       def test_handles_network_error(self, mock_fetch):
           mock_fetch.side_effect = Exception("Network error")
           results = scrape_new_house(max_results=10)
           assert results == []
   ```

3. **Implement the scraper function**:
   ```python
   def scrape_new_house(max_results: int = 50) -> List[dict]:
       """Scrape past auction results from New House."""
       try:
           html = _fetch_html("https://www.newhouse.com/past-auctions")
           parser = _LotHTMLParser()
           parser.feed(html)
           parser.close()
           records = []
           for lot in parser.lots[:max_results]:
               record = _lot_dict_to_record(lot, "New House Name")
               if record:
                   records.append(record)
           return records
       except Exception:
           return []
   ```

4. **Register in the SCRAPERS dict**:
   ```python
   SCRAPERS["new_house"] = {
       "function": scrape_new_house,
       "auction_house": "New House Name",
       "url": "https://www.newhouse.com",
   }
   ```

5. **Add the house to `data/houses.json`** if not already present.

6. **Update the test** for `test_all_scrapers_registered` to include the new key and increment the count.

7. **Run tests**: `pytest tests/test_scrapers.py -v`

8. **Update notes**: `notes/data-loading.md`, `notes/known-limitations.md`

## Shared Utilities

| Function | Purpose |
|----------|---------|
| `_fetch_html(url)` | GET with browser User-Agent, returns HTML string |
| `_fetch_json_api(url)` | GET with Accept: application/json, returns dict |
| `_LotHTMLParser` | Generic HTML parser for lot containers |
| `_lot_dict_to_record(lot, house, date)` | Convert parsed lot to auction record |
| `_classify_from_text(text)` | Classify category from title/description |
| `_extract_artist(title)` | Extract artist name from lot title |
| `_parse_price(price_str)` | Parse price strings like "$1,500" |

## Current Scrapers

| Key | House | Method |
|-----|-------|--------|
| `leland_little` | Leland Little Auctions | JSON API |
| `weschlers` | Weschler's | HTML |
| `quinns` | Quinn's Auction Galleries | HTML |
| `alex_cooper` | Alex Cooper Auctioneers | HTML |
| `hilliard` | Hilliard & Co. | HTML |
| `potomack` | Potomack Company | HTML |
| `bunch` | William Bunch Auctions | HTML |
| `headleys` | Headley's Auctions | HTML (HiBid) |
| `ctbids` | CTBids | HTML |
