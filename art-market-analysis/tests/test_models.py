"""Tests for core domain models: AuctionHouse, AuctionRecord, ArtListing."""
from datetime import date, datetime
from src.models import AuctionHouse, AuctionRecord, ArtListing


class TestAuctionHouse:
    def test_create_auction_house(self):
        house = AuctionHouse(
            name="Brunk Auctions",
            location="Asheville, NC",
            region="mid-atlantic",
        )
        assert house.name == "Brunk Auctions"
        assert house.location == "Asheville, NC"
        assert house.region == "mid-atlantic"

    def test_auction_house_equality(self):
        h1 = AuctionHouse(name="Brunk", location="Asheville, NC", region="mid-atlantic")
        h2 = AuctionHouse(name="Brunk", location="Asheville, NC", region="mid-atlantic")
        assert h1 == h2

    def test_auction_house_from_dict(self):
        data = {"name": "Freeman's", "location": "Philadelphia, PA", "region": "mid-atlantic"}
        house = AuctionHouse.from_dict(data)
        assert house.name == "Freeman's"


class TestAuctionRecord:
    def test_create_auction_record(self):
        record = AuctionRecord(
            lot_number="123",
            title="Landscape with Figures",
            artist="Thomas Cole",
            medium="oil on canvas",
            date_sold=date(2024, 3, 15),
            hammer_price=45000.00,
            auction_house="Freeman's",
            category="painting",
        )
        assert record.title == "Landscape with Figures"
        assert record.hammer_price == 45000.00
        assert record.artist == "Thomas Cole"

    def test_auction_record_is_unidentified_artist(self):
        record = AuctionRecord(
            lot_number="456",
            title="Portrait of a Lady",
            artist="Unidentified Artist",
            medium="oil on canvas",
            date_sold=date(2024, 1, 10),
            hammer_price=2500.00,
            auction_house="Weschler's",
            category="painting",
        )
        assert record.is_unidentified_artist is True

    def test_auction_record_known_artist_not_unidentified(self):
        record = AuctionRecord(
            lot_number="789",
            title="Still Life",
            artist="Severin Roesen",
            medium="oil on canvas",
            date_sold=date(2024, 5, 20),
            hammer_price=120000.00,
            auction_house="Brunk Auctions",
            category="painting",
        )
        assert record.is_unidentified_artist is False

    def test_unidentified_artist_variants(self):
        """Various ways auction houses label unidentified artists."""
        variants = [
            "Unknown Artist",
            "Unidentified",
            "Anonymous",
            "Attributed to Unknown",
            "Circle of Unknown",
            "School of",
            "Manner of",
        ]
        for label in variants:
            record = AuctionRecord(
                lot_number="1",
                title="Test",
                artist=label,
                medium="oil",
                date_sold=date(2024, 1, 1),
                hammer_price=100.0,
                auction_house="Test",
                category="painting",
            )
            assert record.is_unidentified_artist is True, f"Expected '{label}' to be unidentified"

    def test_auction_record_from_dict(self):
        data = {
            "lot_number": "100",
            "title": "Seascape",
            "artist": "Unknown",
            "medium": "watercolor",
            "date_sold": "2024-06-01",
            "hammer_price": 800.0,
            "auction_house": "Potomack",
            "category": "painting",
        }
        record = AuctionRecord.from_dict(data)
        assert record.title == "Seascape"
        assert record.date_sold == date(2024, 6, 1)


class TestArtListing:
    def test_create_listing(self):
        listing = ArtListing(
            listing_id="L001",
            title="Mountain View",
            artist="Albert Bierstadt",
            medium="oil on canvas",
            asking_price=75000.00,
            source="Gallery X",
            category="painting",
            date_listed=date(2025, 1, 15),
        )
        assert listing.title == "Mountain View"
        assert listing.asking_price == 75000.00

    def test_listing_is_unidentified_artist(self):
        listing = ArtListing(
            listing_id="L002",
            title="Floral Still Life",
            artist="Unknown Artist",
            medium="oil on panel",
            asking_price=3000.00,
            source="Online Dealer",
            category="painting",
            date_listed=date(2025, 2, 1),
        )
        assert listing.is_unidentified_artist is True

    def test_listing_from_dict(self):
        data = {
            "listing_id": "L003",
            "title": "Harbor Scene",
            "artist": "John Smith",
            "medium": "oil",
            "asking_price": 5000.0,
            "source": "Dealer Y",
            "category": "painting",
            "date_listed": "2025-03-01",
        }
        listing = ArtListing.from_dict(data)
        assert listing.listing_id == "L003"
        assert listing.date_listed == date(2025, 3, 1)
