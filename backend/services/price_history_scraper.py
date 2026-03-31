import re
import random
import hashlib
import time as _time
import requests
from typing import Optional
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

def _get_headers(referer: str = "") -> dict:
    ua = random.choice(USER_AGENTS)
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-CH-UA": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
    }
    if referer:
        headers["Referer"] = referer
        headers["Sec-Fetch-Site"] = "same-origin"
    return headers

_raw_cache: dict = {}
RAW_CACHE_TTL = 3600 * 6

def extract_asin(url: str) -> Optional[str]:
    patterns = [
        r"/dp/([A-Z0-9]{10})",
        r"/product/([A-Z0-9]{10})",
        r"/gp/product/([A-Z0-9]{10})",
        r"asin=([A-Z0-9]{10})",
    ]
    for p in patterns:
        m = re.search(p, url, re.IGNORECASE)
        if m:
            return m.group(1).upper()
    return None

def _fetch_page(url: str, timeout: int = 20, referer: str = "") -> str:
    session = requests.Session()
    session.headers.update(_get_headers(referer))
    last_error = None
    for attempt in range(3):
        try:
            if attempt > 0:
                session.headers.update(_get_headers(referer))
            response = session.get(url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()
            return response.text
        except Exception as e:
            last_error = e
    raise last_error

def _find_product_slug(asin: Optional[str], product_url: str = "") -> Optional[str]:
    lookup_url = product_url
    if asin:
        if not lookup_url or ("amazon.in" not in lookup_url and "amazon.com" not in lookup_url):
            lookup_url = f"https://www.amazon.in/dp/{asin}"
        dp_match = re.search(r"/dp/([A-Z0-9]{10})", lookup_url, re.IGNORECASE)
        if dp_match:
            lookup_url = f"https://www.amazon.in/dp/{dp_match.group(1)}"

    if not lookup_url:
        return None

    try:
        session = requests.Session()
        session.headers.update(_get_headers())
        session.get("https://pricehistory.app", timeout=10)
        resp = session.post(
            "https://pricehistory.app/api/search",
            json={"url": lookup_url},
            timeout=15,
            headers={
                "Referer": "https://pricehistory.app/",
                "Origin": "https://pricehistory.app",
                "Content-Type": "application/json",
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") and data.get("code"):
                return data["code"]
    except Exception:
        pass

    return None

def _extract_raw_price_points(html: str) -> list[dict]:
    pairs = re.findall(r'\[\s*(\d{10,13})\s*,\s*(\d+(?:\.\d+)?)\s*\]', html)
    if not pairs:
        return []

    points = []
    for ts_str, price_str in pairs:
        try:
            ts_val = int(ts_str)
            price_val = float(price_str)
            if price_val <= 10:
                continue
            if ts_val > 9999999999:
                ts_val = ts_val // 1000
            dt = datetime.fromtimestamp(ts_val, tz=timezone.utc)
            points.append({
                "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "price": price_val,
                "_epoch": ts_val,
            })
        except (ValueError, TypeError, OSError):
            continue

    points.sort(key=lambda x: x["_epoch"])
    return points

def _scrape_pricehistory_page_stats(html: str) -> dict:
    stats = {}
    try:
        soup = BeautifulSoup(html, "lxml")
        full_text = soup.get_text(" ", strip=True)

        for label, key in [("Highest", "highest"), ("Lowest", "lowest"), ("Average", "average")]:
            for pattern in [
                rf'{label}[\s\w]*[Pp]rice\s*[:\s]*(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)',
                rf'{label}[\s\w]*[Pp]rice\s*[:\s]*([\d,]+(?:\.\d+)?)',
                rf'{label}\s*[:\s]*(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)',
                rf'(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)\s*{label}',
            ]:
                m = re.search(pattern, full_text, re.IGNORECASE)
                if m:
                    cleaned = m.group(1).replace(",", "")
                    try:
                        val = float(cleaned)
                        if val > 0:
                            stats[key] = val
                            break
                    except (ValueError, TypeError):
                        pass
    except Exception:
        pass
    return stats

def _scrape_all_pricehistory_data(slug: str) -> tuple[list[dict], dict]:
    try:
        html = _fetch_page(
            f"https://pricehistory.app/p/{slug}",
            referer="https://pricehistory.app/"
        )
        if len(html) < 5000:
            return [], {}

        raw_points = _extract_raw_price_points(html)
        page_stats = _scrape_pricehistory_page_stats(html)

        return raw_points, page_stats
    except Exception:
        return [], {}

def _filter_points_by_period(points: list[dict], months: int) -> list[dict]:
    if not points:
        return []
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=months * 30)
    cutoff_epoch = int(cutoff.timestamp())
    return [p for p in points if p.get("_epoch", 0) >= cutoff_epoch]

def _compute_stats_from_points(points: list[dict], current_price: float = 0) -> dict:
    prices = [p["price"] for p in points if p.get("price") and p["price"] > 0]
    if current_price and current_price > 0:
        prices.append(current_price)
    if not prices:
        return {}
    return {
        "highest": max(prices),
        "lowest": min(prices),
        "average": round(sum(prices) / len(prices), 2),
    }

def _clean_points_for_response(points: list[dict]) -> list[dict]:
    cleaned = []
    seen_dates = set()
    for p in points:
        date_key = p["timestamp"][:10]
        if date_key not in seen_dates:
            seen_dates.add(date_key)
            cleaned.append({
                "timestamp": p["timestamp"],
                "price": p["price"],
            })
    return cleaned

def fetch_external_price_history(
    product_url: str,
    months: int = 6,
    current_price: float = 0,
    product_name: str = "",
) -> tuple[list[dict], dict]:
    global _raw_cache

    current_price = float(current_price) if current_price else 0.0

    asin = extract_asin(product_url)
    product_key = asin if asin else hashlib.md5(product_url.encode()).hexdigest()[:10]
    cache_key = f"{product_key}_raw"

    now = _time.time()
    all_points = []
    page_stats = {}

    if cache_key in _raw_cache:
        cached = _raw_cache[cache_key]
        if now - cached["ts"] < RAW_CACHE_TTL:
            all_points = cached["points"]
            page_stats = cached["page_stats"]

    if not all_points:
        slug = _find_product_slug(asin, product_url)
        if slug:
            all_points, page_stats = _scrape_all_pricehistory_data(slug)
            if all_points:
                _raw_cache[cache_key] = {
                    "points": all_points,
                    "page_stats": page_stats,
                    "ts": now,
                }

    if all_points:
        filtered = _filter_points_by_period(all_points, months)
        if not filtered and all_points:
            filtered = all_points[-5:]

        if page_stats.get("highest") and page_stats.get("lowest"):
            stats = {
                "highest": page_stats["highest"],
                "lowest": page_stats["lowest"],
                "average": page_stats.get("average", round(
                    (page_stats["highest"] + page_stats["lowest"]) / 2, 2
                )),
            }
        else:
            stats = _compute_stats_from_points(filtered, current_price)

        if not stats.get("highest"):
            stats = _compute_stats_from_points(filtered, current_price)

        history = _clean_points_for_response(filtered)
        return history, stats

    if current_price and current_price > 0:
        if page_stats.get("highest") and page_stats.get("lowest"):
            stats = {
                "highest": page_stats["highest"],
                "lowest": page_stats["lowest"],
                "average": page_stats.get("average", current_price),
                "current": current_price,
            }
        else:
            stats = {
                "highest": current_price,
                "lowest": current_price,
                "average": current_price,
                "current": current_price,
            }
        now_ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        history = [{"timestamp": now_ts, "price": current_price}]
        return history, stats

    return [], {}
