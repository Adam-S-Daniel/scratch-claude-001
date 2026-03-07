"""Mid-Atlantic auction tracker - filters and tracks regional auction activity."""
from __future__ import annotations

from collections import Counter
from datetime import date
from typing import List, Tuple

from src.models import AuctionHouse, AuctionRecord
from src.repositories import AuctionRepository


class MidAtlanticAuctionTracker:
    REGION = "mid-atlantic"

    def __init__(self, auction_repo: AuctionRepository) -> None:
        self._repo = auction_repo

    def get_tracked_houses(self) -> List[AuctionHouse]:
        return self._repo.get_houses_by_region(self.REGION)

    def _mid_atlantic_house_names(self) -> set[str]:
        return {h.name for h in self.get_tracked_houses()}

    def get_regional_records(self) -> List[AuctionRecord]:
        names = self._mid_atlantic_house_names()
        return [r for r in self._repo.get_all() if r.auction_house in names]

    def get_records_by_category(self, category: str) -> List[AuctionRecord]:
        return [r for r in self.get_regional_records() if r.category == category]

    def get_records_by_date_range(self, start: date, end: date) -> List[AuctionRecord]:
        return [r for r in self.get_regional_records() if start <= r.date_sold <= end]

    def get_summary_stats(self) -> dict:
        records = self.get_regional_records()
        houses = self.get_tracked_houses()
        prices = [r.hammer_price for r in records]
        categories = Counter(r.category for r in records)
        return {
            "total_records": len(records),
            "total_houses": len(houses),
            "avg_price": sum(prices) / len(prices) if prices else 0,
            "min_price": min(prices) if prices else 0,
            "max_price": max(prices) if prices else 0,
            "categories": dict(categories),
        }

    def get_top_categories(self, limit: int = 5) -> List[Tuple[str, int]]:
        records = self.get_regional_records()
        counts = Counter(r.category for r in records)
        return counts.most_common(limit)
