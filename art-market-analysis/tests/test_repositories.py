"""Tests for AuctionRepository and ListingRepository."""
from datetime import date

from src.models import AuctionHouse, AuctionRecord, ArtListing
from src.repositories import AuctionRepository, ListingRepository


def _sample_houses():
    return [
        AuctionHouse("Freeman's", "Philadelphia, PA", "mid-atlantic"),
        AuctionHouse("Weschler's", "Washington, DC", "mid-atlantic"),
        AuctionHouse("Brunk Auctions", "Asheville, NC", "mid-atlantic"),
        AuctionHouse("Christie's", "New York, NY", "northeast"),
    ]


def _sample_records():
    return [
        AuctionRecord("1", "Landscape", "Thomas Cole", "oil on canvas",
                       date(2024, 3, 1), 45000, "Freeman's", "painting"),
        AuctionRecord("2", "Portrait", "Unknown Artist", "oil on canvas",
                       date(2024, 4, 15), 2500, "Weschler's", "painting"),
        AuctionRecord("3", "Silver Teapot", "Paul Revere", "silver",
                       date(2024, 5, 10), 18000, "Freeman's", "decorative_arts"),
        AuctionRecord("4", "Landscape", "Unidentified", "oil on panel",
                       date(2023, 11, 1), 1200, "Brunk Auctions", "painting"),
        AuctionRecord("5", "Modern Sculpture", "David Smith", "steel",
                       date(2024, 6, 1), 95000, "Christie's", "sculpture"),
    ]


def _sample_listings():
    return [
        ArtListing("L1", "River Scene", "Thomas Cole", "oil on canvas",
                   55000, "Gallery A", "painting", date(2025, 1, 10)),
        ArtListing("L2", "Floral Still Life", "Unknown Artist", "oil on panel",
                   4000, "Dealer B", "painting", date(2025, 2, 5)),
        ArtListing("L3", "Silver Bowl", "Unknown", "silver",
                   8000, "Dealer C", "decorative_arts", date(2025, 1, 20)),
        ArtListing("L4", "Abstract #7", "David Smith", "steel",
                   110000, "Gallery D", "sculpture", date(2025, 3, 1)),
    ]


class TestAuctionRepository:
    def test_add_and_get_all(self):
        repo = AuctionRepository()
        records = _sample_records()
        for r in records:
            repo.add(r)
        assert len(repo.get_all()) == 5

    def test_get_by_auction_house(self):
        repo = AuctionRepository()
        for r in _sample_records():
            repo.add(r)
        freemans = repo.get_by_auction_house("Freeman's")
        assert len(freemans) == 2

    def test_get_by_category(self):
        repo = AuctionRepository()
        for r in _sample_records():
            repo.add(r)
        paintings = repo.get_by_category("painting")
        assert len(paintings) == 3

    def test_get_by_artist(self):
        repo = AuctionRepository()
        for r in _sample_records():
            repo.add(r)
        cole = repo.get_by_artist("Thomas Cole")
        assert len(cole) == 1
        assert cole[0].hammer_price == 45000

    def test_get_unidentified(self):
        repo = AuctionRepository()
        for r in _sample_records():
            repo.add(r)
        unid = repo.get_unidentified()
        assert len(unid) == 2

    def test_get_by_date_range(self):
        repo = AuctionRepository()
        for r in _sample_records():
            repo.add(r)
        results = repo.get_by_date_range(date(2024, 1, 1), date(2024, 4, 30))
        assert len(results) == 2

    def test_add_house_and_get_houses(self):
        repo = AuctionRepository()
        for h in _sample_houses():
            repo.add_house(h)
        assert len(repo.get_houses()) == 4

    def test_get_houses_by_region(self):
        repo = AuctionRepository()
        for h in _sample_houses():
            repo.add_house(h)
        mid_atl = repo.get_houses_by_region("mid-atlantic")
        assert len(mid_atl) == 3

    def test_load_records_from_dicts(self):
        repo = AuctionRepository()
        data = [
            {"lot_number": "10", "title": "Test", "artist": "A", "medium": "oil",
             "date_sold": "2024-01-01", "hammer_price": 100, "auction_house": "X",
             "category": "painting"},
        ]
        repo.load_records(data)
        assert len(repo.get_all()) == 1


class TestListingRepository:
    def test_add_and_get_all(self):
        repo = ListingRepository()
        for l in _sample_listings():
            repo.add(l)
        assert len(repo.get_all()) == 4

    def test_get_by_category(self):
        repo = ListingRepository()
        for l in _sample_listings():
            repo.add(l)
        paintings = repo.get_by_category("painting")
        assert len(paintings) == 2

    def test_get_by_artist(self):
        repo = ListingRepository()
        for l in _sample_listings():
            repo.add(l)
        cole = repo.get_by_artist("Thomas Cole")
        assert len(cole) == 1

    def test_get_unidentified(self):
        repo = ListingRepository()
        for l in _sample_listings():
            repo.add(l)
        unid = repo.get_unidentified()
        assert len(unid) == 2

    def test_get_by_price_range(self):
        repo = ListingRepository()
        for l in _sample_listings():
            repo.add(l)
        results = repo.get_by_price_range(3000, 60000)
        assert len(results) == 3

    def test_load_listings_from_dicts(self):
        repo = ListingRepository()
        data = [
            {"listing_id": "X1", "title": "Test", "artist": "B", "medium": "oil",
             "asking_price": 500, "source": "S", "category": "painting",
             "date_listed": "2025-01-01"},
        ]
        repo.load_listings(data)
        assert len(repo.get_all()) == 1
