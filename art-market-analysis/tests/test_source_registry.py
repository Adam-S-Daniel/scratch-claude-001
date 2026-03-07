"""Tests for data source registry with risk levels, agreements, and API key config."""
from __future__ import annotations

import os
from unittest.mock import patch

from src.source_registry import (
    RiskLevel,
    SourceConfig,
    SourceRegistry,
    DEFAULT_SOURCES,
)


class TestRiskLevel:
    """Test the RiskLevel enum ordering and comparisons."""

    def test_none_is_lowest(self):
        assert RiskLevel.NONE < RiskLevel.LOW

    def test_low_less_than_moderate(self):
        assert RiskLevel.LOW < RiskLevel.MODERATE

    def test_moderate_less_than_high(self):
        assert RiskLevel.MODERATE < RiskLevel.HIGH

    def test_high_is_highest(self):
        assert RiskLevel.HIGH > RiskLevel.NONE
        assert RiskLevel.HIGH > RiskLevel.LOW
        assert RiskLevel.HIGH > RiskLevel.MODERATE

    def test_equal_to_self(self):
        assert RiskLevel.NONE == RiskLevel.NONE
        assert RiskLevel.HIGH == RiskLevel.HIGH

    def test_from_string(self):
        assert RiskLevel.from_string("none") == RiskLevel.NONE
        assert RiskLevel.from_string("LOW") == RiskLevel.LOW
        assert RiskLevel.from_string("Moderate") == RiskLevel.MODERATE
        assert RiskLevel.from_string("HIGH") == RiskLevel.HIGH

    def test_from_string_invalid_defaults_high(self):
        assert RiskLevel.from_string("unknown") == RiskLevel.HIGH
        assert RiskLevel.from_string("") == RiskLevel.HIGH


class TestSourceConfig:
    """Test SourceConfig data container."""

    def test_basic_creation(self):
        cfg = SourceConfig(
            key="met_museum",
            name="Metropolitan Museum of Art",
            source_type="api",
            risk_level=RiskLevel.NONE,
            license="CC0",
        )
        assert cfg.key == "met_museum"
        assert cfg.risk_level == RiskLevel.NONE
        assert cfg.has_agreement is False
        assert cfg.api_key_env is None
        assert cfg.api_key_secret is None

    def test_with_agreement(self):
        cfg = SourceConfig(
            key="weschlers",
            name="Weschler's",
            source_type="scraper",
            risk_level=RiskLevel.HIGH,
            license="Invaluable ToS",
            has_agreement=True,
        )
        assert cfg.has_agreement is True

    def test_with_api_key(self):
        cfg = SourceConfig(
            key="smithsonian",
            name="Smithsonian Open Access",
            source_type="api",
            risk_level=RiskLevel.NONE,
            license="CC0",
            api_key_env="SMITHSONIAN_API_KEY",
            api_key_secret="SMITHSONIAN_API_KEY",
        )
        assert cfg.api_key_env == "SMITHSONIAN_API_KEY"
        assert cfg.api_key_secret == "SMITHSONIAN_API_KEY"

    def test_is_allowed_when_below_max_risk(self):
        cfg = SourceConfig(
            key="leland_little",
            name="Leland Little",
            source_type="scraper",
            risk_level=RiskLevel.LOW,
            license="Proprietary",
        )
        assert cfg.is_allowed(max_risk=RiskLevel.LOW) is True
        assert cfg.is_allowed(max_risk=RiskLevel.MODERATE) is True
        assert cfg.is_allowed(max_risk=RiskLevel.HIGH) is True

    def test_is_not_allowed_when_above_max_risk(self):
        cfg = SourceConfig(
            key="weschlers",
            name="Weschler's",
            source_type="scraper",
            risk_level=RiskLevel.HIGH,
            license="Invaluable ToS",
        )
        assert cfg.is_allowed(max_risk=RiskLevel.NONE) is False
        assert cfg.is_allowed(max_risk=RiskLevel.LOW) is False
        assert cfg.is_allowed(max_risk=RiskLevel.MODERATE) is False

    def test_agreement_overrides_risk(self):
        """A written agreement should make any source allowed regardless of risk."""
        cfg = SourceConfig(
            key="weschlers",
            name="Weschler's",
            source_type="scraper",
            risk_level=RiskLevel.HIGH,
            license="Invaluable ToS",
            has_agreement=True,
        )
        assert cfg.is_allowed(max_risk=RiskLevel.NONE) is True

    def test_requires_api_key_true(self):
        cfg = SourceConfig(
            key="smithsonian",
            name="Smithsonian",
            source_type="api",
            risk_level=RiskLevel.NONE,
            license="CC0",
            api_key_env="SMITHSONIAN_API_KEY",
        )
        assert cfg.requires_api_key is True

    def test_requires_api_key_false(self):
        cfg = SourceConfig(
            key="met_museum",
            name="Met Museum",
            source_type="api",
            risk_level=RiskLevel.NONE,
            license="CC0",
        )
        assert cfg.requires_api_key is False

    def test_get_api_key_from_env(self):
        cfg = SourceConfig(
            key="smithsonian",
            name="Smithsonian",
            source_type="api",
            risk_level=RiskLevel.NONE,
            license="CC0",
            api_key_env="SMITHSONIAN_API_KEY",
        )
        with patch.dict(os.environ, {"SMITHSONIAN_API_KEY": "test-key-123"}):
            assert cfg.get_api_key() == "test-key-123"

    def test_get_api_key_missing(self):
        cfg = SourceConfig(
            key="smithsonian",
            name="Smithsonian",
            source_type="api",
            risk_level=RiskLevel.NONE,
            license="CC0",
            api_key_env="SMITHSONIAN_API_KEY",
        )
        with patch.dict(os.environ, {}, clear=True):
            assert cfg.get_api_key() is None

    def test_get_api_key_no_env_configured(self):
        cfg = SourceConfig(
            key="met_museum",
            name="Met",
            source_type="api",
            risk_level=RiskLevel.NONE,
            license="CC0",
        )
        assert cfg.get_api_key() is None


class TestSourceRegistry:
    """Test the SourceRegistry that manages all data sources."""

    def test_default_sources_loaded(self):
        reg = SourceRegistry()
        assert len(reg.all_sources()) >= 12

    def test_get_source_by_key(self):
        reg = SourceRegistry()
        met = reg.get("met_museum")
        assert met is not None
        assert met.name == "Metropolitan Museum of Art"
        assert met.risk_level == RiskLevel.NONE

    def test_get_unknown_key_returns_none(self):
        reg = SourceRegistry()
        assert reg.get("nonexistent_source") is None

    def test_filter_by_max_risk_none(self):
        """Only CC0/official API sources should pass risk=NONE."""
        reg = SourceRegistry()
        allowed = reg.allowed_sources(max_risk=RiskLevel.NONE)
        for src in allowed:
            assert src.risk_level == RiskLevel.NONE

    def test_filter_by_max_risk_low(self):
        reg = SourceRegistry()
        allowed = reg.allowed_sources(max_risk=RiskLevel.LOW)
        for src in allowed:
            assert src.risk_level <= RiskLevel.LOW

    def test_filter_by_max_risk_high_includes_all(self):
        reg = SourceRegistry()
        all_sources = reg.all_sources()
        allowed = reg.allowed_sources(max_risk=RiskLevel.HIGH)
        assert len(allowed) == len(all_sources)

    def test_allowed_scraper_keys(self):
        """Should return only scraper keys that pass the risk filter."""
        reg = SourceRegistry()
        keys = reg.allowed_scraper_keys(max_risk=RiskLevel.NONE)
        assert keys == []  # All scrapers have risk > NONE

    def test_allowed_scraper_keys_low_includes_leland(self):
        reg = SourceRegistry()
        keys = reg.allowed_scraper_keys(max_risk=RiskLevel.LOW)
        assert "leland_little" in keys

    def test_allowed_scraper_keys_high_includes_all(self):
        reg = SourceRegistry()
        keys = reg.allowed_scraper_keys(max_risk=RiskLevel.HIGH)
        assert len(keys) == 9

    def test_allowed_api_keys(self):
        """API sources (met, smithsonian, nga) should all pass NONE risk."""
        reg = SourceRegistry()
        keys = reg.allowed_api_keys(max_risk=RiskLevel.NONE)
        assert "met_museum" in keys
        assert "smithsonian" in keys
        assert "nga" in keys

    def test_set_agreement(self):
        reg = SourceRegistry()
        reg.set_agreement("weschlers", True)
        cfg = reg.get("weschlers")
        assert cfg.has_agreement is True
        # With agreement, should be allowed at any risk level
        assert cfg.is_allowed(max_risk=RiskLevel.NONE) is True

    def test_set_agreement_unknown_key(self):
        reg = SourceRegistry()
        # Should not raise — just silently ignore
        reg.set_agreement("nonexistent", True)

    def test_set_api_key_secret(self):
        reg = SourceRegistry()
        reg.set_api_key_secret("smithsonian", "MY_GITHUB_SECRET")
        cfg = reg.get("smithsonian")
        assert cfg.api_key_secret == "MY_GITHUB_SECRET"

    def test_seed_always_allowed(self):
        """Seed data source should always be allowed regardless of risk."""
        reg = SourceRegistry()
        seed = reg.get("seed")
        assert seed is not None
        assert seed.risk_level == RiskLevel.NONE
        assert seed.is_allowed(max_risk=RiskLevel.NONE) is True

    def test_is_source_allowed_convenience(self):
        reg = SourceRegistry()
        assert reg.is_source_allowed("met_museum", max_risk=RiskLevel.NONE) is True
        assert reg.is_source_allowed("weschlers", max_risk=RiskLevel.NONE) is False

    def test_is_source_allowed_unknown_key(self):
        reg = SourceRegistry()
        assert reg.is_source_allowed("nonexistent", max_risk=RiskLevel.HIGH) is False


class TestDefaultSources:
    """Verify the default source registry matches our terms-of-service analysis."""

    def test_met_museum_is_none_risk(self):
        assert DEFAULT_SOURCES["met_museum"].risk_level == RiskLevel.NONE

    def test_smithsonian_is_none_risk(self):
        assert DEFAULT_SOURCES["smithsonian"].risk_level == RiskLevel.NONE

    def test_nga_is_none_risk(self):
        assert DEFAULT_SOURCES["nga"].risk_level == RiskLevel.NONE

    def test_leland_little_is_low_risk(self):
        assert DEFAULT_SOURCES["leland_little"].risk_level == RiskLevel.LOW

    def test_hilliard_is_moderate_risk(self):
        assert DEFAULT_SOURCES["hilliard"].risk_level == RiskLevel.MODERATE

    def test_ctbids_is_moderate_risk(self):
        assert DEFAULT_SOURCES["ctbids"].risk_level == RiskLevel.MODERATE

    def test_weschlers_is_high_risk(self):
        assert DEFAULT_SOURCES["weschlers"].risk_level == RiskLevel.HIGH

    def test_quinns_is_high_risk(self):
        assert DEFAULT_SOURCES["quinns"].risk_level == RiskLevel.HIGH

    def test_alex_cooper_is_high_risk(self):
        assert DEFAULT_SOURCES["alex_cooper"].risk_level == RiskLevel.HIGH

    def test_potomack_is_high_risk(self):
        assert DEFAULT_SOURCES["potomack"].risk_level == RiskLevel.HIGH

    def test_bunch_is_high_risk(self):
        assert DEFAULT_SOURCES["bunch"].risk_level == RiskLevel.HIGH

    def test_headleys_is_high_risk(self):
        assert DEFAULT_SOURCES["headleys"].risk_level == RiskLevel.HIGH

    def test_smithsonian_requires_api_key(self):
        assert DEFAULT_SOURCES["smithsonian"].requires_api_key is True

    def test_met_does_not_require_api_key(self):
        assert DEFAULT_SOURCES["met_museum"].requires_api_key is False


class TestEdgeCases:
    """Edge case tests for source registry."""

    def test_risk_level_comparison_with_none_type(self):
        """RiskLevel should handle comparison gracefully."""
        assert RiskLevel.NONE <= RiskLevel.NONE
        assert not (RiskLevel.HIGH < RiskLevel.HIGH)

    def test_source_config_agreement_with_none_risk(self):
        """Even a NONE-risk source can have an agreement (redundant but valid)."""
        cfg = SourceConfig(
            key="test",
            name="Test",
            source_type="api",
            risk_level=RiskLevel.NONE,
            license="CC0",
            has_agreement=True,
        )
        assert cfg.is_allowed(max_risk=RiskLevel.NONE) is True

    def test_empty_registry(self):
        """A registry with no sources should return empty lists."""
        reg = SourceRegistry(sources={})
        assert reg.all_sources() == []
        assert reg.allowed_sources(max_risk=RiskLevel.HIGH) == []
        assert reg.allowed_scraper_keys(max_risk=RiskLevel.HIGH) == []
        assert reg.allowed_api_keys(max_risk=RiskLevel.HIGH) == []

    def test_set_agreement_then_revoke(self):
        reg = SourceRegistry()
        reg.set_agreement("weschlers", True)
        assert reg.get("weschlers").has_agreement is True
        reg.set_agreement("weschlers", False)
        assert reg.get("weschlers").has_agreement is False
        # After revoking, high-risk source should not be allowed at NONE
        assert reg.is_source_allowed("weschlers", max_risk=RiskLevel.NONE) is False

    def test_multiple_agreements(self):
        reg = SourceRegistry()
        reg.set_agreement("weschlers", True)
        reg.set_agreement("quinns", True)
        reg.set_agreement("alex_cooper", True)
        allowed = reg.allowed_scraper_keys(max_risk=RiskLevel.NONE)
        assert "weschlers" in allowed
        assert "quinns" in allowed
        assert "alex_cooper" in allowed
        # Others without agreements should still be excluded
        assert "potomack" not in allowed
