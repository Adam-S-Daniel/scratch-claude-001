"""Automated data loading from seed files and museum collection APIs.

Data sources:
- Seed files (data/houses.json, data/auction_records.json): curated records
  from real mid-Atlantic auction houses with realistic market data.
- Metropolitan Museum of Art Collection API: free, no key required. Returns
  real American art objects that we convert to listing format for analysis.
  API docs: https://metmuseum.github.io/
- Smithsonian Open Access API: free, requires api.data.gov key. Returns items
  from 21 museums including SAAM and Hirshhorn. CC0 license.
  API docs: https://www.si.edu/openaccess/devtools
- National Gallery of Art Open Data: free CSV files on GitHub. 130,000+
  artworks. CC0 license.
  Data: https://github.com/NationalGalleryOfArt/opendata
"""
from __future__ import annotations

import csv
import io
import json
import os
import random
from datetime import date
from typing import List
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import URLError

from src.app import ArtMarketApp

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_MET_API_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"
_SMITHSONIAN_API_BASE = "https://api.si.edu/openaccess/api/v1.0"
_NGA_CSV_BASE = (
    "https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/data"
)

# Category mappings from Met classifications to our categories
_MET_CATEGORY_MAP = {
    "paintings": "painting",
    "painting": "painting",
    "drawings": "works_on_paper",
    "prints": "works_on_paper",
    "furniture": "furniture",
    "silver": "decorative_arts",
    "ceramics": "decorative_arts",
    "glass": "decorative_arts",
    "metalwork": "decorative_arts",
    "textiles": "textile",
    "sculpture": "sculpture",
}

# Base price estimates by category (for Met objects which don't have prices)
_CATEGORY_PRICE_RANGES = {
    "painting": (8000, 65000),
    "works_on_paper": (2000, 15000),
    "furniture": (5000, 35000),
    "decorative_arts": (3000, 20000),
    "textile": (1500, 8000),
    "sculpture": (10000, 80000),
}


def _fetch_json(url: str) -> dict:
    """Fetch JSON from a URL. Raises on network failure."""
    with urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode())


def load_seed_houses() -> List[dict]:
    """Load auction house definitions from data/houses.json."""
    path = os.path.join(_DATA_DIR, "houses.json")
    with open(path) as f:
        return json.load(f)


def load_seed_auction_records() -> List[dict]:
    """Load historical auction records from data/auction_records.json."""
    path = os.path.join(_DATA_DIR, "auction_records.json")
    with open(path) as f:
        return json.load(f)


def _classify_met_object(obj: dict) -> str:
    """Map a Met object's classification/objectName to our category system."""
    classification = (obj.get("classification") or "").lower().strip()
    object_name = (obj.get("objectName") or "").lower().strip()
    medium = (obj.get("medium") or "").lower()

    for key, cat in _MET_CATEGORY_MAP.items():
        if key in classification or key in object_name:
            return cat

    # Fallback heuristics from medium
    if "oil on" in medium or "acrylic" in medium:
        return "painting"
    if "silver" in medium:
        return "decorative_arts"
    if "mahogany" in medium or "walnut" in medium or "oak" in medium:
        return "furniture"
    if "watercolor" in medium or "ink" in medium or "pencil" in medium:
        return "works_on_paper"
    if "textile" in medium or "silk" in medium or "cotton" in medium:
        return "textile"
    if "bronze" in medium or "marble" in medium:
        return "sculpture"

    return "decorative_arts"


def _estimate_price(category: str, obj: dict) -> float:
    """Estimate a market price for a Met object based on category and age."""
    low, high = _CATEGORY_PRICE_RANGES.get(category, (5000, 30000))
    # Use objectID as seed for reproducible prices
    rng = random.Random(obj.get("objectID", 0))
    return round(rng.uniform(low, high), -2)


def met_object_to_listing(obj: dict) -> dict:
    """Convert a Met Museum API object to our listing dict format."""
    artist = obj.get("artistDisplayName", "").strip()
    if not artist:
        artist = "Unknown Artist"

    category = _classify_met_object(obj)
    price = _estimate_price(category, obj)

    return {
        "listing_id": f"met-{obj['objectID']}",
        "title": obj.get("title", "Untitled"),
        "artist": artist,
        "medium": obj.get("medium", "unknown"),
        "asking_price": price,
        "source": "Metropolitan Museum of Art",
        "category": category,
        "date_listed": date.today().isoformat(),
    }


def fetch_met_artworks(
    query: str = "american art",
    department_id: int | None = None,
    max_results: int = 20,
) -> List[dict]:
    """Fetch artworks from the Met Museum API and convert to listing format.

    Args:
        query: Search query string.
        department_id: Met department ID (1 = American Wing). None for all.
        max_results: Maximum number of objects to fetch.

    Returns:
        List of listing dicts, or empty list on any error.
    """
    try:
        encoded_query = quote(query, safe="")
        search_url = f"{_MET_API_BASE}/search?q={encoded_query}&hasImages=true"
        if department_id is not None:
            search_url += f"&departmentId={department_id}"

        search_data = _fetch_json(search_url)
        object_ids = search_data.get("objectIDs") or []
        object_ids = object_ids[:max_results]

        listings = []
        for obj_id in object_ids:
            try:
                obj = _fetch_json(f"{_MET_API_BASE}/objects/{obj_id}")
                listing = met_object_to_listing(obj)
                listings.append(listing)
            except Exception:
                continue

        return listings
    except Exception:
        return []


def _classify_smithsonian_object(obj: dict) -> str:
    """Map a Smithsonian object's type/physicalDescription to our categories."""
    obj_type = (obj.get("type") or "").lower()
    phys_desc = (obj.get("physicalDescription") or "").lower()
    title = (obj.get("title") or "").lower()

    for key, cat in _MET_CATEGORY_MAP.items():
        if key in obj_type or key in phys_desc:
            return cat

    # Fallback heuristics
    if "oil on" in phys_desc or "acrylic" in phys_desc:
        return "painting"
    if "watercolor" in phys_desc or "ink" in phys_desc or "pencil" in phys_desc:
        return "works_on_paper"
    if "silver" in phys_desc:
        return "decorative_arts"
    if "mahogany" in phys_desc or "walnut" in phys_desc or "oak" in phys_desc:
        return "furniture"
    if "textile" in phys_desc or "silk" in phys_desc or "cotton" in phys_desc:
        return "textile"
    if "bronze" in phys_desc or "marble" in phys_desc:
        return "sculpture"

    return "decorative_arts"


def smithsonian_object_to_listing(row: dict) -> dict:
    """Convert a Smithsonian API content record to our listing dict format.

    The Smithsonian API returns nested structures. The `row` here is the
    inner content dict (result["content"]["descriptiveNonRepeating"] merged
    with result["content"]["freetext"] etc.), pre-flattened by the caller.
    """
    record_id = row.get("id", "unknown")
    title = row.get("title", "Untitled")
    artist = (row.get("name") or "").strip() or "Unknown Artist"
    medium = row.get("physicalDescription") or "unknown"
    category = _classify_smithsonian_object(row)
    price = _estimate_price(category, {"objectID": hash(record_id) & 0xFFFFFFFF})

    return {
        "listing_id": f"si-{record_id}",
        "title": title if isinstance(title, str) else str(title),
        "artist": artist,
        "medium": medium,
        "asking_price": price,
        "source": "Smithsonian Open Access",
        "category": category,
        "date_listed": date.today().isoformat(),
    }


def _flatten_smithsonian_row(result: dict) -> dict:
    """Flatten a Smithsonian API search result into a simple dict."""
    content = result.get("content", {})
    desc = content.get("descriptiveNonRepeating", {})
    freetext = content.get("freetext", {})
    indexed = content.get("indexedStructured", {})

    # Extract artist name from freetext "name" entries
    name = ""
    name_entries = freetext.get("name", [])
    if name_entries and isinstance(name_entries, list):
        name = name_entries[0].get("content", "")

    # Extract physical description
    phys_desc = ""
    phys_entries = freetext.get("physicalDescription", [])
    if phys_entries and isinstance(phys_entries, list):
        phys_desc = phys_entries[0].get("content", "")

    # Extract object type
    obj_types = indexed.get("object_type", [])
    obj_type = obj_types[0] if obj_types else ""

    return {
        "id": desc.get("record_ID", result.get("id", "")),
        "title": result.get("title", desc.get("title", {}).get("content", "Untitled")),
        "name": name,
        "physicalDescription": phys_desc,
        "type": obj_type,
    }


def fetch_smithsonian_artworks(
    query: str = "american art",
    api_key: str | None = None,
    max_results: int = 20,
) -> List[dict]:
    """Fetch artworks from the Smithsonian Open Access API.

    Args:
        query: Search query string.
        api_key: Smithsonian API key (from api.data.gov). If None, uses
            the SMITHSONIAN_API_KEY environment variable.
        max_results: Maximum number of objects to return.

    Returns:
        List of listing dicts, or empty list on any error.
    """
    if api_key is None:
        api_key = os.environ.get("SMITHSONIAN_API_KEY", "")
    if not api_key:
        return []

    try:
        encoded_query = quote(query, safe="")
        url = (
            f"{_SMITHSONIAN_API_BASE}/search"
            f"?q={encoded_query}"
            f"&rows={max_results}"
            f"&api_key={api_key}"
        )
        data = _fetch_json(url)
        response = data.get("response", {})
        rows = response.get("rows", [])

        listings = []
        for row in rows:
            try:
                flat = _flatten_smithsonian_row(row)
                listing = smithsonian_object_to_listing(flat)
                listings.append(listing)
            except Exception:
                continue

        return listings
    except Exception:
        return []


def _classify_nga_object(row: dict) -> str:
    """Map an NGA object's classification/medium to our category system."""
    classification = (row.get("classification") or "").lower()
    medium = (row.get("medium") or "").lower()

    for key, cat in _MET_CATEGORY_MAP.items():
        if key in classification:
            return cat

    # Fallback heuristics from medium
    if "oil on" in medium or "acrylic" in medium:
        return "painting"
    if "silver" in medium:
        return "decorative_arts"
    if "mahogany" in medium or "walnut" in medium or "oak" in medium:
        return "furniture"
    if "watercolor" in medium or "ink" in medium or "pencil" in medium:
        return "works_on_paper"
    if "textile" in medium or "silk" in medium or "cotton" in medium:
        return "textile"
    if "bronze" in medium or "marble" in medium:
        return "sculpture"

    return "decorative_arts"


def nga_object_to_listing(row: dict) -> dict | None:
    """Convert an NGA CSV row dict to our listing dict format.

    Returns None if the row lacks enough data to be useful.
    """
    obj_id = row.get("objectID") or row.get("objectid") or ""
    title = (row.get("title") or "").strip()
    if not obj_id or not title:
        return None

    artist = (row.get("attribution") or "").strip() or "Unknown Artist"
    medium = (row.get("medium") or "").strip() or "unknown"
    category = _classify_nga_object(row)
    price = _estimate_price(category, {"objectID": int(obj_id) if obj_id.isdigit() else hash(obj_id) & 0xFFFFFFFF})

    return {
        "listing_id": f"nga-{obj_id}",
        "title": title,
        "artist": artist,
        "medium": medium,
        "asking_price": price,
        "source": "National Gallery of Art",
        "category": category,
        "date_listed": date.today().isoformat(),
    }


def fetch_nga_artworks(max_results: int = 50) -> List[dict]:
    """Fetch artworks from the NGA Open Data CSV on GitHub.

    Downloads the objects CSV, parses it, and converts rows to listing dicts.
    Only American art (nationality contains 'american') is included.

    Args:
        max_results: Maximum number of listings to return.

    Returns:
        List of listing dicts, or empty list on any error.
    """
    try:
        url = f"{_NGA_CSV_BASE}/objects.csv"
        req = Request(url, headers={"User-Agent": "ArtMarketAnalysis/1.0"})
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")

        reader = csv.DictReader(io.StringIO(raw))
        listings = []
        for row in reader:
            # Filter to American artworks
            nationality = (row.get("nationality") or "").lower()
            if "american" not in nationality:
                continue
            listing = nga_object_to_listing(row)
            if listing is not None:
                listings.append(listing)
                if len(listings) >= max_results:
                    break

        return listings
    except Exception:
        return []


class DataLoader:
    """Orchestrates loading data from all sources into the app."""

    def __init__(self) -> None:
        self.houses: List[dict] = []
        self.auction_records: List[dict] = []
        self.listings: List[dict] = []

    def load_seed_data(self) -> None:
        """Load curated seed data from local JSON files."""
        self.houses = load_seed_houses()
        self.auction_records = load_seed_auction_records()

    def load_met_listings(
        self,
        queries: List[str] | None = None,
        max_per_query: int = 10,
    ) -> None:
        """Fetch listings from the Met Museum API."""
        if queries is None:
            queries = [
                "american landscape painting",
                "american silver",
                "american furniture",
            ]
        for q in queries:
            results = fetch_met_artworks(query=q, max_results=max_per_query)
            self.listings.extend(results)

    def load_smithsonian_listings(
        self,
        queries: List[str] | None = None,
        api_key: str | None = None,
        max_per_query: int = 10,
    ) -> None:
        """Fetch listings from the Smithsonian Open Access API."""
        if queries is None:
            queries = [
                "american painting",
                "american decorative arts",
                "american sculpture",
            ]
        for q in queries:
            results = fetch_smithsonian_artworks(
                query=q, api_key=api_key, max_results=max_per_query
            )
            self.listings.extend(results)

    def load_nga_listings(self, max_results: int = 50) -> None:
        """Fetch listings from the National Gallery of Art open data."""
        results = fetch_nga_artworks(max_results=max_results)
        self.listings.extend(results)

    def load_into_app(
        self,
        fetch_met: bool = False,
        met_queries: List[str] | None = None,
        met_max: int = 10,
        fetch_smithsonian: bool = False,
        smithsonian_queries: List[str] | None = None,
        smithsonian_key: str | None = None,
        smithsonian_max: int = 10,
        fetch_nga: bool = False,
        nga_max: int = 50,
    ) -> ArtMarketApp:
        """Load all data and return a fully populated ArtMarketApp.

        Args:
            fetch_met: Whether to fetch listings from the Met Museum API.
            met_queries: Search queries for the Met API.
            met_max: Max results per Met query.
            fetch_smithsonian: Whether to fetch from the Smithsonian API.
            smithsonian_queries: Search queries for the Smithsonian API.
            smithsonian_key: Smithsonian API key (or use env var).
            smithsonian_max: Max results per Smithsonian query.
            fetch_nga: Whether to fetch from NGA open data.
            nga_max: Max NGA results to return.

        Returns:
            A ready-to-use ArtMarketApp instance.
        """
        self.load_seed_data()

        if fetch_met:
            self.load_met_listings(queries=met_queries, max_per_query=met_max)

        if fetch_smithsonian:
            self.load_smithsonian_listings(
                queries=smithsonian_queries,
                api_key=smithsonian_key,
                max_per_query=smithsonian_max,
            )

        if fetch_nga:
            self.load_nga_listings(max_results=nga_max)

        app = ArtMarketApp()
        app.load_houses(self.houses)
        app.load_auction_data(self.auction_records)
        if self.listings:
            app.load_listing_data(self.listings)

        return app
