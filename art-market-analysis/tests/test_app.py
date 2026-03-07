"""Tests for ArtMarketApp - the main orchestrator that ties everything together."""
from datetime import date

from src.app import ArtMarketApp


# Realistic mid-Atlantic auction data
HOUSES_DATA = [
    {"name": "Freeman's", "location": "Philadelphia, PA", "region": "mid-atlantic"},
    {"name": "Weschler's", "location": "Washington, DC", "region": "mid-atlantic"},
    {"name": "Brunk Auctions", "location": "Asheville, NC", "region": "mid-atlantic"},
    {"name": "Potomack Company", "location": "Alexandria, VA", "region": "mid-atlantic"},
    {"name": "Alderfer Auction", "location": "Hatfield, PA", "region": "mid-atlantic"},
    {"name": "Christie's", "location": "New York, NY", "region": "northeast"},
]

AUCTION_DATA = [
    {"lot_number": "101", "title": "View of the Delaware", "artist": "Thomas Birch",
     "medium": "oil on canvas", "date_sold": "2023-11-15", "hammer_price": 42000,
     "auction_house": "Freeman's", "category": "painting"},
    {"lot_number": "102", "title": "Philadelphia Harbor", "artist": "Thomas Birch",
     "medium": "oil on canvas", "date_sold": "2024-03-10", "hammer_price": 38000,
     "auction_house": "Freeman's", "category": "painting"},
    {"lot_number": "201", "title": "Portrait of a Statesman", "artist": "Charles Willson Peale",
     "medium": "oil on canvas", "date_sold": "2024-01-20", "hammer_price": 95000,
     "auction_house": "Freeman's", "category": "painting"},
    {"lot_number": "301", "title": "Shenandoah Valley", "artist": "Unknown Artist",
     "medium": "oil on canvas", "date_sold": "2024-02-15", "hammer_price": 8500,
     "auction_house": "Weschler's", "category": "painting"},
    {"lot_number": "302", "title": "Civil War Encampment", "artist": "Unidentified",
     "medium": "oil on panel", "date_sold": "2024-05-01", "hammer_price": 6200,
     "auction_house": "Weschler's", "category": "painting"},
    {"lot_number": "401", "title": "Philadelphia Chippendale Chair", "artist": "Unknown Maker",
     "medium": "mahogany", "date_sold": "2024-04-10", "hammer_price": 18500,
     "auction_house": "Freeman's", "category": "furniture"},
    {"lot_number": "501", "title": "Kirk Silver Repousse Pitcher", "artist": "Samuel Kirk",
     "medium": "silver", "date_sold": "2024-06-01", "hammer_price": 14000,
     "auction_house": "Potomack Company", "category": "decorative_arts"},
    {"lot_number": "502", "title": "Silver Serving Tray", "artist": "Unknown Maker",
     "medium": "silver", "date_sold": "2024-03-20", "hammer_price": 4800,
     "auction_house": "Brunk Auctions", "category": "decorative_arts"},
    {"lot_number": "601", "title": "Contemporary Sculpture", "artist": "David Smith",
     "medium": "steel", "date_sold": "2024-07-01", "hammer_price": 120000,
     "auction_house": "Christie's", "category": "sculpture"},
    {"lot_number": "701", "title": "Quilt, Star Pattern", "artist": "Anonymous",
     "medium": "textile", "date_sold": "2024-02-28", "hammer_price": 3200,
     "auction_house": "Alderfer Auction", "category": "textile"},
]

LISTING_DATA = [
    {"listing_id": "CL001", "title": "Delaware River Morning", "artist": "Thomas Birch",
     "medium": "oil on canvas", "asking_price": 25000, "source": "Schwarz Gallery",
     "category": "painting", "date_listed": "2025-01-15"},
    {"listing_id": "CL002", "title": "Schuylkill Landscape", "artist": "Thomas Birch",
     "medium": "oil on canvas", "asking_price": 48000, "source": "Online Dealer",
     "category": "painting", "date_listed": "2025-02-01"},
    {"listing_id": "CL003", "title": "Maryland Landscape", "artist": "Unknown Artist",
     "medium": "oil on canvas", "asking_price": 3500, "source": "Estate Sale",
     "category": "painting", "date_listed": "2025-01-20"},
    {"listing_id": "CL004", "title": "Virginia Gentleman Portrait", "artist": "Unidentified",
     "medium": "oil on canvas", "asking_price": 4200, "source": "Antique Shop",
     "category": "painting", "date_listed": "2025-02-10"},
    {"listing_id": "CL005", "title": "Federal Card Table", "artist": "Unknown Maker",
     "medium": "mahogany", "asking_price": 7500, "source": "M.S. Rau",
     "category": "furniture", "date_listed": "2025-03-01"},
    {"listing_id": "CL006", "title": "Kirk Silver Coffee Service", "artist": "Samuel Kirk",
     "medium": "silver", "asking_price": 9000, "source": "Spencer Marks",
     "category": "decorative_arts", "date_listed": "2025-02-20"},
    {"listing_id": "CL007", "title": "Pastoral with Figures", "artist": "Anonymous",
     "medium": "oil on panel", "asking_price": 1800, "source": "eBay",
     "category": "painting", "date_listed": "2025-01-25"},
]


def _build_app():
    app = ArtMarketApp()
    app.load_houses(HOUSES_DATA)
    app.load_auction_data(AUCTION_DATA)
    app.load_listing_data(LISTING_DATA)
    return app


class TestArtMarketApp:
    def test_load_data(self):
        app = _build_app()
        assert app.auction_count == 10
        assert app.listing_count == 7
        assert app.house_count == 6

    def test_mid_atlantic_tracking(self):
        app = _build_app()
        regional = app.get_regional_records()
        # Should exclude Christie's (northeast)
        assert len(regional) == 9
        houses = {r.auction_house for r in regional}
        assert "Christie's" not in houses

    def test_regional_summary(self):
        app = _build_app()
        summary = app.get_regional_summary()
        assert summary["total_records"] == 9
        assert summary["total_houses"] == 5

    def test_find_buying_opportunities(self):
        app = _build_app()
        opps = app.find_buying_opportunities()
        assert len(opps) >= 1
        # Thomas Birch listing at $25k vs avg auction ~$40k should appear
        birch_opps = [o for o in opps if o.listing.artist == "Thomas Birch"]
        assert len(birch_opps) >= 1

    def test_find_promising_unidentified(self):
        app = _build_app()
        promising = app.find_promising_unidentified_works()
        assert len(promising) >= 1
        for pw in promising:
            assert pw.listing.is_unidentified_artist
            assert len(pw.signals) > 0

    def test_find_market_gaps(self):
        app = _build_app()
        gaps = app.find_market_gaps()
        assert len(gaps) >= 1

    def test_compare_specific_artist(self):
        app = _build_app()
        comp = app.compare_artist("Thomas Birch")
        assert comp["num_auction_records"] == 2
        assert comp["avg_auction_price"] == 40000.0
        assert len(comp["underpriced"]) >= 1

    def test_full_report(self):
        """The full analysis report should have all sections."""
        app = _build_app()
        report = app.generate_report()
        assert "regional_summary" in report
        assert "buying_opportunities" in report
        assert "promising_unidentified" in report
        assert "market_gaps" in report
        assert "top_opportunities" in report

    def test_full_report_text(self):
        """Generate a human-readable text report."""
        app = _build_app()
        text = app.generate_text_report()
        assert "Mid-Atlantic Art Market Analysis" in text
        assert "BUYING OPPORTUNITIES" in text
        assert "UNIDENTIFIED ARTISTS" in text
        assert "MARKET GAPS" in text
