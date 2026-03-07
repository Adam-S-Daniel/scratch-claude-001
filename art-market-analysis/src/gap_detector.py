"""MarketGapDetector - finds gaps between auction values and listing prices
across categories, mediums, and individual artists."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set

from src.repositories import AuctionRepository, ListingRepository


@dataclass
class MarketGap:
    segment: str  # category name, medium, or artist
    dimension: str  # "category", "medium", or "artist"
    avg_auction_price: float
    avg_listing_price: float
    gap_pct: float  # how much lower listings are vs auctions (positive = undervalued)
    num_auction_records: int
    num_listings: int


class MarketGapDetector:
    def __init__(self, auction_repo: AuctionRepository, listing_repo: ListingRepository) -> None:
        self._auctions = auction_repo
        self._listings = listing_repo

    def _compute_gaps(self, dimension: str, auction_groups: dict, listing_groups: dict,
                      min_discount_pct: float = 0) -> List[MarketGap]:
        gaps = []
        common = set(auction_groups) & set(listing_groups)
        for key in common:
            a_prices = auction_groups[key]
            l_prices = listing_groups[key]
            avg_a = sum(a_prices) / len(a_prices)
            avg_l = sum(l_prices) / len(l_prices)
            if avg_a > 0:
                gap_pct = (avg_a - avg_l) / avg_a * 100
                if gap_pct > min_discount_pct:
                    gaps.append(MarketGap(
                        segment=key,
                        dimension=dimension,
                        avg_auction_price=avg_a,
                        avg_listing_price=avg_l,
                        gap_pct=gap_pct,
                        num_auction_records=len(a_prices),
                        num_listings=len(l_prices),
                    ))
        gaps.sort(key=lambda g: g.gap_pct, reverse=True)
        return gaps

    def find_category_gaps(self) -> List[MarketGap]:
        auction_by_cat: dict[str, list[float]] = defaultdict(list)
        listing_by_cat: dict[str, list[float]] = defaultdict(list)
        for r in self._auctions.get_all():
            auction_by_cat[r.category].append(r.hammer_price)
        for l in self._listings.get_all():
            listing_by_cat[l.category].append(l.asking_price)
        return self._compute_gaps("category", auction_by_cat, listing_by_cat)

    def find_medium_gaps(self) -> List[MarketGap]:
        auction_by_med: dict[str, list[float]] = defaultdict(list)
        listing_by_med: dict[str, list[float]] = defaultdict(list)
        for r in self._auctions.get_all():
            auction_by_med[r.medium.lower()].append(r.hammer_price)
        for l in self._listings.get_all():
            listing_by_med[l.medium.lower()].append(l.asking_price)
        return self._compute_gaps("medium", auction_by_med, listing_by_med)

    def find_artist_gaps(self, min_discount_pct: float = 20) -> List[MarketGap]:
        auction_by_artist: dict[str, list[float]] = defaultdict(list)
        listing_by_artist: dict[str, list[float]] = defaultdict(list)
        for r in self._auctions.get_all():
            auction_by_artist[r.artist].append(r.hammer_price)
        for l in self._listings.get_all():
            listing_by_artist[l.artist].append(l.asking_price)
        return self._compute_gaps("artist", auction_by_artist, listing_by_artist, min_discount_pct)

    def find_untracked_categories(self) -> Set[str]:
        auction_cats = {r.category for r in self._auctions.get_all()}
        listing_cats = {l.category for l in self._listings.get_all()}
        return listing_cats - auction_cats

    def market_summary(self) -> dict:
        all_gaps = self.find_category_gaps()
        return {
            "total_auction_records": len(self._auctions.get_all()),
            "total_listings": len(self._listings.get_all()),
            "categories_tracked": len({r.category for r in self._auctions.get_all()}),
            "avg_gap_pct": (
                sum(g.gap_pct for g in all_gaps) / len(all_gaps) if all_gaps else 0
            ),
            "untracked_categories": self.find_untracked_categories(),
        }

    def top_opportunities(self, limit: int = 5) -> List[MarketGap]:
        all_gaps = (
            self.find_category_gaps()
            + self.find_medium_gaps()
            + self.find_artist_gaps(min_discount_pct=10)
        )
        all_gaps.sort(key=lambda g: g.gap_pct, reverse=True)
        return all_gaps[:limit]
