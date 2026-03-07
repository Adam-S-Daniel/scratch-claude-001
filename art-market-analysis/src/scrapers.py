"""Web scrapers for mid-Atlantic auction house past results.

Each scraper fetches past auction results from an auction house website and
returns them as a list of auction record dicts matching the AuctionRecord
schema: lot_number, title, artist, medium, date_sold, hammer_price,
auction_house, category.

Supported sites:
- Leland Little Auctions (lelandlittle.com) — custom Vue.js API
- Weschler's (weschlers.com) — past auctions page
- Quinn's Auction Galleries (quinnsauctions.com)
- Alex Cooper Auctioneers (alexcooper.com)
- Hilliard & Co. (hilliardandco.com)
- Potomack Company (potomackcompany.com)
- William Bunch Auctions (bunchauctions.com)
- Headley's Auctions (headleysauctions.com) — uses HiBid
- CTBids (ctbids.com) — estate sale platform
"""
from __future__ import annotations

import json
import re
from datetime import date
from html.parser import HTMLParser
from typing import List
from urllib.parse import quote, urljoin
from urllib.request import urlopen, Request
from urllib.error import URLError


# Category classification from description/title text
_CATEGORY_KEYWORDS = {
    "painting": [
        "oil on canvas", "oil on board", "oil on panel", "acrylic on canvas",
        "painting", "oil on", "acrylic",
    ],
    "works_on_paper": [
        "watercolor", "lithograph", "etching", "engraving", "print",
        "drawing", "pencil", "ink on paper", "charcoal",
    ],
    "furniture": [
        "table", "chair", "desk", "chest", "cabinet", "sideboard",
        "bookcase", "settee", "sofa", "bureau", "highboy", "lowboy",
        "mahogany", "walnut", "oak", "cherry",
    ],
    "decorative_arts": [
        "silver", "porcelain", "ceramic", "glass", "clock", "vase",
        "figurine", "lamp", "chandelier", "mirror", "rug", "carpet",
        "stoneware", "pottery", "pewter", "brass", "copper",
    ],
    "textile": [
        "quilt", "textile", "silk", "cotton", "needlework", "sampler",
        "tapestry", "coverlet", "rug",
    ],
    "sculpture": [
        "sculpture", "bronze", "marble", "statue", "bust", "figure",
        "carved",
    ],
}


def _classify_from_text(text: str) -> str:
    """Classify an item into a category based on title/description text."""
    text_lower = text.lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return category
    return "decorative_arts"


def _extract_artist(title: str) -> str:
    """Try to extract an artist name from a lot title.

    Common patterns:
    - "Artist Name (Nationality, dates), Title"
    - "Artist Name - Title"
    - "Attributed to Artist Name, Title"
    """
    title = title.strip()

    # Pattern: "Artist Name (dates/nationality), Title"
    match = re.match(r'^([^(]+?)\s*\([^)]+\)\s*[,;.]\s*', title)
    if match:
        return match.group(1).strip()

    # Pattern: "Artist Name, Title of Work"
    # Only if the first part looks like a name (2-4 words, capitalized)
    parts = title.split(",", 1)
    if len(parts) == 2:
        candidate = parts[0].strip()
        words = candidate.split()
        if 2 <= len(words) <= 5 and all(w[0].isupper() for w in words if w[0].isalpha()):
            return candidate

    return "Unknown Artist"


def _parse_price(price_str: str) -> float | None:
    """Parse a price string like '$1,500', '1500', 'USD 1,500' to float."""
    if not price_str:
        return None
    cleaned = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(cleaned)
    except ValueError:
        return None


def _fetch_html(url: str, timeout: int = 20) -> str:
    """Fetch HTML from a URL with a browser-like User-Agent."""
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; ArtMarketAnalysis/1.0)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _fetch_json_api(url: str, timeout: int = 20) -> dict:
    """Fetch JSON from an API endpoint."""
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; ArtMarketAnalysis/1.0)",
        "Accept": "application/json",
    })
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


class _LotHTMLParser(HTMLParser):
    """Generic HTML parser that extracts lot data from auction result pages.

    Looks for common patterns in auction house HTML:
    - Elements with classes containing 'lot', 'result', 'item'
    - Price values in common formats
    - Title/description text
    """

    def __init__(self) -> None:
        super().__init__()
        self.lots: List[dict] = []
        self._current_lot: dict | None = None
        self._capture_field: str | None = None
        self._text_buffer: str = ""

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attr_dict = dict(attrs)
        cls = attr_dict.get("class", "")

        # Detect lot containers
        if any(x in cls.lower() for x in ["lot-item", "lot_item", "auction-lot", "result-item", "catalog-item"]):
            if self._current_lot:
                self._finalize_lot()
            self._current_lot = {}

        if self._current_lot is not None:
            # Detect field containers
            if any(x in cls.lower() for x in ["lot-title", "lot_title", "item-title", "title"]):
                self._capture_field = "title"
                self._text_buffer = ""
            elif any(x in cls.lower() for x in ["lot-price", "lot_price", "hammer", "price", "sold"]):
                self._capture_field = "price"
                self._text_buffer = ""
            elif any(x in cls.lower() for x in ["lot-number", "lot_number", "lot-num"]):
                self._capture_field = "lot_number"
                self._text_buffer = ""
            elif any(x in cls.lower() for x in ["lot-desc", "description", "medium", "material"]):
                self._capture_field = "description"
                self._text_buffer = ""
            elif any(x in cls.lower() for x in ["artist", "maker", "creator"]):
                self._capture_field = "artist"
                self._text_buffer = ""

    def handle_data(self, data: str) -> None:
        if self._capture_field is not None:
            self._text_buffer += data

    def handle_endtag(self, tag: str) -> None:
        if self._capture_field and self._current_lot is not None:
            text = self._text_buffer.strip()
            if text:
                self._current_lot[self._capture_field] = text
            self._capture_field = None
            self._text_buffer = ""

    def _finalize_lot(self) -> None:
        if self._current_lot and self._current_lot.get("title"):
            self.lots.append(self._current_lot)
        self._current_lot = None

    def close(self) -> None:
        if self._current_lot:
            self._finalize_lot()
        super().close()


def _lot_dict_to_record(
    lot: dict, auction_house: str, sale_date: str | None = None,
) -> dict:
    """Convert a parsed lot dict to our auction record format."""
    title = lot.get("title", "Untitled")
    artist = lot.get("artist") or _extract_artist(title)
    medium = lot.get("description") or lot.get("medium") or "unknown"
    price = _parse_price(lot.get("price", ""))
    lot_number = lot.get("lot_number") or lot.get("lot") or "0"
    category = _classify_from_text(f"{title} {medium}")

    if price is None or price <= 0:
        return {}

    return {
        "lot_number": str(lot_number),
        "title": title,
        "artist": artist,
        "medium": medium,
        "date_sold": sale_date or date.today().isoformat(),
        "hammer_price": price,
        "auction_house": auction_house,
        "category": category,
    }


# ---- Per-site scrapers ----


def scrape_leland_little(max_results: int = 50) -> List[dict]:
    """Scrape past auction results from Leland Little Auctions.

    Leland Little uses a Vue.js frontend with a JSON API at /api.
    """
    try:
        url = "https://www.lelandlittle.com/api/lots/results?limit={}&offset=0".format(
            max_results
        )
        data = _fetch_json_api(url)
        lots = data if isinstance(data, list) else data.get("data", data.get("lots", []))

        records = []
        for lot in lots:
            if not isinstance(lot, dict):
                continue
            title = lot.get("title") or lot.get("name") or "Untitled"
            artist = lot.get("artist") or lot.get("maker") or _extract_artist(title)
            medium = lot.get("medium") or lot.get("description") or "unknown"
            price = lot.get("hammer_price") or lot.get("price") or lot.get("sold_price")
            if isinstance(price, str):
                price = _parse_price(price)
            if not price or price <= 0:
                continue

            lot_num = str(lot.get("lot_number") or lot.get("lot") or lot.get("id") or "0")
            sale_date = lot.get("sale_date") or lot.get("date") or date.today().isoformat()
            category = _classify_from_text(f"{title} {medium}")

            records.append({
                "lot_number": lot_num,
                "title": title,
                "artist": artist,
                "medium": medium,
                "date_sold": sale_date if isinstance(sale_date, str) else str(sale_date),
                "hammer_price": float(price),
                "auction_house": "Leland Little Auctions",
                "category": category,
            })
            if len(records) >= max_results:
                break

        return records
    except Exception:
        return []


def scrape_weschlers(max_results: int = 50) -> List[dict]:
    """Scrape past auction results from Weschler's.

    Weschler's partners with Invaluable and has a past-auctions page.
    """
    try:
        html = _fetch_html("https://www.weschlers.com/buy/past-auctions/")
        parser = _LotHTMLParser()
        parser.feed(html)
        parser.close()

        records = []
        for lot in parser.lots[:max_results]:
            record = _lot_dict_to_record(lot, "Weschler's")
            if record:
                records.append(record)

        return records
    except Exception:
        return []


def scrape_quinns(max_results: int = 50) -> List[dict]:
    """Scrape past auction results from Quinn's Auction Galleries."""
    try:
        html = _fetch_html("https://www.quinnsauction.com/past-auctions/")
        parser = _LotHTMLParser()
        parser.feed(html)
        parser.close()

        records = []
        for lot in parser.lots[:max_results]:
            record = _lot_dict_to_record(lot, "Quinn's Auction Galleries")
            if record:
                records.append(record)

        return records
    except Exception:
        return []


def scrape_alex_cooper(max_results: int = 50) -> List[dict]:
    """Scrape past auction results from Alex Cooper Auctioneers.

    Alex Cooper has past results accessible via LiveAuctioneers integration.
    """
    try:
        html = _fetch_html("https://www.alexcooper.com/auctions/past")
        parser = _LotHTMLParser()
        parser.feed(html)
        parser.close()

        records = []
        for lot in parser.lots[:max_results]:
            record = _lot_dict_to_record(lot, "Alex Cooper Auctioneers")
            if record:
                records.append(record)

        return records
    except Exception:
        return []


def scrape_hilliard(max_results: int = 50) -> List[dict]:
    """Scrape past auction results from Hilliard & Co."""
    try:
        html = _fetch_html("https://www.hilliardandco.com/past-auctions")
        parser = _LotHTMLParser()
        parser.feed(html)
        parser.close()

        records = []
        for lot in parser.lots[:max_results]:
            record = _lot_dict_to_record(lot, "Hilliard & Co.")
            if record:
                records.append(record)

        return records
    except Exception:
        return []


def scrape_potomack(max_results: int = 50) -> List[dict]:
    """Scrape past auction results from Potomack Company."""
    try:
        html = _fetch_html("https://www.potomackcompany.com/past-auctions")
        parser = _LotHTMLParser()
        parser.feed(html)
        parser.close()

        records = []
        for lot in parser.lots[:max_results]:
            record = _lot_dict_to_record(lot, "Potomack Company")
            if record:
                records.append(record)

        return records
    except Exception:
        return []


def scrape_bunch(max_results: int = 50) -> List[dict]:
    """Scrape past auction results from William Bunch Auctions."""
    try:
        html = _fetch_html("https://www.bunchauctions.com/past-auctions")
        parser = _LotHTMLParser()
        parser.feed(html)
        parser.close()

        records = []
        for lot in parser.lots[:max_results]:
            record = _lot_dict_to_record(lot, "William Bunch Auctions")
            if record:
                records.append(record)

        return records
    except Exception:
        return []


def scrape_headleys(max_results: int = 50) -> List[dict]:
    """Scrape past auction results from Headley's Auctions.

    Headley's uses HiBid for online auctions.
    """
    try:
        html = _fetch_html("https://headleysauctions.hibid.com/auctions/past")
        parser = _LotHTMLParser()
        parser.feed(html)
        parser.close()

        records = []
        for lot in parser.lots[:max_results]:
            record = _lot_dict_to_record(lot, "Headley's Auctions")
            if record:
                records.append(record)

        return records
    except Exception:
        return []


def scrape_ctbids(max_results: int = 50) -> List[dict]:
    """Scrape past auction results from CTBids.

    CTBids is a Caring Transitions franchise estate sale platform.
    Results are organized by location/sale.
    """
    try:
        html = _fetch_html("https://ctbids.com/estate-sales/past")
        parser = _LotHTMLParser()
        parser.feed(html)
        parser.close()

        records = []
        for lot in parser.lots[:max_results]:
            record = _lot_dict_to_record(lot, "CTBids")
            if record:
                records.append(record)

        return records
    except Exception:
        return []


# Registry of all scrapers for easy iteration
SCRAPERS = {
    "leland_little": {
        "function": scrape_leland_little,
        "auction_house": "Leland Little Auctions",
        "url": "https://www.lelandlittle.com",
    },
    "weschlers": {
        "function": scrape_weschlers,
        "auction_house": "Weschler's",
        "url": "https://www.weschlers.com",
    },
    "quinns": {
        "function": scrape_quinns,
        "auction_house": "Quinn's Auction Galleries",
        "url": "https://www.quinnsauction.com",
    },
    "alex_cooper": {
        "function": scrape_alex_cooper,
        "auction_house": "Alex Cooper Auctioneers",
        "url": "https://www.alexcooper.com",
    },
    "hilliard": {
        "function": scrape_hilliard,
        "auction_house": "Hilliard & Co.",
        "url": "https://www.hilliardandco.com",
    },
    "potomack": {
        "function": scrape_potomack,
        "auction_house": "Potomack Company",
        "url": "https://www.potomackcompany.com",
    },
    "bunch": {
        "function": scrape_bunch,
        "auction_house": "William Bunch Auctions",
        "url": "https://www.bunchauctions.com",
    },
    "headleys": {
        "function": scrape_headleys,
        "auction_house": "Headley's Auctions",
        "url": "https://headleysauctions.hibid.com",
    },
    "ctbids": {
        "function": scrape_ctbids,
        "auction_house": "CTBids",
        "url": "https://ctbids.com",
    },
}


def scrape_all(
    sites: List[str] | None = None,
    max_per_site: int = 50,
) -> List[dict]:
    """Run scrapers for multiple auction house sites.

    Args:
        sites: List of scraper keys to run (e.g. ["leland_little", "weschlers"]).
            If None, runs all scrapers.
        max_per_site: Maximum results per site.

    Returns:
        Combined list of auction record dicts from all scrapers.
    """
    if sites is None:
        sites = list(SCRAPERS.keys())

    all_records = []
    for site_key in sites:
        scraper = SCRAPERS.get(site_key)
        if scraper is None:
            continue
        try:
            records = scraper["function"](max_results=max_per_site)
            all_records.extend(records)
        except Exception:
            continue

    return all_records
