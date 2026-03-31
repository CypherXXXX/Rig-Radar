import re
import json
import random
import requests
from typing import Optional
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

def _get_headers(referer: str = "") -> dict:
    ua = random.choice(USER_AGENTS)
    h = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-CH-UA": '"Chromium";v="131", "Not_A Brand";v="24", "Google Chrome";v="131"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
    }
    if referer:
        h["Referer"] = referer
        h["Sec-Fetch-Site"] = "same-origin"
    return h

def _safe_get(url: str, referer: str = "", timeout: int = 20) -> Optional[str]:
    session = requests.Session()
    session.headers.update(_get_headers(referer))
    for attempt in range(3):
        try:
            if attempt > 0:
                session.headers.update(_get_headers(referer))
            r = session.get(url, timeout=timeout, allow_redirects=True)
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
    return None

def _pricehistory_lookup(product_url: str) -> dict:
    session = requests.Session()
    session.headers.update(_get_headers("https://pricehistory.app/"))
    session.headers["Content-Type"] = "application/json"
    session.headers["Origin"] = "https://pricehistory.app"
    try:
        r = session.post(
            "https://pricehistory.app/api/search",
            json={"url": product_url},
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("status") and data.get("code"):
                return {"slug": data["code"], "name": data.get("name", "")}
    except Exception:
        pass
    return {}

def _ph_extract_price(html: str) -> Optional[float]:
    pairs = re.findall(r'\[\s*\d{10,13}\s*,\s*(\d+(?:\.\d+)?)\s*\]', html)
    if pairs:
        try:
            prices = [float(p) for p in pairs if float(p) > 10]
            if prices:
                return prices[-1]
        except (ValueError, TypeError):
            pass

    for pat in [
        r'"currentPrice"\s*:\s*(\d+(?:\.\d+)?)',
        r'"latestPrice"\s*:\s*(\d+(?:\.\d+)?)',
        r'"price"\s*:\s*(\d+(?:\.\d+)?)',
    ]:
        m = re.search(pat, html)
        if m:
            try:
                val = float(m.group(1))
                if val > 10:
                    return val
            except (ValueError, TypeError):
                pass
    return None

PRICE_SELECTORS = {
    "amazon": [
        "span.a-price span.a-offscreen",
        "#corePrice_feature_div span.a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        "span.a-price-whole",
    ],
    "newegg": ["li.price-current"],
    "bestbuy": [".priceView-customer-price span"],
    "flipkart": [
        "div.Nx9bqj.CxhGGd",
        "div.Nx9bqj",
        "div._30jeq3",
        "div._1vC4OE",
    ],
}

def _parse_price(text: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d.]", "", text.replace(",", "").strip())
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

def _jsonld_price(soup: BeautifulSoup) -> Optional[float]:
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(tag.string)
            if isinstance(d, list):
                for item in d:
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        d = item
                        break
                else:
                    d = d[0] if d else {}
            if isinstance(d, dict):
                if d.get("@type") != "Product":
                    for item in d.get("@graph", []):
                        if isinstance(item, dict) and item.get("@type") == "Product":
                            d = item
                            break
                offers = d.get("offers", {})
                if isinstance(offers, list) and offers:
                    offers = offers[0]
                if isinstance(offers, dict):
                    for f in ("price", "lowPrice"):
                        v = offers.get(f)
                        if v:
                            p = float(v)
                            if p > 0:
                                return p
        except Exception:
            continue
    return None

def scrape_product(url: str, store: str) -> dict:
    price = None

    ph = _pricehistory_lookup(url)
    if ph.get("slug"):
        ph_html = _safe_get(
            f"https://pricehistory.app/p/{ph['slug']}",
            referer="https://pricehistory.app/",
        )
        if ph_html:
            price = _ph_extract_price(ph_html)

    if not price:
        html = _safe_get(url)
        if html:
            soup = BeautifulSoup(html, "lxml")
            price = _jsonld_price(soup)
            if not price:
                for sel in PRICE_SELECTORS.get(store, []):
                    el = soup.select_one(sel)
                    if el:
                        p = _parse_price(el.get_text())
                        if p and p > 0:
                            price = p
                            break

    return {"price": price}
