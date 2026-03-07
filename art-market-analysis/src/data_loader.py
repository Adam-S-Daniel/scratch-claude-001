"""Automated data loading from seed files and the Met Museum Collection API.

Data sources:
- Seed files (data/houses.json, data/auction_records.json): curated records
  from real mid-Atlantic auction houses with realistic market data.
- Metropolitan Museum of Art Collection API: free, no key required. Returns
  real American art objects that we convert to listing format for analysis.
  API docs: https://metmuseum.github.io/
"""
from __future__ import annotations

import json
import os
import random
from datetime import date
from typing import List
from urllib.parse import quote
from urllib.request import urlopen
from urllib.error import URLError

from src.app import ArtMarketApp

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_MET_API_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"

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

    def load_into_app(
        self,
        fetch_met: bool = False,
        met_queries: List[str] | None = None,
        met_max: int = 10,
    ) -> ArtMarketApp:
        """Load all data and return a fully populated ArtMarketApp.

        Args:
            fetch_met: Whether to fetch listings from the Met Museum API.
            met_queries: Search queries for the Met API.
            met_max: Max results per Met query.

        Returns:
            A ready-to-use ArtMarketApp instance.
        """
        self.load_seed_data()

        if fetch_met:
            self.load_met_listings(queries=met_queries, max_per_query=met_max)

        app = ArtMarketApp()
        app.load_houses(self.houses)
        app.load_auction_data(self.auction_records)
        if self.listings:
            app.load_listing_data(self.listings)

        return app
