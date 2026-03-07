"""Tests for UnidentifiedArtistAnalyzer - finds promising works by unknown artists."""
from datetime import date

from src.models import AuctionRecord, ArtListing
from src.repositories import AuctionRepository, ListingRepository
from src.unidentified import UnidentifiedArtistAnalyzer, PromisingWork


def _build_analyzer():
    auction_repo = AuctionRepository()
    listing_repo = ListingRepository()

    # Past auction sales by unidentified artists
    auction_repo.add(AuctionRecord(
        "1", "Hudson River Landscape", "Unknown Artist", "oil on canvas",
        date(2023, 3, 1), 8500, "Freeman's", "painting"))
    auction_repo.add(AuctionRecord(
        "2", "Portrait of a Gentleman", "Unidentified", "oil on canvas",
        date(2023, 6, 15), 12000, "Weschler's", "painting"))
    auction_repo.add(AuctionRecord(
        "3", "Still Life with Flowers", "Anonymous", "oil on panel",
        date(2024, 1, 10), 6000, "Brunk Auctions", "painting"))
    auction_repo.add(AuctionRecord(
        "4", "Rural Scene", "Unknown Artist", "oil on canvas",
        date(2024, 4, 1), 3200, "Potomack Company", "painting"))
    auction_repo.add(AuctionRecord(
        "5", "Chippendale Chair", "Unknown Maker", "mahogany",
        date(2024, 5, 1), 4500, "Freeman's", "furniture"))
    # Known artist for contrast
    auction_repo.add(AuctionRecord(
        "6", "Landscape", "Thomas Cole", "oil on canvas",
        date(2024, 2, 1), 55000, "Freeman's", "painting"))

    # Current listings by unidentified artists
    listing_repo.add(ArtListing(
        "L1", "River View at Sunset", "Unknown Artist", "oil on canvas",
        2500, "Dealer A", "painting", date(2025, 1, 10)))
    listing_repo.add(ArtListing(
        "L2", "Gentleman Portrait Study", "Unidentified", "oil on canvas",
        3000, "Dealer B", "painting", date(2025, 2, 5)))
    listing_repo.add(ArtListing(
        "L3", "Floral Arrangement", "Anonymous", "oil on panel",
        1500, "Dealer C", "painting", date(2025, 1, 20)))
    listing_repo.add(ArtListing(
        "L4", "Federal Side Table", "Unknown Maker", "cherry",
        800, "Dealer D", "furniture", date(2025, 3, 1)))
    # Known artist listing
    listing_repo.add(ArtListing(
        "L5", "Mountain Scene", "Thomas Cole", "oil on canvas",
        45000, "Gallery E", "painting", date(2025, 2, 15)))

    return UnidentifiedArtistAnalyzer(auction_repo, listing_repo)


class TestUnidentifiedArtistAnalyzer:
    def test_get_unidentified_auction_records(self):
        analyzer = _build_analyzer()
        records = analyzer.get_unidentified_auction_records()
        assert len(records) == 5
        for r in records:
            assert r.is_unidentified_artist

    def test_get_unidentified_listings(self):
        analyzer = _build_analyzer()
        listings = analyzer.get_unidentified_listings()
        assert len(listings) == 4
        for l in listings:
            assert l.is_unidentified_artist

    def test_find_promising_by_high_past_value(self):
        """Works by unidentified artists that sold well at auction previously,
        suggesting quality or period significance."""
        analyzer = _build_analyzer()
        promising = analyzer.find_promising_works(min_past_sale=5000)
        # Should find listings in categories where unidentified works sold >= 5000
        assert len(promising) >= 1
        for pw in promising:
            assert isinstance(pw, PromisingWork)
            assert pw.listing.is_unidentified_artist

    def test_promising_work_has_signals(self):
        """Each promising work should have signals explaining why it's promising."""
        analyzer = _build_analyzer()
        promising = analyzer.find_promising_works(min_past_sale=3000)
        for pw in promising:
            assert len(pw.signals) > 0

    def test_promising_work_has_comparable_sales(self):
        analyzer = _build_analyzer()
        promising = analyzer.find_promising_works(min_past_sale=3000)
        for pw in promising:
            assert pw.comparable_avg_price > 0

    def test_find_promising_by_medium_match(self):
        """Listings that share medium with high-value unidentified auction results."""
        analyzer = _build_analyzer()
        promising = analyzer.find_promising_by_medium(min_past_sale=5000)
        # oil on canvas unidentified works sold for 8500 and 12000
        # listings L1 and L2 are oil on canvas by unidentified artists
        oil_canvas = [p for p in promising if p.listing.medium == "oil on canvas"]
        assert len(oil_canvas) >= 2

    def test_category_value_summary(self):
        """Summary of unidentified artist value by category."""
        analyzer = _build_analyzer()
        summary = analyzer.unidentified_category_summary()
        assert "painting" in summary
        assert summary["painting"]["avg_auction_price"] > 0
        assert summary["painting"]["num_auction_records"] > 0
        assert summary["painting"]["num_listings"] > 0

    def test_score_listing(self):
        """Score a specific listing based on how promising it is."""
        analyzer = _build_analyzer()
        listings = analyzer.get_unidentified_listings()
        score = analyzer.score_listing(listings[0])
        assert 0 <= score <= 100
