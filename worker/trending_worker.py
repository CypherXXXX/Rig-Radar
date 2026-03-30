import re
import random
import hashlib
import logging
import requests
from decimal import Decimal
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging to match handler.py
logger = logging.getLogger("rigradar.trending_worker")
logger.setLevel(logging.INFO)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

AMAZON_BESTSELLER_URLS = [
    ("https://www.amazon.in/gp/bestsellers/computers/1375424031", "GPU"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375378031", "CPU"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375380031", "RAM"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375382031", "SSD"),
]

AMAZON_DEALS_URL = "https://www.amazon.in/gp/deals"

FLIPKART_SEED_URLS = [
    "https://www.flipkart.com/apple-iphone-15-blue-128-gb/p/itm6e3d0ab408a24",
    "https://www.flipkart.com/samsung-galaxy-s24-cobalt-violet-256-gb/p/itm49ae24f48d0c7",
    "https://www.flipkart.com/asus-rog-strix-g15-2023-ryzen-7-7745hx-16-gb-512-gb-ssd-windows-11-home-g513rc-hn063ws-gaming-laptop/p/itm0e7a9c8e85b5b",
    "https://www.flipkart.com/sony-wh-1000xm5-bluetooth-headset/p/itm9c2dc7bf3d0f2",
    "https://www.flipkart.com/lg-108-cm-43-inch-ultra-hd-4k-led-smart-oled-tv/p/itm1c18eb1f5c26a",
]

def _get_headers(referer: str = "") -> dict:
    h = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }
    if referer:
        h["Referer"] = referer
    return h

def _fetch(url: str, referer: str = "", timeout: int = 20) -> Optional[str]:
    session = requests.Session()
    session.headers.update(_get_headers(referer))
    for attempt in range(2):
        try:
            r = session.get(url, timeout=timeout, allow_redirects=True)
            r.raise_for_status()
            return r.text
        except Exception:
            pass
    return None

def _make_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:16]

def _parse_price(text: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d.]", "", text.replace(",", "").strip())
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

def _ph_search(product_url: str) -> dict:
    session = requests.Session()
    session.headers.update(_get_headers("https://pricehistory.app/"))
    try:
        r = session.post("https://pricehistory.app/api/search", json={"url": product_url}, timeout=12)
        if r.ok:
            data = r.json()
            if data.get("status") and data.get("code"):
                return {"slug": data["code"], "name": data.get("name", "")}
    except Exception:
        pass
    return {}

def _ph_page_data(slug: str) -> dict:
    html = _fetch(f"https://pricehistory.app/p/{slug}", referer="https://pricehistory.app/")
    if not html:
        return {}

    image, current_price, highest_price = None, None, None
    try:
        soup = BeautifulSoup(html, "lxml")
        og = soup.find("meta", property="og:image")
        if og and "placeholder" not in og.get("content", "").lower():
            image = og["content"].strip()
            
        pairs = re.findall(r'\[\s*\d{10,13}\s*,\s*(\d+(?:\.\d+)?)\s*\]', html)
        if pairs:
            prices = [float(p) for p in pairs if float(p) > 10]
            if prices:
                current_price = prices[-1]
                highest_price = max(prices)
    except Exception:
        pass

    return {"image": image, "current_price": current_price, "highest_price": highest_price}

def _scrape_amazon_bestseller(url: str, category: str) -> Optional[dict]:
    html = _fetch(url)
    if not html:
        return None
    
    soup = BeautifulSoup(html, "lxml")
    items = soup.select("li.zg-item-immersion") or soup.select(".zg-grid-general-faceout")
    
    for item in items[:5]:
        try:
            name_el = item.select_one(".p13n-sc-truncate-desktop-type2") or item.select_one(".p13n-sc-truncated")
            if not name_el: continue
            
            price_el = item.select_one(".p13n-sc-price") or item.select_one("span.a-color-price")
            if not price_el: continue
            
            price = _parse_price(price_el.get_text())
            if not price or price < 500: continue

            img_el = item.select_one("img.s-image") or item.select_one("img")
            if not img_el: continue

            link_el = item.select_one("a.a-link-normal[href*='/dp/']")
            if not link_el: continue
            
            dp_m = re.search(r"/dp/([A-Z0-9]{10})", link_el.get("href", ""))
            if not dp_m: continue

            product_url = f"https://www.amazon.in/dp/{dp_m.group(1)}"
            original_price = round(price * 1.15, 2) # Simulate original price for bestsellers
            
            return {
                "id": _make_id(product_url),
                "name": name_el.get_text(strip=True)[:150],
                "image": img_el.get("src", ""),
                "url": product_url,
                "store": "amazon",
                "price": price,
                "originalPrice": original_price,
                "discount": round(((original_price - price) / original_price) * 100)
            }
        except Exception:
            continue
    return None

def _get_amazon_deals(count: int = 5) -> list[dict]:
    html = _fetch(AMAZON_DEALS_URL)
    if not html: return []
    
    soup = BeautifulSoup(html, "lxml")
    products = []
    cards = soup.select("div[data-component-type='s-search-result']") or soup.select(".DealCard-module__dealCard")
    
    for card in cards[:15]:
        try:
            name_el = card.select_one("h2 a span") or card.select_one("span.a-size-base-plus")
            price_el = card.select_one("span.a-price span.a-offscreen") or card.select_one("span.a-price-whole")
            if not name_el or not price_el: continue
            
            price = _parse_price(price_el.get_text())
            if not price or price < 500: continue

            orig_el = card.select_one("span.a-text-price span.a-offscreen")
            original = _parse_price(orig_el.get_text()) if orig_el else price
            if not original or original < price: original = price

            link_el = card.select_one("a[href*='/dp/']")
            if not link_el: continue
            
            dp_m = re.search(r"/dp/([A-Z0-9]{10})", link_el.get("href", ""))
            if not dp_m: continue

            img_el = card.select_one("img.s-image") or card.select_one("img")
            product_url = f"https://www.amazon.in/dp/{dp_m.group(1)}"

            products.append({
                "id": _make_id(product_url),
                "name": name_el.get_text(strip=True)[:150],
                "image": img_el.get("src", "") if img_el else "",
                "url": product_url,
                "store": "amazon",
                "price": price,
                "originalPrice": original,
                "discount": round(((original - price) / original) * 100) if original > price else 0
            })
            if len(products) >= count: break
        except Exception:
            continue
    return products

def _process_flipkart_seed(url: str) -> Optional[dict]:
    try:
        ph = _ph_search(url)
        if not ph.get("slug"): return None
        
        page_data = _ph_page_data(ph["slug"])
        if not page_data.get("image") or not page_data.get("current_price"): return None

        current = page_data["current_price"]
        highest = page_data.get("highest_price") or current
        if highest < current: highest = current

        return {
            "id": _make_id(url),
            "name": ph.get("name", "Unknown Product")[:150],
            "image": page_data["image"],
            "url": url,
            "store": "flipkart",
            "price": current,
            "originalPrice": highest,
            "discount": round(((highest - current) / highest) * 100) if highest > current else 0
        }
    except Exception:
        return None

def fetch_and_store_trending(trending_table) -> None:
    """
    Entry point invoked by handler.py. 
    Scrapes trending deals and stores them securely in DynamoDB using Decimals.
    """
    logger.info("Starting proactive market discovery for trending deals...")
    deals = []

    # 1. Fetch Amazon Deals & Bestsellers concurrently
    deals.extend(_get_amazon_deals(count=5))
    
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_scrape_amazon_bestseller, url, cat): cat for url, cat in AMAZON_BESTSELLER_URLS}
        for future in as_completed(futures):
            res = future.result(timeout=25)
            if res and res["id"] not in {d["id"] for d in deals}:
                deals.append(res)

    # 2. Fetch Flipkart Seeds concurrently
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(_process_flipkart_seed, url) for url in FLIPKART_SEED_URLS]
        for future in as_completed(futures):
            res = future.result(timeout=20)
            if res:
                deals.append(res)

    if not deals:
        logger.warning("No trending deals were successfully scraped. Aborting table update.")
        return

    # 3. Format and store in DynamoDB
    success_count = 0
    current_timestamp = datetime.utcnow().isoformat() + "Z"

    for deal in deals:
        try:
            item = {
                "item_id": deal["id"],
                "product_name": deal["name"],
                "product_image_url": deal["image"],
                "product_url": deal["url"],
                "store": deal["store"],
                "previous_price": Decimal(str(deal["originalPrice"])),
                "current_price": Decimal(str(deal["price"])),
                "drop_percentage": Decimal(str(deal["discount"])),
                "updated_at": current_timestamp
            }
            trending_table.put_item(Item=item)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to insert trending deal {deal.get('id')} into DynamoDB: {e}")

    logger.info(f"Successfully stored {success_count} trending deals into the database.")