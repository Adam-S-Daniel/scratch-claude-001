"""UnidentifiedArtistAnalyzer - identifies promising works by unidentified artists.

Uses past auction results to find patterns: if unidentified works in a category/medium
sold well, current listings with similar characteristics may be undervalued.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

from src.models import ArtListing, AuctionRecord
from src.repositories import AuctionRepository, ListingRepository


@dataclass
class PromisingWork:
    listing: ArtListing
    comparable_avg_price: float
    signals: List[str] = field(default_factory=list)
    score: float = 0.0


class UnidentifiedArtistAnalyzer:
    def __init__(self, auction_repo: AuctionRepository, listing_repo: ListingRepository) -> None:
        self._auctions = auction_repo
        self._listings = listing_repo

    def get_unidentified_auction_records(self) -> List[AuctionRecord]:
        return self._auctions.get_unidentified()

    def get_unidentified_listings(self) -> List[ArtListing]:
        return self._listings.get_unidentified()

    def _unid_records_by_category(self) -> Dict[str, List[AuctionRecord]]:
        by_cat: dict[str, list[AuctionRecord]] = defaultdict(list)
        for r in self.get_unidentified_auction_records():
            by_cat[r.category].append(r)
        return by_cat

    def _unid_records_by_medium(self) -> Dict[str, List[AuctionRecord]]:
        by_med: dict[str, list[AuctionRecord]] = defaultdict(list)
        for r in self.get_unidentified_auction_records():
            by_med[r.medium.lower()].append(r)
        return by_med

    def find_promising_works(self, min_past_sale: float = 3000) -> List[PromisingWork]:
        by_cat = self._unid_records_by_category()
        promising = []
        for listing in self.get_unidentified_listings():
            cat_records = by_cat.get(listing.category, [])
            high_value = [r for r in cat_records if r.hammer_price >= min_past_sale]
            if not high_value:
                continue
            avg_price = sum(r.hammer_price for r in high_value) / len(high_value)
            signals = []
            signals.append(
                f"{len(high_value)} unidentified works in '{listing.category}' "
                f"sold for avg ${avg_price:,.0f} at auction"
            )
            if listing.asking_price < avg_price:
                signals.append(
                    f"Listed at ${listing.asking_price:,.0f}, "
                    f"below comparable avg of ${avg_price:,.0f}"
                )
            score = self.score_listing(listing)
            promising.append(PromisingWork(listing, avg_price, signals, score))
        promising.sort(key=lambda p: p.score, reverse=True)
        return promising

    def find_promising_by_medium(self, min_past_sale: float = 5000) -> List[PromisingWork]:
        by_med = self._unid_records_by_medium()
        promising = []
        for listing in self.get_unidentified_listings():
            med_records = by_med.get(listing.medium.lower(), [])
            high_value = [r for r in med_records if r.hammer_price >= min_past_sale]
            if not high_value:
                continue
            avg_price = sum(r.hammer_price for r in high_value) / len(high_value)
            signals = [
                f"{len(high_value)} unidentified '{listing.medium}' works "
                f"sold for avg ${avg_price:,.0f}"
            ]
            if listing.asking_price < avg_price:
                signals.append(
                    f"Listed at ${listing.asking_price:,.0f}, "
                    f"below comparable avg of ${avg_price:,.0f}"
                )
            score = self.score_listing(listing)
            promising.append(PromisingWork(listing, avg_price, signals, score))
        promising.sort(key=lambda p: p.score, reverse=True)
        return promising

    def unidentified_category_summary(self) -> Dict[str, dict]:
        by_cat = self._unid_records_by_category()
        listing_by_cat: dict[str, list[ArtListing]] = defaultdict(list)
        for l in self.get_unidentified_listings():
            listing_by_cat[l.category].append(l)

        result = {}
        all_cats = set(by_cat) | set(listing_by_cat)
        for cat in all_cats:
            records = by_cat.get(cat, [])
            listings = listing_by_cat.get(cat, [])
            prices = [r.hammer_price for r in records]
            result[cat] = {
                "avg_auction_price": sum(prices) / len(prices) if prices else 0,
                "max_auction_price": max(prices) if prices else 0,
                "num_auction_records": len(records),
                "num_listings": len(listings),
                "avg_listing_price": (
                    sum(l.asking_price for l in listings) / len(listings) if listings else 0
                ),
            }
        return result

    def score_listing(self, listing: ArtListing) -> float:
        """Score 0-100 for how promising an unidentified listing is.

        Factors:
        - Category has high-value unidentified sales (up to 40 pts)
        - Medium matches high-value unidentified sales (up to 30 pts)
        - Price is below comparable averages (up to 30 pts)
        """
        score = 0.0

        # Category signal
        by_cat = self._unid_records_by_category()
        cat_records = by_cat.get(listing.category, [])
        if cat_records:
            avg_cat = sum(r.hammer_price for r in cat_records) / len(cat_records)
            # Scale: more value = more points, cap at 40
            score += min(40, (avg_cat / 500))

        # Medium signal
        by_med = self._unid_records_by_medium()
        med_records = by_med.get(listing.medium.lower(), [])
        if med_records:
            avg_med = sum(r.hammer_price for r in med_records) / len(med_records)
            score += min(30, (avg_med / 500))

        # Price gap signal
        comparables = cat_records or med_records
        if comparables:
            avg_comp = sum(r.hammer_price for r in comparables) / len(comparables)
            if listing.asking_price < avg_comp:
                gap_ratio = (avg_comp - listing.asking_price) / avg_comp
                score += min(30, gap_ratio * 30)

        return min(100, max(0, score))
