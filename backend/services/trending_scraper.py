import re
import time
import json
import random
import hashlib
import requests
from typing import Optional
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

CACHE_TTL = 3600

_cache: dict = {"data": [], "timestamp": 0}

AMAZON_SEED_PRODUCTS = [
    ("B0D1SJ5HSJ", "GPU"),
    ("B0CX23V2ZK", "CPU"),
    ("B0CZLGTFMF", "GPU"),
    ("B0D5J3D27K", "CPU"),
    ("B09HN37XDX", "SSD"),
    ("B0CHX1W1XY", "Laptop"),
    ("B0BT4JTK5J", "Laptop"),
    ("B07XVMDJQW", "Monitor"),
    ("B0C7K5N42C", "RAM"),
    ("B09HSCSQYJ", "Keyboard"),
    ("B08N5WRWNW", "Mouse"),
    ("B09NVPTQPM", "Headset"),
    ("B0GPVVYKTQ", "Tablet"),
    ("B09WMH6LYB", "Earphones"),
    ("B0DGHW8ZPQ", "GPU"),
    ("B0DJHJ3QK8", "Mouse"),
    ("B0D9R7GCK1", "SSD"),
    ("B0DQJYM3DM", "Monitor"),
    ("B0CQKDFZK8", "Laptop"),
    ("B0CY4NRZHV", "RAM"),
]

FLIPKART_SEED_PRODUCTS = [
    ("https://www.flipkart.com/apple-iphone-15-blue-128-gb/p/itm6e3d0ab408a24", "Phone"),
    ("https://www.flipkart.com/samsung-galaxy-s24-ultra-titanium-gray-256-gb/p/itm583e42bb1d98b", "Phone"),
    ("https://www.flipkart.com/apple-macbook-air-m2-8-gb-256-gb-ssd-mac-os-monterey-mly33hn-a/p/itm45b5f5db55963", "Laptop"),
    ("https://www.flipkart.com/samsung-galaxy-s23-fe-mint-128-gb/p/itm29f27f8dfe6e1", "Phone"),
    ("https://www.flipkart.com/asus-vivobook-15-intel-core-i5-12th-gen-1235u-8-gb-512-gb-ssd-windows-11-home-x1502za-ej532ws-laptop/p/itm1a8f0f53b5506", "Laptop"),
    ("https://www.flipkart.com/sony-wh-1000xm5-bluetooth-headset/p/itm9c2dc7bf3d0f2", "Headset"),
    ("https://www.flipkart.com/dell-inspiron-3520-intel-core-i5-1235u-8-gb-512-gb-ssd-windows-11-home-d560896win9b-thin-light-laptop/p/itm0567f562d1f5b", "Laptop"),
    ("https://www.flipkart.com/realme-narzo-70x-5g-ice-blue-128-gb/p/itm7b59e7f81bd36", "Phone"),
    ("https://www.flipkart.com/oneplus-12r-iron-gray-128-gb/p/itm72c1a29e375a8", "Phone"),
    ("https://www.flipkart.com/lg-108-cm-43-inch-ultra-hd-4k-led-smart-webos-tv-2024-edition/p/itm7f5de8de3aec3", "Monitor"),
    ("https://www.flipkart.com/apple-ipad-10th-generation-a14-bionic-chip-64-gb-rom-10-9-inch-wifi-only-blue/p/itm166dfa1082783", "Tablet"),
    ("https://www.flipkart.com/samsung-galaxy-tab-s9-fe-10-9-inch-6-gb-ram-128-gb-rom-wi-fi-only-silver/p/itm5ed3d6fc6e66f", "Tablet"),
    ("https://www.flipkart.com/logitech-g502-hero-high-performance-wired-optical-gaming-mouse/p/itm3d3c3c8d7dd21", "Mouse"),
    ("https://www.flipkart.com/boat-airdopes-141-bluetooth-headset/p/itmc99b17a5e2582", "Earphones"),
    ("https://www.flipkart.com/redmi-note-13-pro-5g-fusion-purple-128-gb/p/itm03ae2ebb03cdf", "Phone"),
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

def _fetch(url: str, referer: str = "", timeout: int = 20) -> Optional[str]:
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

def _ph_search(product_url: str) -> dict:
    session = requests.Session()
    session.headers.update(_get_headers("https://pricehistory.app/"))
    session.headers["Content-Type"] = "application/json"
    session.headers["Origin"] = "https://pricehistory.app"
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
    if not html or len(html) < 3000:
        return {}

    image = None
    try:
        soup = BeautifulSoup(html, "lxml")
        og = soup.find("meta", property="og:image")
        if og and og.get("content") and "placeholder" not in og["content"].lower():
            img_url = og["content"].strip()
            if img_url.startswith("http"):
                image = img_url
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
        for pat in [r'"currentPrice"\s*:\s*(\d+(?:\.\d+)?)', r'"latestPrice"\s*:\s*(\d+(?:\.\d+)?)', r'"price"\s*:\s*(\d+(?:\.\d+)?)']:
            m = re.search(pat, html)
            if m:
                try:
                    val = float(m.group(1))
                    if val > 10:
                        current_price = val
                        break
                except (ValueError, TypeError):
                    pass

    name = None
    try:
        soup = BeautifulSoup(html, "lxml") if not image else soup
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            t = og_title["content"].strip()
            t = re.sub(r"\s*[-|]\s*Price\s*History.*$", "", t, flags=re.IGNORECASE).strip()
            if t and len(t) > 5:
                name = t[:150]
    except Exception:
        pass

    return {"image": image, "current_price": current_price, "highest_price": highest_price, "name": name}

def _make_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:16]

def _parse_price(text: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d.]", "", text.replace(",", "").strip())
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

def _process_amazon_seed(asin: str, category: str) -> Optional[dict]:
    product_url = f"https://www.amazon.in/dp/{asin}"
    try:
        ph = _ph_search(product_url)
        if not ph.get("slug"):
            return None
        page_data = _ph_page_data(ph["slug"])
        if not page_data.get("current_price"):
            return None

        current = page_data["current_price"]
        highest = page_data.get("highest_price") or current
        if highest < current:
            highest = current
        discount = round(((highest - current) / highest) * 100) if highest > current else 0

        name = page_data.get("name") or ph.get("name", "") or f"Amazon Product {asin}"
        if not name or name == "Unknown Product":
            name = f"Amazon Product {asin}"

        return {
            "id": _make_id(product_url),
            "name": name[:150],
            "image": page_data.get("image", ""),
            "url": product_url,
            "store": "Amazon",
            "price": current,
            "originalPrice": highest,
            "discount": discount,
            "rating": 0.0,
            "reviews": 0,
            "category": category,
        }
    except Exception:
        return None

def _process_flipkart_seed(url: str, category: str) -> Optional[dict]:
    try:
        ph = _ph_search(url)
        if not ph.get("slug"):
            return None

        page_data = _ph_page_data(ph["slug"])
        if not page_data.get("current_price"):
            return None

        current = page_data["current_price"]
        highest = page_data.get("highest_price") or current
        if highest < current:
            highest = current
        discount = round(((highest - current) / highest) * 100) if highest > current else 0

        name = page_data.get("name") or ph.get("name", "") or "Unknown Product"

        image = page_data.get("image", "")
        if not image:
            return None

        return {
            "id": _make_id(url),
            "name": name[:150],
            "image": image,
            "url": url,
            "store": "Flipkart",
            "price": current,
            "originalPrice": highest,
            "discount": discount,
            "rating": 0.0,
            "reviews": 0,
            "category": category,
        }
    except Exception:
        return None

def get_trending_products(force_refresh: bool = False) -> list[dict]:
    global _cache
    now = time.time()
    if not force_refresh and _cache["data"] and (now - _cache["timestamp"]) < CACHE_TTL:
        return _cache["data"]

    amazon_products = []
    flipkart_products = []
    seen_ids = set()

    with ThreadPoolExecutor(max_workers=8) as pool:
        seed_futures = {
            pool.submit(_process_amazon_seed, asin, cat): f"amazon_{asin}"
            for asin, cat in AMAZON_SEED_PRODUCTS
        }
        for future in as_completed(seed_futures):
            try:
                result = future.result(timeout=25)
                if result and result["id"] not in seen_ids and result.get("name") and result["name"] != "Unknown Product":
                    seen_ids.add(result["id"])
                    amazon_products.append(result)
            except Exception:
                pass

    amazon_products.sort(key=lambda x: x.get("discount", 0), reverse=True)
    amazon_products = amazon_products[:5]

    with ThreadPoolExecutor(max_workers=8) as pool:
        fk_futures = {
            pool.submit(_process_flipkart_seed, url, cat): url
            for url, cat in FLIPKART_SEED_PRODUCTS
        }
        for future in as_completed(fk_futures):
            try:
                result = future.result(timeout=25)
                if result and result["id"] not in seen_ids and result.get("name") and result["name"] != "Unknown Product":
                    seen_ids.add(result["id"])
                    flipkart_products.append(result)
            except Exception:
                pass

    flipkart_products.sort(key=lambda x: x.get("discount", 0), reverse=True)
    flipkart_products = flipkart_products[:5]

    products = amazon_products + flipkart_products

    if products:
        _cache["data"] = products
        _cache["timestamp"] = now

    return products
