"""Core domain models for the art market analysis app."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date


_UNIDENTIFIED_PATTERNS = [
    r"(?i)^unknown",
    r"(?i)^unidentified",
    r"(?i)^anonymous",
    r"(?i)^attributed\s+to\s+unknown",
    r"(?i)^circle\s+of\s+unknown",
    r"(?i)^school\s+of$",
    r"(?i)^manner\s+of$",
]

_UNIDENTIFIED_RE = [re.compile(p) for p in _UNIDENTIFIED_PATTERNS]


def _is_unidentified(artist: str) -> bool:
    artist = artist.strip()
    return any(regex.search(artist) for regex in _UNIDENTIFIED_RE)


@dataclass(frozen=True)
class AuctionHouse:
    name: str
    location: str
    region: str

    @classmethod
    def from_dict(cls, data: dict) -> AuctionHouse:
        return cls(name=data["name"], location=data["location"], region=data["region"])


@dataclass
class AuctionRecord:
    lot_number: str
    title: str
    artist: str
    medium: str
    date_sold: date
    hammer_price: float
    auction_house: str
    category: str

    @property
    def is_unidentified_artist(self) -> bool:
        return _is_unidentified(self.artist)

    @classmethod
    def from_dict(cls, data: dict) -> AuctionRecord:
        date_sold = data["date_sold"]
        if isinstance(date_sold, str):
            date_sold = date.fromisoformat(date_sold)
        return cls(
            lot_number=data["lot_number"],
            title=data["title"],
            artist=data["artist"],
            medium=data["medium"],
            date_sold=date_sold,
            hammer_price=float(data["hammer_price"]),
            auction_house=data["auction_house"],
            category=data["category"],
        )


@dataclass
class ArtListing:
    listing_id: str
    title: str
    artist: str
    medium: str
    asking_price: float
    source: str
    category: str
    date_listed: date

    @property
    def is_unidentified_artist(self) -> bool:
        return _is_unidentified(self.artist)

    @classmethod
    def from_dict(cls, data: dict) -> ArtListing:
        date_listed = data["date_listed"]
        if isinstance(date_listed, str):
            date_listed = date.fromisoformat(date_listed)
        return cls(
            listing_id=data["listing_id"],
            title=data["title"],
            artist=data["artist"],
            medium=data["medium"],
            asking_price=float(data["asking_price"]),
            source=data["source"],
            category=data["category"],
            date_listed=date_listed,
        )
