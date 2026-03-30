import re
import time
import random
import hashlib
import requests
from typing import Optional
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

CACHE_TTL = 86400

_cache: dict = {"data": [], "timestamp": 0}

AMAZON_BESTSELLER_URLS = [
    ("https://www.amazon.in/gp/bestsellers/computers/1375424031", "GPU"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375378031", "CPU"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375380031", "RAM"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375382031", "SSD"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375398031", "Monitor"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375406031", "Keyboard"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375408031", "Mouse"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375400031", "Headset"),
]

AMAZON_DEALS_URL = "https://www.amazon.in/gp/deals"

FLIPKART_SEED_URLS = [
    "https://www.flipkart.com/apple-iphone-15-blue-128-gb/p/itm6e3d0ab408a24",
    "https://www.flipkart.com/samsung-galaxy-s24-cobalt-violet-256-gb/p/itm49ae24f48d0c7",
    "https://www.flipkart.com/asus-rog-strix-g15-2023-ryzen-7-7745hx-16-gb-512-gb-ssd-windows-11-home-g513rc-hn063ws-gaming-laptop/p/itm0e7a9c8e85b5b",
    "https://www.flipkart.com/dell-inspiron-3520-intel-core-i5-1235u-8-gb-512-gb-ssd-windows-11-home-d560896win9b-thin-light-laptop/p/itm0567f562d1f5b",
    "https://www.flipkart.com/redmi-note-13-pro-fusion-white-256-gb/p/itm1e7a3ce4d1ce0",
    "https://www.flipkart.com/sony-wh-1000xm5-bluetooth-headset/p/itm9c2dc7bf3d0f2",
    "https://www.flipkart.com/samsung-65-cm-26-inch-full-hd-led-smart-television/p/itm03b1bebd4dcfe",
    "https://www.flipkart.com/one-plus-nord-ce-4-lite-5g-mega-blue-128-gb/p/itmd8f5186f86eae",
    "https://www.flipkart.com/lg-108-cm-43-inch-ultra-hd-4k-led-smart-oled-tv/p/itm1c18eb1f5c26a",
    "https://www.flipkart.com/boult-audio-airbass-propods-x-tws/p/itm7d8d8c3f1e3b2",
    "https://www.flipkart.com/hp-omen-16-ryzen-7-7745hx-16-gb-1-tb-ssd-windows-11-gaming-laptop/p/itm9c8d0c8e9d1a2",
    "https://www.flipkart.com/mi-smart-band-8-active/p/itm4c7b7c0d3c1e8",
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
        "Sec-CH-UA": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
    }
    if referer:
        h["Referer"] = referer
        h["Sec-Fetch-Site"] = "same-origin"
    return h

def _fetch(url: str, referer: str = "", timeout: int = 20) -> Optional[str]:
    session = requests.Session()
    session.headers.update(_get_headers(referer))
    for attempt in range(2):
        try:
            if attempt > 0:
                session.headers.update(_get_headers(referer))
            r = session.get(url, timeout=timeout, allow_redirects=True)
            r.raise_for_status()
            return r.text
        except Exception:
            pass
    return None

def _ph_search(product_url: str) -> dict:
    session = requests.Session()
    session.headers.update(_get_headers("https://pricehistory.app/"))
    session.headers["Content-Type"] = "application/json"
    try:
        r = session.post(
            "https://pricehistory.app/api/search",
            json={"url": product_url},
            timeout=12,
        )
        if r.ok:
            data = r.json()
            if data.get("status") and data.get("code"):
                return {"slug": data["code"], "name": data.get("name", "")}
    except Exception:
        pass
    return {}

def _ph_page_data(slug: str) -> dict:
    html = _fetch(f"https://pricehistory.app/p/{slug}", referer="https://pricehistory.app/")
    if not html or len(html) < 5000:
        return {}

    image = None
    try:
        soup = BeautifulSoup(html, "lxml")
        og = soup.find("meta", property="og:image")
        if og and og.get("content") and "placeholder" not in og["content"].lower():
            image = og["content"].strip()
    except Exception:
        pass

    current_price = None
    highest_price = None

    pairs = re.findall(r'\[\s*\d{10,13}\s*,\s*(\d+(?:\.\d+)?)\s*\]', html)
    if pairs:
        try:
            prices = [float(p) for p in pairs if float(p) > 10]
            if prices:
                current_price = prices[-1]
                highest_price = max(prices)
        except (ValueError, TypeError):
            pass

    if not current_price:
        for pat in [r'"currentPrice"\s*:\s*(\d+(?:\.\d+)?)', r'"latestPrice"\s*:\s*(\d+(?:\.\d+)?)']:
            m = re.search(pat, html)
            if m:
                try:
                    val = float(m.group(1))
                    if val > 10:
                        current_price = val
                        break
                except (ValueError, TypeError):
                    pass

    return {"image": image, "current_price": current_price, "highest_price": highest_price}

def _make_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:16]

def _parse_price(text: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d.]", "", text.replace(",", "").strip())
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

def _scrape_amazon_bestseller(url: str, category: str) -> Optional[dict]:
    html = _fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")

    items = soup.select("li.zg-item-immersion") or soup.select(".zg-grid-general-faceout")
    for item in items[:8]:
        try:
            name_el = item.select_one(".p13n-sc-truncate-desktop-type2") or item.select_one(".p13n-sc-truncated") or item.select_one("._cDEzb_p13n-sc-css-line-clamp-3_g3dy1")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name or len(name) < 8:
                continue

            price_el = item.select_one(".p13n-sc-price") or item.select_one("span.a-color-price")
            if not price_el:
                continue
            price = _parse_price(price_el.get_text())
            if not price or price < 500:
                continue

            img_el = item.select_one("img.s-image") or item.select_one("img.a-dynamic-image") or item.select_one("img")
            image = img_el.get("src", "") if img_el else ""
            if not image:
                continue

            link_el = item.select_one("a.a-link-normal[href*='/dp/']") or item.select_one("a[href*='/dp/']")
            if not link_el:
                continue
            href = link_el.get("href", "")
            dp_m = re.search(r"/dp/([A-Z0-9]{10})", href)
            if not dp_m:
                continue
            product_url = f"https://www.amazon.in/dp/{dp_m.group(1)}"

            return {
                "id": _make_id(product_url),
                "name": name[:150],
                "image": image,
                "url": product_url,
                "store": "Amazon",
                "price": price,
                "originalPrice": round(price * 1.15, 2),
                "discount": 0,
                "rating": 0.0,
                "reviews": 0,
                "category": category,
            }
        except Exception:
            continue
    return None

def _get_amazon_deals() -> list[dict]:
    html = _fetch(AMAZON_DEALS_URL)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    products = []

    cards = soup.select("div[data-component-type='s-search-result']") or soup.select(".DealCard-module__dealCard")
    for card in cards[:20]:
        try:
            name_el = card.select_one("h2 a span") or card.select_one("span.a-size-base-plus")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name or len(name) < 8:
                continue

            price_el = card.select_one("span.a-price span.a-offscreen") or card.select_one("span.a-price-whole")
            if not price_el:
                continue
            price = _parse_price(price_el.get_text())
            if not price or price < 500:
                continue

            orig_el = card.select_one("span.a-text-price span.a-offscreen")
            original = _parse_price(orig_el.get_text()) if orig_el else price
            if not original or original < price:
                original = price
            discount = round(((original - price) / original) * 100) if original > price else 0

            img_el = card.select_one("img.s-image") or card.select_one("img")
            image = img_el.get("src", "") if img_el else ""
            if not image:
                continue

            link_el = card.select_one("a[href*='/dp/']")
            if not link_el:
                continue
            dp_m = re.search(r"/dp/([A-Z0-9]{10})", link_el.get("href", ""))
            if not dp_m:
                continue
            product_url = f"https://www.amazon.in/dp/{dp_m.group(1)}"

            products.append({
                "id": _make_id(product_url),
                "name": name[:150],
                "image": image,
                "url": product_url,
                "store": "Amazon",
                "price": price,
                "originalPrice": original,
                "discount": discount,
                "rating": 0.0,
                "reviews": 0,
                "category": "Deal",
            })
            if len(products) >= 5:
                break
        except Exception:
            continue
    return products

def _get_amazon_trending(count: int = 5) -> list[dict]:
    products = _get_amazon_deals()
    if len(products) >= count:
        return products[:count]

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_scrape_amazon_bestseller, url, cat): cat for url, cat in AMAZON_BESTSELLER_URLS}
        for future in as_completed(futures):
            try:
                result = future.result(timeout=25)
                if result and result["id"] not in {p["id"] for p in products}:
                    products.append(result)
                    if len(products) >= count:
                        break
            except Exception:
                pass

    return products[:count]

def _get_flipkart_trending(count: int = 5) -> list[dict]:
    products = []

    def _process_flipkart_seed(url: str) -> Optional[dict]:
        try:
            ph = _ph_search(url)
            if not ph.get("slug"):
                return None
            page_data = _ph_page_data(ph["slug"])
            if not page_data.get("image") or not page_data.get("current_price"):
                return None

            current = page_data["current_price"]
            highest = page_data.get("highest_price") or current
            if highest < current:
                highest = current
            discount = round(((highest - current) / highest) * 100) if highest > current else 0

            return {
                "id": _make_id(url),
                "name": ph.get("name", "Unknown Product")[:150],
                "image": page_data["image"],
                "url": url,
                "store": "Flipkart",
                "price": current,
                "originalPrice": highest,
                "discount": discount,
                "rating": 0.0,
                "reviews": 0,
                "category": "Deal",
            }
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(_process_flipkart_seed, url): url for url in FLIPKART_SEED_URLS}
        results = []
        for future in as_completed(futures):
            try:
                result = future.result(timeout=20)
                if result:
                    results.append(result)
            except Exception:
                pass

    results.sort(key=lambda x: x.get("discount", 0), reverse=True)
    return results[:count]

def get_trending_products(force_refresh: bool = False) -> list[dict]:
    global _cache
    now = time.time()
    if not force_refresh and _cache["data"] and (now - _cache["timestamp"]) < CACHE_TTL:
        return _cache["data"]

    amazon_products = _get_amazon_trending(5)
    flipkart_products = _get_flipkart_trending(5)

    result = amazon_products + flipkart_products

    if result:
        _cache["data"] = result
        _cache["timestamp"] = now

    return result
