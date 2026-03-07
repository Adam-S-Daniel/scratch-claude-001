---
name: add-data-source
description: Add a new external data source (museum API, open data, or web scraper) to the art market analysis app. Use when adding a new museum API, CSV data source, or auction house scraper integration.
compatibility: Python 3.11+, no external dependencies beyond stdlib
metadata:
  author: art-market-analysis
  version: "1.0"
---

# Adding a New Data Source

Follow this pattern to add a new external data source to the app. Every source added so far follows the same structure.

## Steps

1. **Write failing tests first** (red/green TDD):
   - Add a test class in `tests/test_data_loader.py` (for APIs) or `tests/test_scrapers.py` (for scrapers)
   - Mock all network calls with `unittest.mock.patch`
   - Test the converter function with sample data
   - Test error handling (network errors, empty responses, malformed data)
   - Run `pytest tests/ -v` and confirm RED

2. **Implement the fetch function** in `src/data_loader.py`:
   - Create `fetch_<source>_artworks(query, max_results, api_key=None)` function
   - Use `urllib.request.urlopen` for HTTP (no external deps)
   - Return list of listing dicts matching `ArtListing` schema
   - Handle all exceptions gracefully — return empty list on failure

3. **Implement the converter function**:
   - Create `<source>_object_to_listing(obj)` to convert API response to listing dict
   - Map the source's category/classification to our categories: `painting`, `works_on_paper`, `furniture`, `decorative_arts`, `textile`, `sculpture`
   - Use `_estimate_price(category)` for price estimation if no real price available

4. **Wire into DataLoader**:
   - Add `load_<source>_listings(self, ...)` method to `DataLoader`
   - Add `fetch_<source>` flag and related params to `load_into_app()`
   - Call the new loader in `load_into_app()` when the flag is True

5. **Run tests** and confirm GREEN: `pytest tests/ -v`

6. **Test edge cases** manually: `python -c "from src.data_loader import ..."`

7. **Update documentation**:
   - `notes/data-loading.md` — add source description and usage example
   - `notes/usage-guide.md` — add to DataLoader section
   - `notes/architecture.md` — update test counts and structure

## Example: Adding a New Museum API

```python
# In src/data_loader.py

_NEW_API_BASE = "https://api.example.org/v1"

def _classify_new_object(obj: dict) -> str:
    """Map source classification to our categories."""
    obj_type = (obj.get("type") or "").lower()
    if "painting" in obj_type:
        return "painting"
    # ... more mappings
    return "decorative_arts"

def new_object_to_listing(obj: dict) -> dict | None:
    """Convert API object to our listing format."""
    title = obj.get("title")
    if not title:
        return None
    category = _classify_new_object(obj)
    return {
        "listing_id": f"NEW-{obj.get('id', '0')}",
        "title": title,
        "artist": obj.get("artist") or "Unknown Artist",
        "medium": obj.get("medium") or "unknown",
        "asking_price": _estimate_price(category),
        "source": "New Museum",
        "category": category,
        "date_listed": date.today().isoformat(),
    }
```

## Existing Sources (for reference)

| Source | Type | Auth | Fetch Function |
|--------|------|------|----------------|
| Met Museum | REST API | None | `fetch_met_artworks()` |
| Smithsonian | REST API | api.data.gov key | `fetch_smithsonian_artworks()` |
| NGA | CSV/GitHub | None | `fetch_nga_artworks()` |
| 9 auction houses | Web scraping | None | `scrape_all()` in scrapers.py |
