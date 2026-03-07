"""Tests for MidAtlanticAuctionTracker."""
from datetime import date

from src.models import AuctionHouse, AuctionRecord
from src.repositories import AuctionRepository
from src.tracker import MidAtlanticAuctionTracker


MID_ATLANTIC_HOUSES = [
    AuctionHouse("Freeman's", "Philadelphia, PA", "mid-atlantic"),
    AuctionHouse("Weschler's", "Washington, DC", "mid-atlantic"),
    AuctionHouse("Brunk Auctions", "Asheville, NC", "mid-atlantic"),
    AuctionHouse("Potomack Company", "Alexandria, VA", "mid-atlantic"),
    AuctionHouse("Alderfer Auction", "Hatfield, PA", "mid-atlantic"),
]


def _build_tracker():
    repo = AuctionRepository()
    for h in MID_ATLANTIC_HOUSES:
        repo.add_house(h)
    # Also add a non-mid-atlantic house
    repo.add_house(AuctionHouse("Christie's", "New York, NY", "northeast"))

    records = [
        AuctionRecord("1", "Landscape", "Thomas Cole", "oil on canvas",
                       date(2024, 3, 1), 45000, "Freeman's", "painting"),
        AuctionRecord("2", "Portrait", "Unknown Artist", "oil on canvas",
                       date(2024, 4, 15), 2500, "Weschler's", "painting"),
        AuctionRecord("3", "Silver Teapot", "Paul Revere", "silver",
                       date(2024, 5, 10), 18000, "Freeman's", "decorative_arts"),
        AuctionRecord("4", "Abstract", "Unidentified", "oil on panel",
                       date(2023, 11, 1), 1200, "Brunk Auctions", "painting"),
        AuctionRecord("5", "Modern Piece", "David Smith", "steel",
                       date(2024, 6, 1), 95000, "Christie's", "sculpture"),
        AuctionRecord("6", "Quilt", "Anonymous", "textile",
                       date(2024, 2, 20), 3500, "Potomack Company", "decorative_arts"),
        AuctionRecord("7", "Chest of Drawers", "Unknown Maker", "wood",
                       date(2024, 7, 1), 12000, "Alderfer Auction", "furniture"),
    ]
    for r in records:
        repo.add(r)
    return MidAtlanticAuctionTracker(repo)


class TestMidAtlanticAuctionTracker:
    def test_get_mid_atlantic_houses(self):
        tracker = _build_tracker()
        houses = tracker.get_tracked_houses()
        assert len(houses) == 5
        names = {h.name for h in houses}
        assert "Christie's" not in names
        assert "Freeman's" in names

    def test_get_mid_atlantic_records(self):
        tracker = _build_tracker()
        records = tracker.get_regional_records()
        # Should exclude Christie's (northeast) record
        assert len(records) == 6
        houses = {r.auction_house for r in records}
        assert "Christie's" not in houses

    def test_get_records_by_category(self):
        tracker = _build_tracker()
        paintings = tracker.get_records_by_category("painting")
        assert len(paintings) == 3

    def test_get_records_by_date_range(self):
        tracker = _build_tracker()
        recent = tracker.get_records_by_date_range(date(2024, 1, 1), date(2024, 12, 31))
        assert len(recent) == 5  # excludes the 2023 record and the Christie's record

    def test_summary_statistics(self):
        tracker = _build_tracker()
        stats = tracker.get_summary_stats()
        assert stats["total_records"] == 6
        assert stats["total_houses"] == 5
        assert "avg_price" in stats
        assert "categories" in stats
        assert "painting" in stats["categories"]

    def test_top_categories(self):
        tracker = _build_tracker()
        top = tracker.get_top_categories(limit=2)
        # painting (3 records) and decorative_arts (2 records) should be top 2
        assert len(top) == 2
        assert top[0][0] == "painting"
        assert top[0][1] == 3
