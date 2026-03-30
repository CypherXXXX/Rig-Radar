import re
import json
import random
import requests
from urllib.parse import urlparse
from typing import Optional
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

STORE_DETECTION_PATTERNS = {
    "amazon": ["amazon.com", "amazon.in", "amazon.co.uk", "amzn.in", "amzn.com"],
    "newegg": ["newegg.com"],
    "bestbuy": ["bestbuy.com"],
    "flipkart": ["flipkart.com"],
}

def detect_store(url: str) -> Optional[str]:
    hostname = urlparse(url).hostname or ""
    for store, patterns in STORE_DETECTION_PATTERNS.items():
        for pattern in patterns:
            if pattern in hostname:
                return store
    return None

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
        "Sec-CH-UA": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
    }
    if referer:
        h["Referer"] = referer
        h["Sec-Fetch-Site"] = "same-origin"
    return h

def _safe_get(url: str, referer: str = "", timeout: int = 20) -> Optional[requests.Response]:
    session = requests.Session()
    session.headers.update(_get_headers(referer))
    for attempt in range(3):
        try:
            if attempt > 0:
                session.headers.update(_get_headers(referer))
            r = session.get(url, timeout=timeout, allow_redirects=True)
            r.raise_for_status()
            return r
        except Exception:
            pass
    return None

def _safe_post(url: str, payload: dict, referer: str = "") -> Optional[requests.Response]:
    session = requests.Session()
    session.headers.update(_get_headers(referer))
    session.headers["Content-Type"] = "application/json"
    try:
        r = session.post(url, json=payload, timeout=15)
        r.raise_for_status()
        return r
    except Exception:
        return None

def _pricehistory_lookup(product_url: str) -> dict:
    r = _safe_post(
        "https://pricehistory.app/api/search",
        {"url": product_url},
        referer="https://pricehistory.app/",
    )
    if r:
        try:
            data = r.json()
            if data.get("status") and data.get("code"):
                return {"slug": data["code"], "name": data.get("name", "")}
        except Exception:
            pass
    return {}

def _pricehistory_page(slug: str) -> Optional[str]:
    r = _safe_get(f"https://pricehistory.app/p/{slug}", referer="https://pricehistory.app/")
    if r and len(r.text) > 5000:
        return r.text
    return None

def _ph_extract_image(html: str) -> Optional[str]:
    try:
        soup = BeautifulSoup(html, "lxml")
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            img = og["content"].strip()
            if img and "placeholder" not in img.lower():
                return img
    except Exception:
        pass
    return None

def _ph_extract_price(html: str) -> Optional[float]:
    pairs = re.findall(r'\[\s*\d{10,13}\s*,\s*(\d+(?:\.\d+)?)\s*\]', html)
    if pairs:
        try:
            val = float(pairs[-1])
            if val > 10:
                return val
        except (ValueError, TypeError):
            pass

    for pat in [
        r'"currentPrice"\s*:\s*(\d+(?:\.\d+)?)',
        r'"latestPrice"\s*:\s*(\d+(?:\.\d+)?)',
        r'"current_price"\s*:\s*(\d+(?:\.\d+)?)',
    ]:
        m = re.search(pat, html)
        if m:
            try:
                val = float(m.group(1))
                if val > 10:
                    return val
            except (ValueError, TypeError):
                pass

    chart_m = re.search(r'(?:chartData|priceData)\s*[=:]\s*(\[[\s\S]{5,8000}?\])\s*[;,\n]', html)
    if chart_m:
        try:
            data = json.loads(chart_m.group(1))
            if isinstance(data, list) and data:
                last = data[-1]
                if isinstance(last, (int, float)):
                    return float(last)
                if isinstance(last, list) and len(last) >= 2:
                    return float(last[1])
                if isinstance(last, dict):
                    for k in ("y", "price", "value"):
                        if last.get(k):
                            return float(last[k])
        except Exception:
            pass
    return None

PRICE_SELECTORS = {
    "amazon": [
        "span.a-price span.a-offscreen",
        "#corePrice_feature_div span.a-offscreen",
        "#corePriceDisplay_desktop_feature_div span.a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        "span.a-price-whole",
    ],
    "newegg": ["li.price-current", ".price-current strong"],
    "bestbuy": [".priceView-customer-price span"],
    "flipkart": ["div.Nx9bqj", "div._30jeq3", "div._1vC4OE"],
}

TITLE_SELECTORS = {
    "amazon": ["#productTitle", "h1#title span"],
    "newegg": [".product-title"],
    "bestbuy": [".sku-title h1", ".sku-title"],
    "flipkart": ["span.VU-ZEz", "span.B_NuCI", "h1._9E25nV"],
}

IMAGE_SELECTORS = {
    "amazon": [
        {"s": "#landingImage", "a": "src"},
        {"s": "#imgBlkFront", "a": "src"},
        {"s": "img[data-old-hires]", "a": "data-old-hires"},
        {"s": "#main-image-container img", "a": "src"},
    ],
    "newegg": [{"s": ".product-view-img-original", "a": "src"}],
    "bestbuy": [{"s": ".primary-image", "a": "src"}],
    "flipkart": [
        {"s": "img._396cs4", "a": "src"},
        {"s": "img.DByuf4", "a": "src"},
        {"s": "img.qqDXDz", "a": "src"},
    ],
}

def _parse_price(text: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d.]", "", text.replace(",", "").strip())
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

def _jsonld_product(soup: BeautifulSoup) -> Optional[dict]:
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(tag.string)
            if isinstance(d, list):
                for item in d:
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        return item
                d = d[0] if d else {}
            if isinstance(d, dict):
                if d.get("@type") == "Product":
                    return d
                for item in d.get("@graph", []):
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        return item
        except Exception:
            continue
    return None

def _amazon_image_from_script(soup: BeautifulSoup) -> Optional[str]:
    for script in soup.find_all("script", type="text/javascript"):
        txt = script.string or ""
        if "colorImages" in txt or "ImageBlockATF" in txt:
            m = re.search(r'"hiRes"\s*:\s*"(https://[^"]+)"', txt)
            if m:
                return m.group(1)
            m = re.search(r'"large"\s*:\s*"(https://[^"]+)"', txt)
            if m:
                return m.group(1)
    return None

def _fallback_scrape(url: str, store: str) -> dict:
    r = _safe_get(url)
    if not r:
        return {}
    soup = BeautifulSoup(r.text, "lxml")

    price = None
    jd = _jsonld_product(soup)
    if jd:
        offers = jd.get("offers", {})
        if isinstance(offers, list) and offers:
            offers = offers[0]
        if isinstance(offers, dict):
            for f in ("price", "lowPrice"):
                v = offers.get(f)
                if v:
                    try:
                        p = float(v)
                        if p > 0:
                            price = p
                            break
                    except (ValueError, TypeError):
                        pass
    if not price:
        for sel in PRICE_SELECTORS.get(store, []):
            el = soup.select_one(sel)
            if el:
                p = _parse_price(el.get_text())
                if p and p > 0:
                    price = p
                    break

    name = None
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        t = re.sub(r"\s*[-|:]\s*(Amazon\.|Flipkart|Newegg|Best Buy).*$", "", og["content"], flags=re.IGNORECASE).strip()
        if t and len(t) > 5:
            name = t[:200]
    if not name and jd and jd.get("name"):
        name = jd["name"][:200]
    if not name:
        for sel in TITLE_SELECTORS.get(store, []):
            el = soup.select_one(sel)
            if el:
                t = el.get_text().strip()
                if t:
                    name = t[:200]
                    break

    image = None
    if store == "amazon":
        image = _amazon_image_from_script(soup)
    if not image:
        for cfg in IMAGE_SELECTORS.get(store, []):
            el = soup.select_one(cfg["s"])
            if el:
                src = el.get(cfg["a"])
                if src and "placeholder" not in src.lower():
                    if store == "amazon":
                        src = re.sub(r"\._[A-Z]+\d+_", "._SL500_", src)
                    image = src
                    break
    if not image:
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img.get("content"):
            image = og_img["content"]
    if not image and jd:
        img = jd.get("image")
        if isinstance(img, str):
            image = img
        elif isinstance(img, list) and img:
            image = img[0]
        elif isinstance(img, dict):
            image = img.get("url")

    return {"price": price, "name": name, "image": image}

def extract_product_metadata(url: str) -> dict:
    store = detect_store(url)
    if not store:
        raise ValueError(f"Unsupported store URL: {url}")

    name = image = price = None

    ph = _pricehistory_lookup(url)
    if ph.get("slug"):
        name = ph.get("name") or None
        ph_html = _pricehistory_page(ph["slug"])
        if ph_html:
            image = _ph_extract_image(ph_html)
            price = _ph_extract_price(ph_html)

    if not (name and image and price):
        fb = _fallback_scrape(url, store)
        name = name or fb.get("name")
        image = image or fb.get("image")
        price = price or fb.get("price")

    return {
        "store": store,
        "product_name": name or "Unknown Product",
        "product_image_url": image or "",
        "current_price": price,
    }
