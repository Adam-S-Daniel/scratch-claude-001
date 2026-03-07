---
name: assess-risk
description: Assess and configure license risk levels for data sources. Use when adding a new data source, reviewing legal compliance, or configuring which sources to include based on terms of service risk.
compatibility: Python 3.11+, no external dependencies beyond stdlib
metadata:
  author: art-market-analysis
  version: "1.0"
---

# Assessing Data Source Risk Levels

This skill defines how to evaluate the license risk level of a data source and configure it in the source registry.

## Risk Level Definitions

| Level | Value | Criteria | Examples |
|-------|-------|----------|----------|
| **NONE** | 0 | CC0/public domain license with an official API designed for programmatic access. No terms restrict automated use. | Met Museum API, Smithsonian API, NGA Open Data |
| **LOW** | 1 | No explicit scraping prohibition found in terms of service. Site may have a JSON API or structured data endpoint. No active blocking (Cloudflare, CAPTCHA). | Leland Little (JSON API, no anti-scraping terms) |
| **MODERATE** | 2 | Terms of service are not publicly available, not retrievable (JS-rendered), or ambiguous. Site may have technical barriers (React SPA, client-side rendering) but no explicit legal prohibition. | Hilliard & Co. (no terms found), CTBids (React SPA, terms not retrievable) |
| **HIGH** | 3 | Terms of service **explicitly prohibit** automated access, robots, spiders, scrapers, data mining, or data extraction. Platform provider terms (Invaluable, HiBid, Auction Mobility) may apply. Site may actively block with Cloudflare/WAF. | Weschler's (Invaluable ToS), Quinn's (HiBid ToS), Alex Cooper (Auction Mobility ToS) |

## How to Assess a New Source

1. **Find the Terms of Service page**: Check `/terms`, `/terms-of-use`, `/tos`, `/legal`, or footer links.

2. **Search for prohibitory language**: Look for mentions of:
   - "robot", "spider", "scraper", "crawler"
   - "automated", "data mining", "data extraction"
   - "web harvesting", "systematic collection"
   - "robot exclusion headers", "robots.txt"

3. **Check the platform provider**: Many auction houses use third-party platforms (Invaluable, HiBid, Auction Mobility, LiveAuctioneers). The platform's ToS may apply even if the auction house's own terms are silent.

4. **Check for technical barriers**: Cloudflare protection, CAPTCHA, JavaScript-only rendering, rate limiting headers.

5. **Check the license**: CC0, Creative Commons, public domain, or "all rights reserved"?

6. **Check robots.txt**: Visit `https://example.com/robots.txt` for disallow rules.

7. **Assign the risk level** using the criteria table above.

## Configuring Sources in the Registry

### Setting the Maximum Risk Level

```python
from src.source_registry import RiskLevel
from src.data_loader import DataLoader

# Only use CC0/official API sources (safest)
loader = DataLoader(max_risk=RiskLevel.NONE)

# Include sources without explicit prohibition
loader = DataLoader(max_risk=RiskLevel.LOW)

# Include sources with unknown/ambiguous terms
loader = DataLoader(max_risk=RiskLevel.MODERATE)

# Include all sources (default — use at your own risk)
loader = DataLoader(max_risk=RiskLevel.HIGH)
```

### Registering Written Agreements

If you have negotiated written permission or an API access agreement with an auction house, register it to override the risk level:

```python
loader = DataLoader(max_risk=RiskLevel.NONE)

# This high-risk source is now allowed because you have a written agreement
loader.registry.set_agreement("weschlers", True)
loader.registry.set_agreement("alex_cooper", True)

# Verify
assert loader.registry.is_source_allowed("weschlers", max_risk=loader.max_risk)
```

### Configuring API Keys

For sources that require API keys (currently only Smithsonian):

```python
# The registry knows Smithsonian needs SMITHSONIAN_API_KEY env var
cfg = loader.registry.get("smithsonian")
assert cfg.requires_api_key  # True
assert cfg.api_key_env == "SMITHSONIAN_API_KEY"

# Set the GitHub Secrets name (for CI/CD documentation)
loader.registry.set_api_key_secret("smithsonian", "MY_ORG_SI_KEY")

# The key is read from the environment at runtime
import os
os.environ["SMITHSONIAN_API_KEY"] = "your-key-here"
assert cfg.get_api_key() == "your-key-here"
```

## Adding a New Source to the Registry

In `src/source_registry.py`, add to `DEFAULT_SOURCES`:

```python
"new_source": SourceConfig(
    key="new_source",
    name="New Auction House",
    source_type="scraper",       # "api", "scraper", "csv", "seed"
    risk_level=RiskLevel.HIGH,   # Assessed using criteria above
    license="Platform ToS",      # License or ToS that applies
    api_key_env="NEW_API_KEY",   # Only if API key required (None otherwise)
),
```

Then document the assessment in `notes/terms-of-service.md`.

## Reference: Current Source Risk Levels

| Source | Risk | License | Reason |
|--------|------|---------|--------|
| Seed Data | NONE | Internal | Local curated data |
| Met Museum API | NONE | CC0 | Official API, public domain |
| Smithsonian API | NONE | CC0 | Official API, CC0, requires key |
| NGA Open Data | NONE | CC0 | Official CSV download |
| Leland Little | LOW | Proprietary | No explicit prohibition, JSON API |
| Hilliard & Co. | MODERATE | Unknown | No public ToS found |
| CTBids | MODERATE | Unknown | Terms not retrievable (React SPA) |
| Weschler's | HIGH | Invaluable ToS | Explicitly prohibits robots/spiders |
| Quinn's | HIGH | HiBid ToS | Explicitly prohibits all scraping |
| Alex Cooper | HIGH | Auction Mobility ToS | Prohibits robots, data mining |
| Potomack | HIGH | Invaluable ToS | Explicitly prohibits + Cloudflare |
| Bunch | HIGH | Auction Mobility ToS | Prohibits robots, database creation |
| Headley's | HIGH | HiBid ToS | Explicitly prohibits all scraping |
