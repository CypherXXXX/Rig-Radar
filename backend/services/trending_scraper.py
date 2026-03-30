import re
import time
import hashlib
from typing import Optional
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup
import json

BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8,hi;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Upgrade-Insecure-Requests": "1",
}

AMAZON_SEARCH_URLS = [
    {"url": "https://www.amazon.in/s?k=nvidia+geforce+rtx+graphics+card&s=review-rank", "category": "GPU", "min_price": 10000},
    {"url": "https://www.amazon.in/s?k=amd+ryzen+intel+core+processor+desktop&s=review-rank", "category": "CPU", "min_price": 5000},
    {"url": "https://www.amazon.in/s?k=ddr5+ddr4+ram+desktop+16gb+32gb&s=review-rank", "category": "RAM", "min_price": 2000},
    {"url": "https://www.amazon.in/s?k=nvme+ssd+1tb+internal+samsung+wd&s=review-rank", "category": "SSD", "min_price": 2000},
    {"url": "https://www.amazon.in/s?k=gaming+monitor+144hz+27+inch&s=review-rank", "category": "Monitor", "min_price": 8000},
    {"url": "https://www.amazon.in/s?k=mechanical+gaming+keyboard+rgb+full+size&s=review-rank", "category": "Keyboard", "min_price": 1500},
    {"url": "https://www.amazon.in/s?k=gaming+mouse+logitech+razer+wireless&s=review-rank", "category": "Mouse", "min_price": 1000},
    {"url": "https://www.amazon.in/s?k=motherboard+am5+lga1700+desktop+gaming&s=review-rank", "category": "Motherboard", "min_price": 5000},
    {"url": "https://www.amazon.in/s?k=cpu+cooler+tower+aio+liquid+cooling&s=review-rank", "category": "Cooling", "min_price": 2000},
    {"url": "https://www.amazon.in/s?k=pc+power+supply+unit+psu+650w+750w+modular&s=review-rank", "category": "PSU", "min_price": 3000},
    {"url": "https://www.amazon.in/s?k=gaming+headset+surround+sound+hyperx+steelseries&s=review-rank", "category": "Headset", "min_price": 1500},
    {"url": "https://www.amazon.in/s?k=gaming+laptop+rtx+asus+msi+lenovo&s=review-rank", "category": "Laptop", "min_price": 40000},
]

_cache: dict = {"data": [], "timestamp": 0}
CACHE_TTL = 3600

def _fetch_html(url: str) -> str:
    profiles = ["chrome120", "chrome110", "safari17_0"]
    last_error = None
    for profile in profiles:
        try:
            response = cffi_requests.get(
                url,
                headers=BROWSER_HEADERS,
                impersonate=profile,
                timeout=20,
                allow_redirects=True,
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            last_error = e
    raise last_error

def _generate_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:16]

def _parse_price(text: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d.,]", "", text.strip())
    cleaned = cleaned.replace(",", "")
    try:
        val = float(cleaned)
        return val if val > 0 else None
    except (ValueError, TypeError):
        return None

def _extract_search_result(item, category: str) -> Optional[dict]:
    try:
        name_el = item.select_one("h2 a span") or item.select_one("h2 span")
        if not name_el:
            return None
        name = name_el.get_text(strip=True)
        if not name or len(name) < 10:
            return None

        price = None
        price_el = item.select_one("span.a-price span.a-offscreen")
        if price_el:
            price = _parse_price(price_el.get_text())
        if not price:
            price_el = item.select_one("span.a-price-whole")
            if price_el:
                price = _parse_price(price_el.get_text())
        if not price or price < 500:
            return None

        min_price_map = {
            "GPU": 10000, "CPU": 5000, "RAM": 2000, "SSD": 2000,
            "Monitor": 8000, "Keyboard": 1500, "Mouse": 1000,
            "Motherboard": 5000, "Cooling": 2000, "PSU": 3000,
            "Headset": 1500, "Laptop": 40000,
        }
        cat_min = min_price_map.get(category, 500)
        if price < cat_min:
            return None

        img_el = item.select_one("img.s-image")
        image_url = ""
        if img_el:
            image_url = img_el.get("src", "") or ""
        if not image_url:
            img_el = item.select_one("img")
            if img_el:
                image_url = img_el.get("src", "") or ""

        link_el = item.select_one("h2 a.a-link-normal") or item.select_one("a.a-link-normal[href*='/dp/']")
        product_url = ""
        if link_el:
            href = link_el.get("href", "")
            if href.startswith("/"):
                product_url = f"https://www.amazon.in{href}"
            elif href.startswith("http"):
                product_url = href

        dp_match = re.search(r"/dp/([A-Z0-9]{10})", product_url)
        if dp_match:
            product_url = f"https://www.amazon.in/dp/{dp_match.group(1)}"
        if not product_url:
            return None

        rating = 0.0
        rating_el = item.select_one("span.a-icon-alt")
        if rating_el:
            rm = re.search(r"([\d.]+)", rating_el.get_text(strip=True))
            if rm:
                rating = float(rm.group(1))

        reviews = 0
        rev_el = item.select_one("span.a-size-base.s-underline-text")
        if rev_el:
            rev_text = rev_el.get_text(strip=True).replace(",", "")
            rm = re.search(r"(\d+)", rev_text)
            if rm:
                reviews = int(rm.group(1))

        original_price = price
        mrp_el = item.select_one("span.a-price.a-text-price span.a-offscreen")
        if mrp_el:
            op = _parse_price(mrp_el.get_text())
            if op and op > price:
                original_price = op

        discount = 0
        if original_price > price:
            discount = round(((original_price - price) / original_price) * 100)

        return {
            "id": _generate_id(product_url),
            "name": name[:150],
            "image": image_url,
            "url": product_url,
            "store": "Amazon",
            "price": price,
            "originalPrice": original_price,
            "discount": discount,
            "rating": rating,
            "reviews": reviews,
            "category": category,
        }
    except Exception:
        return None

def _scrape_amazon_search(url: str, category: str, limit: int = 1) -> list[dict]:
    products = []
    try:
        html = _fetch_html(url)
        soup = BeautifulSoup(html, "lxml")

        items = soup.select("div[data-component-type='s-search-result']")
        if not items:
            items = soup.select("div.s-result-item[data-asin]")

        for item in items[:limit * 3]:
            asin = item.get("data-asin", "")
            if not asin or asin == "":
                continue
            product = _extract_search_result(item, category)
            if product and product.get("image"):
                products.append(product)
                if len(products) >= limit:
                    break
    except Exception:
        pass
    return products

def get_trending_products(force_refresh: bool = False) -> list[dict]:
    global _cache

    now = time.time()
    if not force_refresh and _cache["data"] and (now - _cache["timestamp"]) < CACHE_TTL:
        return _cache["data"]

    all_products = []

    for entry in AMAZON_SEARCH_URLS:
        try:
            products = _scrape_amazon_search(entry["url"], entry["category"], limit=1)
            all_products.extend(products)
        except Exception:
            continue

    seen_ids = set()
    unique_products = []
    for p in all_products:
        if p["id"] not in seen_ids and p.get("image"):
            seen_ids.add(p["id"])
            unique_products.append(p)

    category_order = ["GPU", "CPU", "RAM", "SSD", "Monitor", "Keyboard", "Mouse", "Motherboard", "Cooling", "PSU", "Headset", "Laptop"]
    category_map: dict[str, list] = {}
    for p in unique_products:
        cat = p.get("category", "Other")
        if cat not in category_map:
            category_map[cat] = []
        category_map[cat].append(p)

    result = []
    for cat in category_order:
        if cat in category_map:
            result.extend(category_map[cat][:1])
        if len(result) >= 10:
            break

    if len(result) < 10:
        for p in unique_products:
            if p not in result:
                result.append(p)
            if len(result) >= 10:
                break

    if result:
        _cache["data"] = result
        _cache["timestamp"] = now

    return result
