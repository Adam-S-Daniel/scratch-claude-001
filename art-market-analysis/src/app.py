"""ArtMarketApp - main orchestrator for the secondary market art analysis app.

Ties together all components:
- MidAtlanticAuctionTracker for regional auction tracking
- OpportunityAnalyzer for comparing past sales vs current listings
- UnidentifiedArtistAnalyzer for finding promising unattributed works
- MarketGapDetector for finding undervalued segments
"""
from __future__ import annotations

from typing import List

from src.models import AuctionHouse, AuctionRecord, ArtListing
from src.repositories import AuctionRepository, ListingRepository
from src.tracker import MidAtlanticAuctionTracker
from src.opportunity import OpportunityAnalyzer, Opportunity
from src.unidentified import UnidentifiedArtistAnalyzer, PromisingWork
from src.gap_detector import MarketGapDetector, MarketGap


class ArtMarketApp:
    def __init__(self) -> None:
        self._auction_repo = AuctionRepository()
        self._listing_repo = ListingRepository()
        self._tracker: MidAtlanticAuctionTracker | None = None
        self._opportunity: OpportunityAnalyzer | None = None
        self._unidentified: UnidentifiedArtistAnalyzer | None = None
        self._gap_detector: MarketGapDetector | None = None

    def _init_analyzers(self) -> None:
        self._tracker = MidAtlanticAuctionTracker(self._auction_repo)
        self._opportunity = OpportunityAnalyzer(self._auction_repo, self._listing_repo)
        self._unidentified = UnidentifiedArtistAnalyzer(self._auction_repo, self._listing_repo)
        self._gap_detector = MarketGapDetector(self._auction_repo, self._listing_repo)

    def load_houses(self, data: list[dict]) -> None:
        for d in data:
            self._auction_repo.add_house(AuctionHouse.from_dict(d))
        self._init_analyzers()

    def load_auction_data(self, data: list[dict]) -> None:
        self._auction_repo.load_records(data)
        self._init_analyzers()

    def load_listing_data(self, data: list[dict]) -> None:
        self._listing_repo.load_listings(data)
        self._init_analyzers()

    @property
    def auction_count(self) -> int:
        return len(self._auction_repo.get_all())

    @property
    def listing_count(self) -> int:
        return len(self._listing_repo.get_all())

    @property
    def house_count(self) -> int:
        return len(self._auction_repo.get_houses())

    def get_regional_records(self) -> List[AuctionRecord]:
        return self._tracker.get_regional_records()

    def get_regional_summary(self) -> dict:
        return self._tracker.get_summary_stats()

    def find_buying_opportunities(self) -> List[Opportunity]:
        return self._opportunity.find_underpriced_listings()

    def find_promising_unidentified_works(self) -> List[PromisingWork]:
        return self._unidentified.find_promising_works(min_past_sale=3000)

    def find_market_gaps(self) -> List[MarketGap]:
        return self._gap_detector.find_category_gaps()

    def compare_artist(self, artist: str) -> dict:
        return self._opportunity.compare_artist(artist)

    def generate_report(self) -> dict:
        return {
            "regional_summary": self.get_regional_summary(),
            "buying_opportunities": [
                {
                    "title": o.listing.title,
                    "artist": o.listing.artist,
                    "asking_price": o.listing.asking_price,
                    "avg_auction_price": o.avg_auction_price,
                    "discount_pct": round(o.discount_pct, 1),
                    "source": o.listing.source,
                }
                for o in self.find_buying_opportunities()
            ],
            "promising_unidentified": [
                {
                    "title": pw.listing.title,
                    "medium": pw.listing.medium,
                    "asking_price": pw.listing.asking_price,
                    "comparable_avg": pw.comparable_avg_price,
                    "signals": pw.signals,
                    "score": round(pw.score, 1),
                }
                for pw in self.find_promising_unidentified_works()
            ],
            "market_gaps": [
                {
                    "segment": g.segment,
                    "dimension": g.dimension,
                    "avg_auction_price": g.avg_auction_price,
                    "avg_listing_price": g.avg_listing_price,
                    "gap_pct": round(g.gap_pct, 1),
                }
                for g in self.find_market_gaps()
            ],
            "top_opportunities": [
                {
                    "segment": g.segment,
                    "dimension": g.dimension,
                    "gap_pct": round(g.gap_pct, 1),
                }
                for g in self._gap_detector.top_opportunities(limit=5)
            ],
        }

    def generate_text_report(self) -> str:
        report = self.generate_report()
        lines = []
        lines.append("=" * 60)
        lines.append("  Mid-Atlantic Art Market Analysis Report")
        lines.append("=" * 60)

        # Regional summary
        s = report["regional_summary"]
        lines.append("")
        lines.append("REGIONAL SUMMARY")
        lines.append("-" * 40)
        lines.append(f"  Tracked auction houses: {s['total_houses']}")
        lines.append(f"  Total auction records:  {s['total_records']}")
        lines.append(f"  Average hammer price:   ${s['avg_price']:,.0f}")
        lines.append(f"  Price range:            ${s['min_price']:,.0f} - ${s['max_price']:,.0f}")

        # Buying opportunities
        lines.append("")
        lines.append("BUYING OPPORTUNITIES (Underpriced Listings)")
        lines.append("-" * 40)
        for opp in report["buying_opportunities"]:
            lines.append(
                f"  {opp['title']} by {opp['artist']}\n"
                f"    Asking: ${opp['asking_price']:,.0f} | "
                f"Avg Auction: ${opp['avg_auction_price']:,.0f} | "
                f"Discount: {opp['discount_pct']}%\n"
                f"    Source: {opp['source']}"
            )

        # Unidentified artist opportunities
        lines.append("")
        lines.append("PROMISING WORKS BY UNIDENTIFIED ARTISTS")
        lines.append("-" * 40)
        for pw in report["promising_unidentified"]:
            lines.append(
                f"  {pw['title']} ({pw['medium']})\n"
                f"    Asking: ${pw['asking_price']:,.0f} | "
                f"Comparable Avg: ${pw['comparable_avg']:,.0f} | "
                f"Score: {pw['score']}"
            )
            for sig in pw["signals"]:
                lines.append(f"    -> {sig}")

        # Market gaps
        lines.append("")
        lines.append("MARKET GAPS (Categories Below Auction Values)")
        lines.append("-" * 40)
        for gap in report["market_gaps"]:
            lines.append(
                f"  {gap['segment']}: "
                f"Auction avg ${gap['avg_auction_price']:,.0f} vs "
                f"Listing avg ${gap['avg_listing_price']:,.0f} "
                f"({gap['gap_pct']}% gap)"
            )

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)
