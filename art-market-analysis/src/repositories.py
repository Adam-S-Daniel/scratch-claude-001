"""In-memory repositories for auction records and art listings."""
from __future__ import annotations

from datetime import date
from typing import List

from src.models import AuctionHouse, AuctionRecord, ArtListing


class AuctionRepository:
    def __init__(self) -> None:
        self._records: List[AuctionRecord] = []
        self._houses: List[AuctionHouse] = []

    def add(self, record: AuctionRecord) -> None:
        self._records.append(record)

    def add_house(self, house: AuctionHouse) -> None:
        self._houses.append(house)

    def get_all(self) -> List[AuctionRecord]:
        return list(self._records)

    def get_houses(self) -> List[AuctionHouse]:
        return list(self._houses)

    def get_houses_by_region(self, region: str) -> List[AuctionHouse]:
        return [h for h in self._houses if h.region.lower() == region.lower()]

    def get_by_auction_house(self, name: str) -> List[AuctionRecord]:
        return [r for r in self._records if r.auction_house == name]

    def get_by_category(self, category: str) -> List[AuctionRecord]:
        return [r for r in self._records if r.category == category]

    def get_by_artist(self, artist: str) -> List[AuctionRecord]:
        return [r for r in self._records if r.artist.lower() == artist.lower()]

    def get_unidentified(self) -> List[AuctionRecord]:
        return [r for r in self._records if r.is_unidentified_artist]

    def get_by_date_range(self, start: date, end: date) -> List[AuctionRecord]:
        return [r for r in self._records if start <= r.date_sold <= end]

    def load_records(self, data: list[dict]) -> None:
        for d in data:
            self.add(AuctionRecord.from_dict(d))


class ListingRepository:
    def __init__(self) -> None:
        self._listings: List[ArtListing] = []

    def add(self, listing: ArtListing) -> None:
        self._listings.append(listing)

    def get_all(self) -> List[ArtListing]:
        return list(self._listings)

    def get_by_category(self, category: str) -> List[ArtListing]:
        return [l for l in self._listings if l.category == category]

    def get_by_artist(self, artist: str) -> List[ArtListing]:
        return [l for l in self._listings if l.artist.lower() == artist.lower()]

    def get_unidentified(self) -> List[ArtListing]:
        return [l for l in self._listings if l.is_unidentified_artist]

    def get_by_price_range(self, min_price: float, max_price: float) -> List[ArtListing]:
        return [l for l in self._listings if min_price <= l.asking_price <= max_price]

    def load_listings(self, data: list[dict]) -> None:
        for d in data:
            self.add(ArtListing.from_dict(d))
