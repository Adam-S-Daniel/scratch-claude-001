"""Data source registry with risk levels, written agreements, and API key config.

Each data source (museum API, open data, auction house scraper) has a risk
level assessed from its terms of service. Users can specify:
- Maximum risk level they're willing to accept
- Written agreements negotiated with specific sources
- API key environment variables and GitHub Secrets names

Risk levels (from notes/terms-of-service.md):
- NONE: CC0/open license with official API — free to use
- LOW: No explicit scraping prohibition found
- MODERATE: Terms unknown/unretrievable, or site has technical barriers
- HIGH: Terms explicitly prohibit scraping/automated access
"""
from __future__ import annotations

import enum
import os
from typing import Dict, List


class RiskLevel(enum.IntEnum):
    """License risk level for a data source, ordered lowest to highest."""

    NONE = 0
    LOW = 1
    MODERATE = 2
    HIGH = 3

    @classmethod
    def from_string(cls, value: str) -> RiskLevel:
        """Parse a risk level from a case-insensitive string.

        Returns HIGH for unrecognized values (fail-safe default).
        """
        try:
            return cls[value.upper()]
        except (KeyError, AttributeError):
            return cls.HIGH


class SourceConfig:
    """Configuration for a single data source."""

    def __init__(
        self,
        key: str,
        name: str,
        source_type: str,
        risk_level: RiskLevel,
        license: str,
        has_agreement: bool = False,
        api_key_env: str | None = None,
        api_key_secret: str | None = None,
    ) -> None:
        self.key = key
        self.name = name
        self.source_type = source_type  # "api", "scraper", "seed", "csv"
        self.risk_level = risk_level
        self.license = license
        self.has_agreement = has_agreement
        self.api_key_env = api_key_env
        self.api_key_secret = api_key_secret

    @property
    def requires_api_key(self) -> bool:
        return self.api_key_env is not None

    def get_api_key(self) -> str | None:
        """Retrieve the API key from the environment variable, if configured."""
        if self.api_key_env is None:
            return None
        return os.environ.get(self.api_key_env) or None

    def is_allowed(self, max_risk: RiskLevel) -> bool:
        """Check whether this source is allowed under the given max risk level.

        A written agreement overrides the risk level check.
        """
        if self.has_agreement:
            return True
        return self.risk_level <= max_risk


class SourceRegistry:
    """Registry of all data sources with risk filtering and agreement tracking."""

    def __init__(self, sources: Dict[str, SourceConfig] | None = None) -> None:
        if sources is None:
            self._sources = {k: _copy_config(v) for k, v in DEFAULT_SOURCES.items()}
        else:
            self._sources = dict(sources)

    def get(self, key: str) -> SourceConfig | None:
        return self._sources.get(key)

    def all_sources(self) -> List[SourceConfig]:
        return list(self._sources.values())

    def allowed_sources(self, max_risk: RiskLevel) -> List[SourceConfig]:
        return [s for s in self._sources.values() if s.is_allowed(max_risk)]

    def allowed_scraper_keys(self, max_risk: RiskLevel) -> List[str]:
        return [
            s.key
            for s in self._sources.values()
            if s.source_type == "scraper" and s.is_allowed(max_risk)
        ]

    def allowed_api_keys(self, max_risk: RiskLevel) -> List[str]:
        return [
            s.key
            for s in self._sources.values()
            if s.source_type in ("api", "csv") and s.is_allowed(max_risk)
        ]

    def is_source_allowed(self, key: str, max_risk: RiskLevel) -> bool:
        src = self._sources.get(key)
        if src is None:
            return False
        return src.is_allowed(max_risk)

    def set_agreement(self, key: str, has_agreement: bool) -> None:
        src = self._sources.get(key)
        if src is not None:
            src.has_agreement = has_agreement

    def set_api_key_secret(self, key: str, secret_name: str) -> None:
        src = self._sources.get(key)
        if src is not None:
            src.api_key_secret = secret_name


def _copy_config(cfg: SourceConfig) -> SourceConfig:
    """Create a shallow copy of a SourceConfig."""
    return SourceConfig(
        key=cfg.key,
        name=cfg.name,
        source_type=cfg.source_type,
        risk_level=cfg.risk_level,
        license=cfg.license,
        has_agreement=cfg.has_agreement,
        api_key_env=cfg.api_key_env,
        api_key_secret=cfg.api_key_secret,
    )


# Default source definitions based on notes/terms-of-service.md
DEFAULT_SOURCES: Dict[str, SourceConfig] = {
    "seed": SourceConfig(
        key="seed",
        name="Seed Data",
        source_type="seed",
        risk_level=RiskLevel.NONE,
        license="Internal",
    ),
    "met_museum": SourceConfig(
        key="met_museum",
        name="Metropolitan Museum of Art",
        source_type="api",
        risk_level=RiskLevel.NONE,
        license="CC0",
    ),
    "smithsonian": SourceConfig(
        key="smithsonian",
        name="Smithsonian Open Access",
        source_type="api",
        risk_level=RiskLevel.NONE,
        license="CC0",
        api_key_env="SMITHSONIAN_API_KEY",
        api_key_secret="SMITHSONIAN_API_KEY",
    ),
    "nga": SourceConfig(
        key="nga",
        name="National Gallery of Art",
        source_type="csv",
        risk_level=RiskLevel.NONE,
        license="CC0",
    ),
    "leland_little": SourceConfig(
        key="leland_little",
        name="Leland Little Auctions",
        source_type="scraper",
        risk_level=RiskLevel.LOW,
        license="Proprietary",
    ),
    "hilliard": SourceConfig(
        key="hilliard",
        name="Hilliard & Co.",
        source_type="scraper",
        risk_level=RiskLevel.MODERATE,
        license="Unknown",
    ),
    "ctbids": SourceConfig(
        key="ctbids",
        name="CTBids",
        source_type="scraper",
        risk_level=RiskLevel.MODERATE,
        license="Unknown (React SPA)",
    ),
    "weschlers": SourceConfig(
        key="weschlers",
        name="Weschler's",
        source_type="scraper",
        risk_level=RiskLevel.HIGH,
        license="Invaluable ToS",
    ),
    "quinns": SourceConfig(
        key="quinns",
        name="Quinn's Auction Galleries",
        source_type="scraper",
        risk_level=RiskLevel.HIGH,
        license="HiBid ToS",
    ),
    "alex_cooper": SourceConfig(
        key="alex_cooper",
        name="Alex Cooper Auctioneers",
        source_type="scraper",
        risk_level=RiskLevel.HIGH,
        license="Auction Mobility ToS",
    ),
    "potomack": SourceConfig(
        key="potomack",
        name="Potomack Company",
        source_type="scraper",
        risk_level=RiskLevel.HIGH,
        license="Invaluable ToS",
    ),
    "bunch": SourceConfig(
        key="bunch",
        name="William Bunch Auctions",
        source_type="scraper",
        risk_level=RiskLevel.HIGH,
        license="Auction Mobility ToS",
    ),
    "headleys": SourceConfig(
        key="headleys",
        name="Headley's Auctions",
        source_type="scraper",
        risk_level=RiskLevel.HIGH,
        license="HiBid ToS",
    ),
}
