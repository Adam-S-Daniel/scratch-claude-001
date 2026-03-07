"""Tests for automated data loading from seed files and the Met Museum API."""
import json
import os
from datetime import date
from unittest.mock import patch, MagicMock

from src.data_loader import (
    DataLoader,
    load_seed_houses,
    load_seed_auction_records,
    fetch_met_artworks,
    met_object_to_listing,
)


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


class TestSeedDataFiles:
    """Verify seed data files exist and have correct structure."""

    def test_houses_file_exists(self):
        path = os.path.join(DATA_DIR, "houses.json")
        assert os.path.exists(path)

    def test_houses_file_has_mid_atlantic(self):
        houses = load_seed_houses()
        mid_atlantic = [h for h in houses if h["region"] == "mid-atlantic"]
        assert len(mid_atlantic) >= 5

    def test_houses_have_required_fields(self):
        houses = load_seed_houses()
        for h in houses:
            assert "name" in h
            assert "location" in h
            assert "region" in h

    def test_auction_records_file_exists(self):
        path = os.path.join(DATA_DIR, "auction_records.json")
        assert os.path.exists(path)

    def test_auction_records_have_required_fields(self):
        records = load_seed_auction_records()
        assert len(records) >= 20
        for r in records:
            assert "lot_number" in r
            assert "title" in r
            assert "artist" in r
            assert "medium" in r
            assert "date_sold" in r
            assert "hammer_price" in r
            assert "auction_house" in r
            assert "category" in r

    def test_auction_records_reference_known_houses(self):
        houses = load_seed_houses()
        house_names = {h["name"] for h in houses}
        records = load_seed_auction_records()
        for r in records:
            assert r["auction_house"] in house_names, (
                f"Record references unknown house: {r['auction_house']}"
            )

    def test_auction_records_have_varied_categories(self):
        records = load_seed_auction_records()
        categories = {r["category"] for r in records}
        assert len(categories) >= 3

    def test_auction_records_include_unidentified_artists(self):
        records = load_seed_auction_records()
        unidentified = [
            r for r in records
            if any(kw in r["artist"].lower() for kw in ["unknown", "unidentified", "anonymous"])
        ]
        assert len(unidentified) >= 3


class TestMetMuseumAPI:
    """Test Met Museum API integration with mocked HTTP calls."""

    SAMPLE_SEARCH_RESPONSE = {
        "total": 3,
        "objectIDs": [11050, 2688, 4895],
    }

    SAMPLE_OBJECT = {
        "objectID": 11050,
        "title": "Approaching Thunder Storm",
        "artistDisplayName": "Martin Johnson Heade",
        "medium": "Oil on canvas",
        "objectDate": "1859",
        "department": "The American Wing",
        "classification": "Paintings",
        "objectName": "Painting",
        "culture": "American",
        "isPublicDomain": True,
        "accessionYear": "1975",
    }

    SAMPLE_OBJECT_NO_ARTIST = {
        "objectID": 99999,
        "title": "Portrait of a Lady",
        "artistDisplayName": "",
        "medium": "Oil on canvas",
        "objectDate": "ca. 1820",
        "department": "The American Wing",
        "classification": "Paintings",
        "objectName": "Painting",
        "culture": "American",
        "isPublicDomain": True,
        "accessionYear": "1960",
    }

    def test_met_object_to_listing_basic(self):
        listing = met_object_to_listing(self.SAMPLE_OBJECT)
        assert listing["listing_id"] == "met-11050"
        assert listing["title"] == "Approaching Thunder Storm"
        assert listing["artist"] == "Martin Johnson Heade"
        assert listing["medium"] == "Oil on canvas"
        assert listing["source"] == "Metropolitan Museum of Art"
        assert listing["category"] == "painting"

    def test_met_object_to_listing_no_artist(self):
        listing = met_object_to_listing(self.SAMPLE_OBJECT_NO_ARTIST)
        assert listing["artist"] == "Unknown Artist"

    def test_met_object_to_listing_category_mapping(self):
        """Classification 'Paintings' should map to 'painting'."""
        listing = met_object_to_listing(self.SAMPLE_OBJECT)
        assert listing["category"] == "painting"

    def test_met_object_to_listing_furniture(self):
        obj = dict(self.SAMPLE_OBJECT, objectName="Table", classification="Furniture",
                   objectID=555, title="Card Table", medium="Mahogany")
        listing = met_object_to_listing(obj)
        assert listing["category"] == "furniture"

    def test_met_object_to_listing_silver(self):
        obj = dict(self.SAMPLE_OBJECT, objectName="Pitcher", classification="Silver",
                   objectID=556, title="Water Pitcher", medium="Silver")
        listing = met_object_to_listing(obj)
        assert listing["category"] == "decorative_arts"

    def test_met_object_to_listing_has_estimated_price(self):
        listing = met_object_to_listing(self.SAMPLE_OBJECT)
        assert "asking_price" in listing
        assert listing["asking_price"] > 0

    @patch("src.data_loader._fetch_json")
    def test_fetch_met_artworks_calls_api(self, mock_fetch):
        mock_fetch.side_effect = [
            self.SAMPLE_SEARCH_RESPONSE,
            self.SAMPLE_OBJECT,
            self.SAMPLE_OBJECT,
            self.SAMPLE_OBJECT,
        ]
        results = fetch_met_artworks(query="oil painting", max_results=3)
        assert len(results) == 3
        assert results[0]["title"] == "Approaching Thunder Storm"

    @patch("src.data_loader._fetch_json")
    def test_fetch_met_artworks_handles_empty_search(self, mock_fetch):
        mock_fetch.return_value = {"total": 0, "objectIDs": None}
        results = fetch_met_artworks(query="xyznonexistent", max_results=5)
        assert results == []

    @patch("src.data_loader._fetch_json")
    def test_fetch_met_artworks_handles_network_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("Network error")
        results = fetch_met_artworks(query="painting", max_results=5)
        assert results == []


class TestDataLoader:
    """Test the DataLoader orchestrator that combines all sources."""

    def test_load_seed_data(self):
        loader = DataLoader()
        loader.load_seed_data()
        assert loader.houses is not None
        assert len(loader.houses) >= 5
        assert len(loader.auction_records) >= 20

    def test_load_seed_populates_app(self):
        from src.app import ArtMarketApp
        loader = DataLoader()
        app = loader.load_into_app()
        assert app.house_count >= 5
        assert app.auction_count >= 20

    @patch("src.data_loader.fetch_met_artworks")
    def test_load_with_met_listings(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "listing_id": "met-11050",
                "title": "Approaching Thunder Storm",
                "artist": "Martin Johnson Heade",
                "medium": "Oil on canvas",
                "asking_price": 45000,
                "source": "Metropolitan Museum of Art",
                "category": "painting",
                "date_listed": date.today().isoformat(),
            },
        ]
        loader = DataLoader()
        app = loader.load_into_app(fetch_met=True, met_queries=["painting"], met_max=1)
        assert app.listing_count >= 1

    def test_load_seed_only_no_network(self):
        """Loading seed data should work without network access."""
        loader = DataLoader()
        app = loader.load_into_app(fetch_met=False)
        assert app.house_count >= 5
        assert app.auction_count >= 20
        assert app.listing_count == 0  # no listings without Met fetch
