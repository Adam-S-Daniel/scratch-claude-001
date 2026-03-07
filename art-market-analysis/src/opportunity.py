"""OpportunityAnalyzer - compares past auction sales with current listings
to identify buying opportunities (underpriced) and overpriced listings."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List

from src.models import ArtListing, AuctionRecord
from src.repositories import AuctionRepository, ListingRepository


@dataclass
class Opportunity:
    listing: ArtListing
    avg_auction_price: float
    discount_pct: float  # positive means listing is below avg auction price


class OpportunityAnalyzer:
    def __init__(self, auction_repo: AuctionRepository, listing_repo: ListingRepository) -> None:
        self._auctions = auction_repo
        self._listings = listing_repo

    def _avg_price_by_artist(self) -> Dict[str, float]:
        by_artist: dict[str, list[float]] = defaultdict(list)
        for r in self._auctions.get_all():
            by_artist[r.artist.lower()].append(r.hammer_price)
        return {artist: sum(prices) / len(prices) for artist, prices in by_artist.items()}

    def find_underpriced_listings(self) -> List[Opportunity]:
        avg_prices = self._avg_price_by_artist()
        opportunities = []
        for listing in self._listings.get_all():
            key = listing.artist.lower()
            if key in avg_prices:
                avg = avg_prices[key]
                if listing.asking_price < avg:
                    discount = (avg - listing.asking_price) / avg * 100
                    opportunities.append(Opportunity(listing, avg, discount))
        opportunities.sort(key=lambda o: o.discount_pct, reverse=True)
        return opportunities

    def find_overpriced_listings(self) -> List[Opportunity]:
        avg_prices = self._avg_price_by_artist()
        overpriced = []
        for listing in self._listings.get_all():
            key = listing.artist.lower()
            if key in avg_prices:
                avg = avg_prices[key]
                if listing.asking_price > avg:
                    premium = (listing.asking_price - avg) / avg * 100
                    overpriced.append(Opportunity(listing, avg, premium))
        overpriced.sort(key=lambda o: o.discount_pct, reverse=True)
        return overpriced

    def compare_artist(self, artist: str) -> dict:
        records = self._auctions.get_by_artist(artist)
        listings = self._listings.get_by_artist(artist)
        if not records:
            return {
                "artist": artist,
                "avg_auction_price": 0,
                "num_auction_records": 0,
                "current_listings": [],
                "underpriced": [],
                "overpriced": [],
            }
        avg_price = sum(r.hammer_price for r in records) / len(records)
        underpriced = [l for l in listings if l.asking_price < avg_price]
        overpriced = [l for l in listings if l.asking_price > avg_price]
        return {
            "artist": artist,
            "avg_auction_price": avg_price,
            "num_auction_records": len(records),
            "current_listings": listings,
            "underpriced": underpriced,
            "overpriced": overpriced,
        }

    def price_gap_by_category(self) -> Dict[str, dict]:
        auction_by_cat: dict[str, list[float]] = defaultdict(list)
        listing_by_cat: dict[str, list[float]] = defaultdict(list)
        for r in self._auctions.get_all():
            auction_by_cat[r.category].append(r.hammer_price)
        for l in self._listings.get_all():
            listing_by_cat[l.category].append(l.asking_price)

        all_cats = set(auction_by_cat) | set(listing_by_cat)
        result = {}
        for cat in all_cats:
            a_prices = auction_by_cat.get(cat, [])
            l_prices = listing_by_cat.get(cat, [])
            result[cat] = {
                "avg_auction_price": sum(a_prices) / len(a_prices) if a_prices else 0,
                "avg_listing_price": sum(l_prices) / len(l_prices) if l_prices else 0,
                "num_auction_records": len(a_prices),
                "num_listings": len(l_prices),
            }
        return result
