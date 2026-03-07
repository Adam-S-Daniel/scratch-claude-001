"""Tests for auction house web scrapers."""
from unittest.mock import patch, MagicMock

from src.scrapers import (
    _classify_from_text,
    _extract_artist,
    _parse_price,
    _lot_dict_to_record,
    _LotHTMLParser,
    scrape_leland_little,
    scrape_weschlers,
    scrape_all,
    SCRAPERS,
)


class TestClassifyFromText:
    """Test category classification from descriptive text."""

    def test_painting_oil_on_canvas(self):
        assert _classify_from_text("Oil on canvas landscape") == "painting"

    def test_painting_acrylic(self):
        assert _classify_from_text("Acrylic on board") == "painting"

    def test_works_on_paper_watercolor(self):
        assert _classify_from_text("Watercolor on paper") == "works_on_paper"

    def test_works_on_paper_lithograph(self):
        assert _classify_from_text("Lithograph, signed") == "works_on_paper"

    def test_furniture_table(self):
        assert _classify_from_text("Federal Card Table") == "furniture"

    def test_furniture_mahogany(self):
        assert _classify_from_text("Mahogany chest of drawers") == "furniture"

    def test_decorative_arts_silver(self):
        assert _classify_from_text("Sterling Silver Tea Set") == "decorative_arts"

    def test_decorative_arts_porcelain(self):
        assert _classify_from_text("Chinese Export Porcelain Vase") == "decorative_arts"

    def test_textile_quilt(self):
        assert _classify_from_text("Amish Star Quilt") == "textile"

    def test_sculpture_bronze(self):
        assert _classify_from_text("Bronze figure of a horse") == "sculpture"

    def test_unknown_defaults_decorative_arts(self):
        assert _classify_from_text("misc household item") == "decorative_arts"


class TestExtractArtist:
    """Test artist name extraction from lot titles."""

    def test_artist_with_dates(self):
        assert _extract_artist("Thomas Birch (American, 1779-1851), River View") == "Thomas Birch"

    def test_artist_with_comma_title(self):
        assert _extract_artist("John Smith, Portrait of a Lady") == "John Smith"

    def test_no_artist_pattern(self):
        assert _extract_artist("Antique Silver Teapot") == "Unknown Artist"

    def test_single_word_not_artist(self):
        assert _extract_artist("Landscape, Oil on Canvas") == "Unknown Artist"

    def test_empty_string(self):
        assert _extract_artist("") == "Unknown Artist"

    def test_artist_with_nationality(self):
        assert _extract_artist("Charles Peale (1741-1827), George Washington") == "Charles Peale"


class TestParsePrice:
    """Test price string parsing."""

    def test_dollar_sign(self):
        assert _parse_price("$1,500") == 1500.0

    def test_plain_number(self):
        assert _parse_price("2500") == 2500.0

    def test_with_usd(self):
        assert _parse_price("USD 3,200") == 3200.0

    def test_with_decimal(self):
        assert _parse_price("$1,500.50") == 1500.50

    def test_empty_string(self):
        assert _parse_price("") is None

    def test_none(self):
        assert _parse_price(None) is None

    def test_no_digits(self):
        assert _parse_price("not a price") is None


class TestLotDictToRecord:
    """Test conversion of parsed lot dicts to auction record format."""

    def test_basic_conversion(self):
        lot = {
            "title": "River Landscape",
            "price": "$5,000",
            "lot_number": "42",
            "description": "oil on canvas",
        }
        record = _lot_dict_to_record(lot, "Test House", "2024-06-01")
        assert record["title"] == "River Landscape"
        assert record["hammer_price"] == 5000.0
        assert record["lot_number"] == "42"
        assert record["auction_house"] == "Test House"
        assert record["category"] == "painting"
        assert record["date_sold"] == "2024-06-01"

    def test_with_artist_field(self):
        lot = {"title": "Sunset", "artist": "John Smith", "price": "$1,000"}
        record = _lot_dict_to_record(lot, "Test House")
        assert record["artist"] == "John Smith"

    def test_extracts_artist_from_title(self):
        lot = {"title": "Thomas Cole (American, 1801-1848), Mountain View", "price": "$50,000"}
        record = _lot_dict_to_record(lot, "Test House")
        assert record["artist"] == "Thomas Cole"

    def test_no_price_returns_empty(self):
        lot = {"title": "Some Item"}
        record = _lot_dict_to_record(lot, "Test House")
        assert record == {}

    def test_zero_price_returns_empty(self):
        lot = {"title": "Some Item", "price": "$0"}
        record = _lot_dict_to_record(lot, "Test House")
        assert record == {}

    def test_defaults_date_to_today(self):
        lot = {"title": "Item", "price": "$100"}
        record = _lot_dict_to_record(lot, "Test House")
        assert "date_sold" in record
        assert len(record["date_sold"]) == 10  # ISO date format


class TestLotHTMLParser:
    """Test the generic HTML lot parser."""

    def test_parses_lot_items(self):
        html = """
        <div class="lot-item">
            <span class="lot-title">Silver Teapot</span>
            <span class="lot-price">$2,500</span>
            <span class="lot-number">15</span>
        </div>
        <div class="lot-item">
            <span class="lot-title">Oil Painting</span>
            <span class="lot-price">$8,000</span>
        </div>
        """
        parser = _LotHTMLParser()
        parser.feed(html)
        parser.close()
        assert len(parser.lots) == 2
        assert parser.lots[0]["title"] == "Silver Teapot"
        assert parser.lots[0]["price"] == "$2,500"
        assert parser.lots[0]["lot_number"] == "15"
        assert parser.lots[1]["title"] == "Oil Painting"

    def test_handles_empty_html(self):
        parser = _LotHTMLParser()
        parser.feed("<html><body></body></html>")
        parser.close()
        assert parser.lots == []

    def test_handles_auction_lot_class(self):
        html = """
        <div class="auction-lot">
            <h3 class="item-title">Federal Sideboard</h3>
            <span class="price">$12,000</span>
        </div>
        """
        parser = _LotHTMLParser()
        parser.feed(html)
        parser.close()
        assert len(parser.lots) == 1
        assert parser.lots[0]["title"] == "Federal Sideboard"


class TestScrapeLelandLittle:
    """Test Leland Little scraper with mocked API."""

    @patch("src.scrapers._fetch_json_api")
    def test_parses_api_response(self, mock_fetch):
        mock_fetch.return_value = {
            "data": [
                {
                    "title": "Mountain Landscape",
                    "artist": "Thomas Doughty",
                    "medium": "oil on canvas",
                    "hammer_price": 25000,
                    "lot_number": "101",
                    "sale_date": "2024-06-15",
                },
                {
                    "title": "Silver Coffee Service",
                    "maker": "Kirk & Son",
                    "medium": "silver",
                    "sold_price": 8500,
                    "lot": "102",
                    "date": "2024-06-15",
                },
            ]
        }
        results = scrape_leland_little(max_results=10)
        assert len(results) == 2
        assert results[0]["title"] == "Mountain Landscape"
        assert results[0]["artist"] == "Thomas Doughty"
        assert results[0]["hammer_price"] == 25000
        assert results[0]["auction_house"] == "Leland Little Auctions"
        assert results[0]["category"] == "painting"
        assert results[1]["title"] == "Silver Coffee Service"
        assert results[1]["hammer_price"] == 8500

    @patch("src.scrapers._fetch_json_api")
    def test_handles_empty_response(self, mock_fetch):
        mock_fetch.return_value = {"data": []}
        results = scrape_leland_little(max_results=10)
        assert results == []

    @patch("src.scrapers._fetch_json_api")
    def test_handles_network_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("Connection refused")
        results = scrape_leland_little(max_results=10)
        assert results == []

    @patch("src.scrapers._fetch_json_api")
    def test_skips_lots_without_price(self, mock_fetch):
        mock_fetch.return_value = {
            "data": [
                {"title": "Item A", "hammer_price": 5000},
                {"title": "Item B"},  # no price
                {"title": "Item C", "hammer_price": 0},  # zero price
            ]
        }
        results = scrape_leland_little(max_results=10)
        assert len(results) == 1


class TestScrapeWeschlers:
    """Test Weschler's scraper with mocked HTML."""

    @patch("src.scrapers._fetch_html")
    def test_parses_html_results(self, mock_fetch):
        mock_fetch.return_value = """
        <div class="lot-item">
            <span class="lot-title">Chippendale Desk</span>
            <span class="lot-price">$15,000</span>
            <span class="lot-number">45</span>
            <span class="description">mahogany</span>
        </div>
        """
        results = scrape_weschlers(max_results=10)
        assert len(results) == 1
        assert results[0]["title"] == "Chippendale Desk"
        assert results[0]["hammer_price"] == 15000
        assert results[0]["auction_house"] == "Weschler's"
        assert results[0]["category"] == "furniture"

    @patch("src.scrapers._fetch_html")
    def test_handles_network_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("Network error")
        results = scrape_weschlers(max_results=10)
        assert results == []


class TestScrapeAll:
    """Test the scrape_all orchestrator."""

    def test_runs_selected_scrapers(self):
        mock_leland = MagicMock(return_value=[{"lot_number": "1", "title": "A"}])
        mock_weschlers = MagicMock(return_value=[{"lot_number": "2", "title": "B"}])

        with patch.dict(SCRAPERS, {
            "leland_little": {**SCRAPERS["leland_little"], "function": mock_leland},
            "weschlers": {**SCRAPERS["weschlers"], "function": mock_weschlers},
        }):
            results = scrape_all(sites=["leland_little", "weschlers"], max_per_site=10)
        assert len(results) == 2
        mock_leland.assert_called_once_with(max_results=10)
        mock_weschlers.assert_called_once_with(max_results=10)

    def test_skips_unknown_sites(self):
        mock_leland = MagicMock(return_value=[])
        with patch.dict(SCRAPERS, {
            "leland_little": {**SCRAPERS["leland_little"], "function": mock_leland},
        }):
            results = scrape_all(sites=["leland_little", "nonexistent"], max_per_site=5)
        assert results == []
        mock_leland.assert_called_once()

    def test_all_scrapers_registered(self):
        assert "leland_little" in SCRAPERS
        assert "weschlers" in SCRAPERS
        assert "quinns" in SCRAPERS
        assert "alex_cooper" in SCRAPERS
        assert "hilliard" in SCRAPERS
        assert "potomack" in SCRAPERS
        assert "bunch" in SCRAPERS
        assert "headleys" in SCRAPERS
        assert "ctbids" in SCRAPERS
        assert len(SCRAPERS) == 9


class TestDataLoaderScrapeIntegration:
    """Test scraper integration with DataLoader."""

    @patch("src.scrapers.scrape_all")
    def test_load_scraped_records(self, mock_scrape):
        mock_scrape.return_value = [
            {
                "lot_number": "1",
                "title": "Test Painting",
                "artist": "Test Artist",
                "medium": "oil on canvas",
                "date_sold": "2024-06-01",
                "hammer_price": 10000,
                "auction_house": "Leland Little Auctions",
                "category": "painting",
            }
        ]
        from src.data_loader import DataLoader
        loader = DataLoader()
        app = loader.load_into_app(
            scrape_sites=["leland_little"],
            scrape_max=10,
        )
        # Should have seed records + 1 scraped record
        assert app.auction_count >= 39  # 38 seed + 1 scraped
