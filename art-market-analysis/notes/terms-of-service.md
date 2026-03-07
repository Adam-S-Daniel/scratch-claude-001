# Art Market Analysis — Data Source Terms of Service

This document summarizes the terms of use, licensing, and legal considerations for each data source used by the app. Last reviewed: 2026-03-07.

---

## Museum APIs & Open Data (CC0 Sources)

### 1. Metropolitan Museum of Art Collection API

- **URL**: https://metmuseum.github.io/
- **Full Terms**: https://www.metmuseum.org/information/terms-and-conditions
- **License**: Creative Commons Zero (CC0) for public domain works
- **API Key**: Not required
- **Rate Limit**: 80 requests per second
- **Attribution**: Not legally required under CC0, but the Met requests citation with URL `www.metmuseum.org` as you would any source
- **Commercial Use**: Allowed for CC0-designated works
- **Restrictions**:
  - Works NOT marked as public domain (`isPublicDomain: false`) are restricted to noncommercial, educational, and personal use only
  - Must retain copyright notices on non-public-domain works
  - Must not imply Met endorsement
  - Third-party copyrights (e.g., ARS-represented artists) require separate permission regardless
- **Automated Access**: No explicit prohibition of API use (that's the API's purpose). Terms say users must "use the Websites for lawful purposes only"
- **Our Compliance**: We only fetch metadata (title, artist, medium, classification) through the official API. We do not scrape the website or download images. We respect the rate limit.

### 2. Smithsonian Open Access API

- **URL**: https://www.si.edu/openaccess
- **Full Terms**: https://www.si.edu/termsofuse
- **FAQ**: https://www.si.edu/openaccess/faq
- **License**: Creative Commons Zero (CC0) for designated items (5.1M+ items)
- **API Key**: Required — free from https://api.data.gov
- **Rate Limit**: Default 1,000 requests per hour (api.data.gov default). Exceeding the limit temporarily blocks the API key for up to one hour. Higher limits available by contacting the agency.
- **Attribution**: Not legally required under CC0, but Smithsonian recommends a minimal caption: title, author, source, license, and source URL
- **Commercial Use**: Allowed for CC0-designated items, without fee or permission
- **Restrictions**:
  - CC0 only covers copyright — other rights (publicity, privacy, trademark) may still apply
  - Content NOT marked CC0 is restricted to personal, educational, and non-commercial use under fair use (Section 108 U.S. Copyright Act)
  - The Smithsonian does not guarantee that all CC0 content is free from third-party rights
- **Automated Access**: API is designed for automated access. Must use an API key for tracking.
- **Our Compliance**: We use the official API with an API key. We only fetch CC0-designated metadata. We respect api.data.gov rate limits.

### 3. National Gallery of Art Open Data

- **URL**: https://github.com/NationalGalleryOfArt/opendata
- **License**: Creative Commons Zero (CC0 1.0)
- **API Key**: Not required (direct CSV download from GitHub)
- **Rate Limit**: GitHub's standard rate limits apply to raw file downloads
- **Attribution**: Not legally required, but NGA requests: "Please consider providing attribution to or citing the National Gallery of Art's Collection Dataset"
- **Commercial Use**: Allowed under CC0
- **Restrictions**:
  - Dataset is "as is" with no warranties — may contain inaccuracies or incomplete data
  - Do NOT use the National Gallery's logo or claim NGA endorsement without written permission
  - The dataset contains references/links to images but does NOT include actual image files
  - Wikidata identifiers included may not be exhaustive
- **Automated Access**: Data is published as static CSV files for download — automated download is the intended use
- **Our Compliance**: We download the CSV file, filter to American artworks, and extract metadata only. No images downloaded. No logo usage.

---

## Auction House Websites (Scraped Sources)

**Important legal context**: Web scraping of auction house websites carries significant legal risk. Most auction houses and their platform providers explicitly prohibit automated data collection in their terms of service. The scrapers in this project are provided for educational and research purposes. Users should review the applicable terms before running scrapers against live sites.

### Legal Precedents

- **eBay v. Bidder's Edge (2000)**: Court ruled that automated scraping of auction listings constituted trespass to chattels, issuing an injunction against the scraper.
- **Meta v. Bright Data (2024)**: Court ruled that scraping public data while logged out may not be bound by browsewrap ToS since no contract was formed.
- **General principle**: Terms of service violations may not always lead to criminal liability, but they can result in civil action, IP blocking, and account termination.

### 4. Leland Little Auctions (lelandlittle.com)

- **Terms**: https://www.lelandlittle.com/terms-and-conditions/
- **Platform**: Custom Vue.js frontend with JSON API
- **Scraping Policy**: Terms and conditions focus on auction sale terms (bidding, payment, shipping). No explicit web scraping prohibition was found in the indexed terms. However, the absence of explicit permission does not imply consent.
- **Our Approach**: Uses their JSON API endpoint. Most permissive of the scraped sites.

### 5. Weschler's (weschlers.com)

- **Terms**: https://www.weschlers.com/terms-conditions/
- **Platform**: Powered by Invaluable, LLC
- **Scraping Policy**: Weschler's own terms focus on auction conditions. However, because the site is powered by **Invaluable**, Invaluable's terms also apply (see below). The site returns 403 errors to automated requests (Cloudflare protection), which is itself a technical indication that automated access is not welcome.
- **Invaluable Terms (Section 5.2)**: "you will not use any robot, spider, other automatic device, or manual process to monitor or copy [our] web pages or the content contained herein without [our] prior expressed written permission"
- **Risk Level**: HIGH — explicit prohibition via Invaluable platform terms + active Cloudflare blocking.

### 6. Quinn's Auction Galleries (quinnsauction.com)

- **Terms**: http://www.quinnsauction.com/index.php/buyerssellers/terms-conditions-2/ (content listed as "coming soon")
- **Platform**: HiBid (402 Ventures, LLC)
- **HiBid Terms (Section 9)**: Explicitly prohibits "any robot, spider, scraper, data mining tool, data gathering tools, data extraction tools, or any other automated means to access our Sites or Services." Also prohibits: "conduct any web scraping, web harvesting, web data extraction, or any other data scraping." Users must not "bypass any measures [HiBid] may use to prevent or restrict access to [their] Services, including [their] robot exclusion headers."
- **Risk Level**: HIGH — HiBid's terms explicitly ban all forms of scraping, and the site uses client-side JavaScript rendering that blocks HTML scrapers anyway.

### 7. Alex Cooper Auctioneers (alexcooper.com)

- **Terms**: https://www.alexcooper.com/terms-and-conditions-of-sale
- **Platform**: Auction Mobility, LLC (bidding at bid.alexcooper.com)
- **Auction Mobility Terms**: Prohibit use of "any robot, spider, site search/retrieval application or other manual or automatic device or process to retrieve, index, 'data mine' or in any way reproduce or circumvent the navigational structure or presentation." Also prohibit using content to "directly or indirectly create or contribute to the development of any database or product."
- **Risk Level**: HIGH — Auction Mobility platform terms explicitly prohibit scraping and database creation from their data.

### 8. Hilliard & Co. (hilliardandco.com)

- **Terms**: No publicly indexed terms of service found
- **Platform**: Squarespace website; past results likely on LiveAuctioneers
- **Scraping Policy**: No explicit terms found. LiveAuctioneers (if used for results) likely has its own scraping prohibitions.
- **Risk Level**: MODERATE — no explicit prohibition found, but absence of terms doesn't mean consent.

### 9. Potomack Company (potomackcompany.com)

- **Terms**: https://www.potomackcompany.com/privacy-policy/ (privacy only; no standalone ToS found)
- **Platform**: Powered by Invaluable, LLC
- **Scraping Policy**: Same as Weschler's — Invaluable's terms (Section 5.2) explicitly prohibit robots, spiders, and automated monitoring/copying. Site also returns 403 errors via Cloudflare.
- **Risk Level**: HIGH — Invaluable prohibition + active blocking.

### 10. William Bunch Auctions (bunchauctions.com)

- **Terms**: https://www.bunchauctions.com/policies
- **Platform**: Auction Mobility, LLC (bidding at bid.bunchauctions.com)
- **Auction Mobility Terms**: Same as Alex Cooper — prohibit robots, spiders, data mining, and database creation from platform content.
- **Risk Level**: HIGH — Auction Mobility terms explicitly prohibit scraping.

### 11. Headley's Auctions (headleysauctions.com → headleysauctions.hibid.com)

- **Terms**: https://hibid.com/home/termsofuse
- **Platform**: HiBid (402 Ventures, LLC)
- **Scraping Policy**: Same as Quinn's — HiBid terms (Section 9) explicitly ban all scraping, web harvesting, data extraction, robots, spiders, and scrapers. Also prohibits bypassing robot exclusion headers.
- **Risk Level**: HIGH — explicit ban + client-side JS rendering blocks HTML scrapers.

### 12. CTBids (ctbids.com)

- **Terms**: https://ctbids.com/terms (React SPA — content not indexable by search engines)
- **Platform**: Caring Transitions proprietary React application
- **Scraping Policy**: Full terms could not be retrieved (JavaScript-rendered page). As a React SPA, the site itself is resistant to HTML scraping.
- **Risk Level**: MODERATE-HIGH — terms not retrievable but the React SPA architecture itself prevents scraping. Standard industry practice is to prohibit automated access.

---

## Summary Table

| Source | License | Auth | Scraping Allowed? | Risk |
|--------|---------|------|--------------------|------|
| Met Museum API | CC0 | None | Yes (official API) | None |
| Smithsonian API | CC0 | API key | Yes (official API) | None |
| NGA Open Data | CC0 | None | Yes (CSV download) | None |
| Leland Little | Proprietary | None | No explicit prohibition found | Low |
| Weschler's | Invaluable ToS | None | **Explicitly prohibited** | High |
| Quinn's | HiBid ToS | None | **Explicitly prohibited** | High |
| Alex Cooper | Auction Mobility ToS | None | **Explicitly prohibited** | High |
| Hilliard | Unknown | None | No terms found | Moderate |
| Potomack | Invaluable ToS | None | **Explicitly prohibited** | High |
| Bunch | Auction Mobility ToS | None | **Explicitly prohibited** | High |
| Headley's | HiBid ToS | None | **Explicitly prohibited** | High |
| CTBids | Unknown (React SPA) | None | Terms not retrievable | Moderate-High |

## Recommendations

1. **Museum APIs are safe to use freely** — all three are CC0 with official APIs/downloads designed for programmatic access.

2. **Auction house scrapers should be used with caution**:
   - 6 of 9 sites explicitly prohibit automated scraping in their platform terms
   - 2 sites actively block automated requests (Cloudflare 403)
   - Consider using aggregator APIs (Invaluable, LiveAuctioneers) with proper API agreements instead of direct scraping
   - For research/educational use, mock data or the seed dataset may be sufficient

3. **If scraping for production use**: Obtain written permission from each auction house, or negotiate API access through their platform providers (Invaluable, HiBid, Auction Mobility).

4. **Attribution**: While CC0 doesn't legally require it, all three museum sources request attribution/citation. Include source information in any published analysis.

---

*This document is for informational purposes only and does not constitute legal advice. Terms of service change frequently — verify current terms before relying on this summary.*
