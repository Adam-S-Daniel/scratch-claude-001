"""Tests for MarketGapDetector - finds undervalued categories, mediums, and periods."""
from datetime import date

from src.models import AuctionRecord, ArtListing
from src.repositories import AuctionRepository, ListingRepository
from src.gap_detector import MarketGapDetector, MarketGap


def _build_detector():
    auction_repo = AuctionRepository()
    listing_repo = ListingRepository()

    # Paintings - strong auction market, some underpriced listings
    for i, (title, artist, price, dt) in enumerate([
        ("Landscape A", "Artist A", 40000, date(2023, 6, 1)),
        ("Landscape B", "Artist B", 35000, date(2023, 9, 1)),
        ("Landscape C", "Artist A", 45000, date(2024, 1, 1)),
        ("Portrait X", "Artist C", 28000, date(2024, 3, 1)),
        ("Still Life", "Artist D", 15000, date(2024, 5, 1)),
    ]):
        auction_repo.add(AuctionRecord(
            str(i), title, artist, "oil on canvas", dt, price, "Freeman's", "painting"))

    # Decorative arts - moderate auction market
    for i, (title, artist, price, dt) in enumerate([
        ("Silver Teapot", "Maker A", 18000, date(2024, 2, 1)),
        ("Silver Bowl", "Maker B", 12000, date(2024, 4, 1)),
    ], start=10):
        auction_repo.add(AuctionRecord(
            str(i), title, artist, "silver", dt, price, "Weschler's", "decorative_arts"))

    # Furniture - sparse auction data but high values
    auction_repo.add(AuctionRecord(
        "20", "Federal Desk", "Unknown Maker", "mahogany",
        date(2024, 1, 15), 25000, "Freeman's", "furniture"))

    # Sculpture - no auction data (gap!)
    # (no records)

    # Listings
    listing_repo.add(ArtListing(
        "L1", "River Scene", "Artist A", "oil on canvas",
        20000, "Dealer X", "painting", date(2025, 1, 10)))  # Way below auction avg
    listing_repo.add(ArtListing(
        "L2", "Mountain View", "Artist B", "oil on canvas",
        38000, "Gallery Y", "painting", date(2025, 2, 1)))  # Close to auction
    listing_repo.add(ArtListing(
        "L3", "Silver Tray", "Maker A", "silver",
        8000, "Dealer Z", "decorative_arts", date(2025, 1, 20)))  # Below auction avg
    listing_repo.add(ArtListing(
        "L4", "Bronze Figure", "Sculptor X", "bronze",
        12000, "Gallery W", "sculpture", date(2025, 3, 1)))  # No auction comps
    listing_repo.add(ArtListing(
        "L5", "Sheraton Table", "Unknown Maker", "mahogany",
        9000, "Dealer V", "furniture", date(2025, 2, 15)))  # Well below auction

    return MarketGapDetector(auction_repo, listing_repo)


class TestMarketGapDetector:
    def test_find_category_gaps(self):
        """Categories where listing prices are well below auction averages."""
        detector = _build_detector()
        gaps = detector.find_category_gaps()
        assert len(gaps) >= 1
        for gap in gaps:
            assert isinstance(gap, MarketGap)
            assert gap.gap_pct > 0

    def test_category_gap_sorted_by_opportunity(self):
        detector = _build_detector()
        gaps = detector.find_category_gaps()
        pcts = [g.gap_pct for g in gaps]
        assert pcts == sorted(pcts, reverse=True)

    def test_find_medium_gaps(self):
        """Mediums where listing prices are below auction averages."""
        detector = _build_detector()
        gaps = detector.find_medium_gaps()
        assert len(gaps) >= 1

    def test_find_categories_with_no_auction_data(self):
        """Categories with current listings but no auction history - potential opportunities."""
        detector = _build_detector()
        untracked = detector.find_untracked_categories()
        assert "sculpture" in untracked

    def test_find_artist_gaps(self):
        """Artists whose listings are significantly below their auction averages."""
        detector = _build_detector()
        gaps = detector.find_artist_gaps(min_discount_pct=20)
        # Artist A: auction avg ~42500, listing at 20000 = ~53% discount
        assert len(gaps) >= 1
        artist_a = [g for g in gaps if g.segment == "Artist A"]
        assert len(artist_a) == 1
        assert artist_a[0].gap_pct > 40

    def test_overall_market_summary(self):
        detector = _build_detector()
        summary = detector.market_summary()
        assert "total_auction_records" in summary
        assert "total_listings" in summary
        assert "categories_tracked" in summary
        assert "avg_gap_pct" in summary

    def test_top_opportunities(self):
        """Get the top N most promising gaps across all dimensions."""
        detector = _build_detector()
        top = detector.top_opportunities(limit=3)
        assert len(top) <= 3
        assert all(isinstance(g, MarketGap) for g in top)
