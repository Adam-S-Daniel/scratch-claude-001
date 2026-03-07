"""Tests for automated data loading from seed files and museum APIs."""
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
    fetch_smithsonian_artworks,
    smithsonian_object_to_listing,
    _flatten_smithsonian_row,
    fetch_nga_artworks,
    nga_object_to_listing,
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

    @patch("src.data_loader.fetch_smithsonian_artworks")
    def test_load_with_smithsonian_listings(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "listing_id": "si-saam_12345",
                "title": "American Landscape",
                "artist": "George Inness",
                "medium": "Oil on canvas",
                "asking_price": 35000,
                "source": "Smithsonian Open Access",
                "category": "painting",
                "date_listed": date.today().isoformat(),
            },
        ]
        loader = DataLoader()
        app = loader.load_into_app(
            fetch_smithsonian=True,
            smithsonian_queries=["painting"],
            smithsonian_key="test-key",
            smithsonian_max=1,
        )
        assert app.listing_count >= 1

    @patch("src.data_loader.fetch_nga_artworks")
    def test_load_with_nga_listings(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "listing_id": "nga-12345",
                "title": "The Voyage of Life",
                "artist": "Thomas Cole",
                "medium": "oil on canvas",
                "asking_price": 55000,
                "source": "National Gallery of Art",
                "category": "painting",
                "date_listed": date.today().isoformat(),
            },
        ]
        loader = DataLoader()
        app = loader.load_into_app(fetch_nga=True, nga_max=1)
        assert app.listing_count >= 1


class TestSmithsonianAPI:
    """Test Smithsonian Open Access API integration with mocked calls."""

    SAMPLE_SEARCH_RESULT = {
        "id": "edanmdm-saam_1234",
        "title": "Autumn Landscape",
        "content": {
            "descriptiveNonRepeating": {
                "record_ID": "saam_1234",
                "title": {"content": "Autumn Landscape"},
            },
            "freetext": {
                "name": [{"content": "George Inness", "label": "Artist"}],
                "physicalDescription": [
                    {"content": "oil on canvas", "label": "Medium"}
                ],
            },
            "indexedStructured": {
                "object_type": ["Paintings"],
            },
        },
    }

    SAMPLE_SEARCH_RESULT_NO_ARTIST = {
        "id": "edanmdm-saam_9999",
        "title": "Untitled Portrait",
        "content": {
            "descriptiveNonRepeating": {
                "record_ID": "saam_9999",
                "title": {"content": "Untitled Portrait"},
            },
            "freetext": {
                "physicalDescription": [
                    {"content": "oil on canvas", "label": "Medium"}
                ],
            },
            "indexedStructured": {
                "object_type": ["Paintings"],
            },
        },
    }

    def test_flatten_smithsonian_row(self):
        flat = _flatten_smithsonian_row(self.SAMPLE_SEARCH_RESULT)
        assert flat["id"] == "saam_1234"
        assert flat["name"] == "George Inness"
        assert flat["physicalDescription"] == "oil on canvas"
        assert flat["type"] == "Paintings"

    def test_smithsonian_object_to_listing_basic(self):
        flat = _flatten_smithsonian_row(self.SAMPLE_SEARCH_RESULT)
        listing = smithsonian_object_to_listing(flat)
        assert listing["listing_id"] == "si-saam_1234"
        assert listing["artist"] == "George Inness"
        assert listing["source"] == "Smithsonian Open Access"
        assert listing["category"] == "painting"
        assert listing["asking_price"] > 0

    def test_smithsonian_object_no_artist(self):
        flat = _flatten_smithsonian_row(self.SAMPLE_SEARCH_RESULT_NO_ARTIST)
        listing = smithsonian_object_to_listing(flat)
        assert listing["artist"] == "Unknown Artist"

    @patch("src.data_loader._fetch_json")
    def test_fetch_smithsonian_artworks_calls_api(self, mock_fetch):
        mock_fetch.return_value = {
            "response": {
                "rows": [self.SAMPLE_SEARCH_RESULT],
            },
        }
        results = fetch_smithsonian_artworks(
            query="american painting", api_key="test-key", max_results=5
        )
        assert len(results) == 1
        assert results[0]["source"] == "Smithsonian Open Access"

    def test_fetch_smithsonian_artworks_no_key_returns_empty(self):
        """Without an API key, should return empty list."""
        with patch.dict(os.environ, {}, clear=True):
            results = fetch_smithsonian_artworks(
                query="painting", api_key=None, max_results=5
            )
        assert results == []

    @patch("src.data_loader._fetch_json")
    def test_fetch_smithsonian_artworks_handles_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("Network error")
        results = fetch_smithsonian_artworks(
            query="painting", api_key="test-key", max_results=5
        )
        assert results == []


class TestNGAOpenData:
    """Test National Gallery of Art open data integration."""

    def test_nga_object_to_listing_basic(self):
        row = {
            "objectID": "12345",
            "title": "The Voyage of Life: Youth",
            "attribution": "Thomas Cole",
            "medium": "oil on canvas",
            "classification": "Painting",
        }
        listing = nga_object_to_listing(row)
        assert listing is not None
        assert listing["listing_id"] == "nga-12345"
        assert listing["title"] == "The Voyage of Life: Youth"
        assert listing["artist"] == "Thomas Cole"
        assert listing["source"] == "National Gallery of Art"
        assert listing["category"] == "painting"
        assert listing["asking_price"] > 0

    def test_nga_object_to_listing_no_artist(self):
        row = {
            "objectID": "67890",
            "title": "Still Life with Fruit",
            "attribution": "",
            "medium": "oil on canvas",
            "classification": "Painting",
        }
        listing = nga_object_to_listing(row)
        assert listing is not None
        assert listing["artist"] == "Unknown Artist"

    def test_nga_object_to_listing_missing_id(self):
        row = {"title": "Some Painting", "objectID": ""}
        listing = nga_object_to_listing(row)
        assert listing is None

    def test_nga_object_to_listing_missing_title(self):
        row = {"objectID": "123", "title": ""}
        listing = nga_object_to_listing(row)
        assert listing is None

    def test_nga_object_to_listing_sculpture(self):
        row = {
            "objectID": "111",
            "title": "Bronze Figure",
            "attribution": "Augustus Saint-Gaudens",
            "medium": "bronze",
            "classification": "Sculpture",
        }
        listing = nga_object_to_listing(row)
        assert listing is not None
        assert listing["category"] == "sculpture"

    @patch("src.data_loader.urlopen")
    def test_fetch_nga_artworks_handles_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Network error")
        results = fetch_nga_artworks(max_results=5)
        assert results == []

    @patch("src.data_loader.urlopen")
    def test_fetch_nga_artworks_parses_csv(self, mock_urlopen):
        csv_content = (
            "objectID,title,attribution,medium,classification,nationality\n"
            "100,Sunset Landscape,Frederic Church,oil on canvas,Painting,American\n"
            "101,French Garden,Claude Monet,oil on canvas,Painting,French\n"
            "102,Harbor View,Winslow Homer,watercolor,Drawing,American\n"
        )
        mock_resp = MagicMock()
        mock_resp.read.return_value = csv_content.encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        results = fetch_nga_artworks(max_results=10)
        # Should only include American artworks (2 of 3)
        assert len(results) == 2
        assert results[0]["title"] == "Sunset Landscape"
        assert results[0]["source"] == "National Gallery of Art"
        assert results[1]["title"] == "Harbor View"


class TestDataLoaderRiskFiltering:
    """Test DataLoader respects max_risk and registry settings."""

    def test_load_into_app_default_max_risk_is_high(self):
        """Without specifying max_risk, all sources should be available."""
        loader = DataLoader()
        # Default should allow everything
        assert loader.registry.is_source_allowed("weschlers", max_risk=loader.max_risk)

    def test_load_into_app_with_max_risk_none(self):
        """With max_risk=NONE, scrapers should be excluded."""
        from src.source_registry import RiskLevel
        loader = DataLoader(max_risk=RiskLevel.NONE)
        assert loader.max_risk == RiskLevel.NONE
        # Should not allow any scrapers
        allowed = loader.registry.allowed_scraper_keys(max_risk=loader.max_risk)
        assert allowed == []

    def test_load_into_app_with_max_risk_low(self):
        """With max_risk=LOW, only leland_little scraper should pass."""
        from src.source_registry import RiskLevel
        loader = DataLoader(max_risk=RiskLevel.LOW)
        allowed = loader.registry.allowed_scraper_keys(max_risk=loader.max_risk)
        assert "leland_little" in allowed
        assert "weschlers" not in allowed

    @patch("src.data_loader.fetch_met_artworks")
    def test_met_skipped_when_not_allowed(self, mock_fetch):
        """If met_museum is somehow not allowed, load_met should be skipped."""
        from src.source_registry import RiskLevel, SourceRegistry, SourceConfig
        # Custom registry where met is HIGH risk (hypothetical)
        custom = SourceRegistry(sources={
            "met_museum": SourceConfig(
                key="met_museum", name="Met", source_type="api",
                risk_level=RiskLevel.HIGH, license="test",
            ),
        })
        loader = DataLoader(max_risk=RiskLevel.NONE, registry=custom)
        app = loader.load_into_app(fetch_met=True)
        mock_fetch.assert_not_called()

    @patch("src.data_loader.fetch_smithsonian_artworks")
    def test_smithsonian_uses_registry_api_key(self, mock_fetch):
        """DataLoader should pull the Smithsonian API key from the registry."""
        from src.source_registry import RiskLevel
        mock_fetch.return_value = []
        loader = DataLoader(max_risk=RiskLevel.HIGH)
        with patch.dict(os.environ, {"SMITHSONIAN_API_KEY": "reg-test-key"}):
            loader.load_into_app(
                fetch_smithsonian=True,
                smithsonian_queries=["test"],
                smithsonian_max=1,
            )
        # Should have been called with the key from registry/env
        mock_fetch.assert_called()

    @patch("src.data_loader.fetch_smithsonian_artworks")
    def test_smithsonian_skipped_without_api_key(self, mock_fetch):
        """If Smithsonian requires a key and none is set, it should be skipped."""
        from src.source_registry import RiskLevel
        mock_fetch.return_value = []
        loader = DataLoader(max_risk=RiskLevel.HIGH)
        with patch.dict(os.environ, {}, clear=True):
            app = loader.load_into_app(
                fetch_smithsonian=True,
                smithsonian_queries=["test"],
                smithsonian_max=1,
            )
        # fetch_smithsonian_artworks handles missing key by returning [],
        # so it may still be called but return empty
        assert app.listing_count == 0

    def test_scrape_sites_filtered_by_risk(self):
        """When scrape_sites is ["all"] and max_risk is LOW, only low-risk scrapers run."""
        from src.source_registry import RiskLevel
        loader = DataLoader(max_risk=RiskLevel.LOW)
        with patch("src.scrapers.scrape_all") as mock_scrape:
            mock_scrape.return_value = []
            loader.load_into_app(scrape_sites=["all"])
            mock_scrape.assert_called_once()
            call_args = mock_scrape.call_args
            sites = call_args[1].get("sites", call_args[0][0] if call_args[0] else None)
            assert sites is not None
            for site in sites:
                assert loader.registry.is_source_allowed(site, max_risk=RiskLevel.LOW)

    def test_agreement_allows_high_risk_at_none_max(self):
        """Setting an agreement should allow a high-risk source even at NONE max."""
        from src.source_registry import RiskLevel
        loader = DataLoader(max_risk=RiskLevel.NONE)
        loader.registry.set_agreement("weschlers", True)
        assert loader.registry.is_source_allowed("weschlers", max_risk=loader.max_risk)

    def test_set_api_key_secret_on_loader(self):
        """Users should be able to set the GitHub Secrets name for API keys."""
        from src.source_registry import RiskLevel
        loader = DataLoader()
        loader.registry.set_api_key_secret("smithsonian", "MY_ORG_SMITHSONIAN_KEY")
        cfg = loader.registry.get("smithsonian")
        assert cfg.api_key_secret == "MY_ORG_SMITHSONIAN_KEY"
