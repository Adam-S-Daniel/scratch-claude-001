"""Tests for OpportunityAnalyzer - compares past sales with current listings."""
from datetime import date

from src.models import AuctionRecord, ArtListing
from src.repositories import AuctionRepository, ListingRepository
from src.opportunity import OpportunityAnalyzer, Opportunity


def _build_analyzer():
    auction_repo = AuctionRepository()
    listing_repo = ListingRepository()

    # Past sales
    auction_repo.add(AuctionRecord(
        "1", "Landscape with River", "Thomas Cole", "oil on canvas",
        date(2023, 6, 1), 50000, "Freeman's", "painting"))
    auction_repo.add(AuctionRecord(
        "2", "Landscape with Mountains", "Thomas Cole", "oil on canvas",
        date(2024, 1, 15), 55000, "Freeman's", "painting"))
    auction_repo.add(AuctionRecord(
        "3", "Silver Teapot", "Paul Revere", "silver",
        date(2024, 3, 10), 22000, "Weschler's", "decorative_arts"))
    auction_repo.add(AuctionRecord(
        "4", "Portrait of Lady", "Gilbert Stuart", "oil on canvas",
        date(2024, 5, 1), 80000, "Freeman's", "painting"))
    auction_repo.add(AuctionRecord(
        "5", "Small Landscape", "Unknown Artist", "oil on panel",
        date(2024, 2, 1), 1500, "Brunk Auctions", "painting"))

    # Current listings
    listing_repo.add(ArtListing(
        "L1", "Autumn Landscape", "Thomas Cole", "oil on canvas",
        35000, "Gallery A", "painting", date(2025, 1, 10)))  # Below avg auction price
    listing_repo.add(ArtListing(
        "L2", "Spring Landscape", "Thomas Cole", "oil on canvas",
        70000, "Gallery B", "painting", date(2025, 2, 1)))  # Above avg auction price
    listing_repo.add(ArtListing(
        "L3", "Silver Bowl", "Paul Revere", "silver",
        15000, "Dealer C", "decorative_arts", date(2025, 1, 20)))  # Below auction
    listing_repo.add(ArtListing(
        "L4", "Portrait Study", "Gilbert Stuart", "oil on canvas",
        90000, "Gallery D", "painting", date(2025, 3, 1)))  # Above auction
    listing_repo.add(ArtListing(
        "L5", "Rural Scene", "Unknown Artist", "oil on panel",
        800, "Dealer E", "painting", date(2025, 2, 15)))  # Below auction

    return OpportunityAnalyzer(auction_repo, listing_repo)


class TestOpportunityAnalyzer:
    def test_find_underpriced_listings(self):
        """Listings priced below avg past auction price for same artist."""
        analyzer = _build_analyzer()
        opportunities = analyzer.find_underpriced_listings()
        assert len(opportunities) >= 2
        # Thomas Cole listing at 35k vs avg 52.5k should appear
        cole_opps = [o for o in opportunities if o.listing.artist == "Thomas Cole"]
        assert len(cole_opps) == 1
        assert cole_opps[0].listing.asking_price == 35000

    def test_opportunity_has_discount_percentage(self):
        analyzer = _build_analyzer()
        opportunities = analyzer.find_underpriced_listings()
        for opp in opportunities:
            assert hasattr(opp, "discount_pct")
            assert opp.discount_pct > 0

    def test_opportunity_has_avg_auction_price(self):
        analyzer = _build_analyzer()
        opportunities = analyzer.find_underpriced_listings()
        for opp in opportunities:
            assert opp.avg_auction_price > 0

    def test_find_overpriced_listings(self):
        """Listings priced above avg past auction price for same artist."""
        analyzer = _build_analyzer()
        overpriced = analyzer.find_overpriced_listings()
        cole_over = [o for o in overpriced if o.listing.artist == "Thomas Cole"]
        assert len(cole_over) == 1
        assert cole_over[0].listing.asking_price == 70000

    def test_compare_artist_returns_comparison(self):
        analyzer = _build_analyzer()
        comp = analyzer.compare_artist("Thomas Cole")
        assert comp["artist"] == "Thomas Cole"
        assert comp["avg_auction_price"] == 52500.0
        assert comp["num_auction_records"] == 2
        assert len(comp["current_listings"]) == 2
        assert len(comp["underpriced"]) == 1
        assert len(comp["overpriced"]) == 1

    def test_compare_artist_not_found(self):
        analyzer = _build_analyzer()
        comp = analyzer.compare_artist("Nonexistent Artist")
        assert comp["num_auction_records"] == 0

    def test_get_all_opportunities_sorted(self):
        """Opportunities sorted by discount percentage descending."""
        analyzer = _build_analyzer()
        opportunities = analyzer.find_underpriced_listings()
        discounts = [o.discount_pct for o in opportunities]
        assert discounts == sorted(discounts, reverse=True)

    def test_price_gap_analysis_by_category(self):
        analyzer = _build_analyzer()
        gaps = analyzer.price_gap_by_category()
        assert "painting" in gaps
        assert "decorative_arts" in gaps
        # Each category should have avg auction price and avg listing price
        assert "avg_auction_price" in gaps["painting"]
        assert "avg_listing_price" in gaps["painting"]
