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

logger = logging.getLogger("rigradar.trending_worker")
logger.setLevel(logging.INFO)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

AMAZON_SEED_ASINS = [
    ("B0CZLGTFMF", "GPU"),
    ("B0D5J3D27K", "CPU"),
    ("B09HN37XDX", "SSD"),
    ("B07XVMDJQW", "Monitor"),
    ("B09HSCSQYJ", "Keyboard"),
    ("B09NVPTQPM", "Headset"),
    ("B08N5WRWNW", "Mouse"),
    ("B0C7K5N42C", "RAM"),
    ("B0GPVVYKTQ", "Tablet"),
    ("B0CHX1W1XY", "Laptop"),
    ("B0DGHW8ZPQ", "GPU"),
    ("B0BT4JTK5J", "Laptop"),
    ("B0CX23V2ZK", "CPU"),
    ("B0DJHJ3QK8", "Mouse"),
    ("B09WMH6LYB", "Earphones"),
]

AMAZON_BESTSELLER_URLS = [
    ("https://www.amazon.in/gp/bestsellers/computers/1375424031", "GPU"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375378031", "CPU"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375380031", "RAM"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375382031", "SSD"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375398031", "Monitor"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375406031", "Keyboard"),
    ("https://www.amazon.in/gp/bestsellers/computers/1375408031", "Mouse"),
    ("https://www.amazon.in/gp/bestsellers/electronics/1389401031", "Earphones"),
]

FLIPKART_SEED_URLS = [
    "https://www.flipkart.com/apple-iphone-15-blue-128-gb/p/itm6e3d0ab408a24",
    "https://www.flipkart.com/samsung-galaxy-s24-cobalt-violet-256-gb/p/itm49ae24f48d0c7",
    "https://www.flipkart.com/asus-rog-strix-g15-2023-ryzen-7-7745hx-16-gb-512-gb-ssd-windows-11-home-g513rc-hn063ws-gaming-laptop/p/itm0e7a9c8e85b5b",
    "https://www.flipkart.com/dell-inspiron-3520-intel-core-i5-1235u-8-gb-512-gb-ssd-windows-11-home-d560896win9b-thin-light-laptop/p/itm0567f562d1f5b",
    "https://www.flipkart.com/redmi-note-13-pro-fusion-white-256-gb/p/itm1e7a3ce4d1ce0",
    "https://www.flipkart.com/sony-wh-1000xm5-bluetooth-headset/p/itm9c2dc7bf3d0f2",
    "https://www.flipkart.com/one-plus-nord-ce-4-lite-5g-mega-blue-128-gb/p/itmd8f5186f86eae",
    "https://www.flipkart.com/lg-108-cm-43-inch-ultra-hd-4k-led-smart-oled-tv/p/itm1c18eb1f5c26a",
    "https://www.flipkart.com/boult-audio-airbass-propods-x-tws/p/itm7d8d8c3f1e3b2",
    "https://www.flipkart.com/apple-macbook-air-m2-8-gb-256-gb-ssd-mac-os-monterey-mly33hn-a/p/itm45b5f5db55963",
]

def _get_headers(referer: str = "") -> dict:
    h = {
        "User-Agent": random.choice(USER_AGENTS),
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
    session.headers["Content-Type"] = "application/json"
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
    if not html or len(html) < 5000:
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

        return {
            "id": _make_id(product_url),
            "name": ph.get("name", "Unknown Product")[:150],
            "image": page_data.get("image", ""),
            "url": product_url,
            "store": "amazon",
            "price": current,
            "originalPrice": highest,
            "discount": discount,
        }
    except Exception:
        return None

def _scrape_amazon_bestseller(url: str, category: str) -> list:
    html = _fetch(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    items = (
        soup.select("div[id^='p13n-asin-index-']")
        or soup.select("li.zg-item-immersion")
        or soup.select(".zg-grid-general-faceout")
        or soup.select("div._cDEzb_itemContainer_1GHJR")
    )

    results = []
    for item in items[:10]:
        try:
            name_el = (
                item.select_one(".p13n-sc-truncate-desktop-type2")
                or item.select_one(".p13n-sc-truncated")
                or item.select_one("._cDEzb_p13n-sc-css-line-clamp-3_g3dy1")
                or item.select_one("span.a-size-small")
                or item.select_one("div._cDEzb_p13n-sc-css-line-clamp-1_1Fn1y")
            )
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name or len(name) < 8:
                continue

            price_el = (
                item.select_one(".p13n-sc-price")
                or item.select_one("span.a-color-price")
                or item.select_one("span._cDEzb_p13n-sc-price_3mJ9Z")
            )
            if not price_el:
                continue
            price = _parse_price(price_el.get_text())
            if not price or price < 500:
                continue

            img_el = item.select_one("img.s-image") or item.select_one("img.a-dynamic-image") or item.select_one("img")
            if not img_el:
                continue

            link_el = item.select_one("a.a-link-normal[href*='/dp/']") or item.select_one("a[href*='/dp/']")
            if not link_el:
                continue
            dp_m = re.search(r"/dp/([A-Z0-9]{10})", link_el.get("href", ""))
            if not dp_m:
                continue

            product_url = f"https://www.amazon.in/dp/{dp_m.group(1)}"
            original_price = round(price * 1.15, 2)

            results.append({
                "id": _make_id(product_url),
                "name": name[:150],
                "image": img_el.get("src", ""),
                "url": product_url,
                "store": "amazon",
                "price": price,
                "originalPrice": original_price,
                "discount": 13,
            })
            if len(results) >= 2:
                break
        except Exception:
            continue
    return results

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

        return {
            "id": _make_id(url),
            "name": ph.get("name", "Unknown Product")[:150],
            "image": page_data["image"],
            "url": url,
            "store": "flipkart",
            "price": current,
            "originalPrice": highest,
            "discount": round(((highest - current) / highest) * 100) if highest > current else 0,
        }
    except Exception:
        return None

def fetch_and_store_trending(trending_table) -> None:
    logger.info("Starting proactive market discovery for trending deals...")
    deals = []
    seen_ids = set()

    def _add_deal(deal):
        if deal and deal["id"] not in seen_ids and deal.get("name") and deal["name"] != "Unknown Product":
            seen_ids.add(deal["id"])
            deals.append(deal)

    with ThreadPoolExecutor(max_workers=8) as pool:
        seed_futures = {
            pool.submit(_process_amazon_seed, asin, cat): f"amazon_{asin}"
            for asin, cat in AMAZON_SEED_ASINS
        }
        for future in as_completed(seed_futures):
            try:
                result = future.result(timeout=25)
                _add_deal(result)
            except Exception:
                pass

    logger.info(f"Collected {len(deals)} deals from Amazon seed ASINs")

    if len(deals) < 5:
        with ThreadPoolExecutor(max_workers=6) as pool:
            bs_futures = {
                pool.submit(_scrape_amazon_bestseller, url, cat): cat
                for url, cat in AMAZON_BESTSELLER_URLS
            }
            for future in as_completed(bs_futures):
                try:
                    results = future.result(timeout=30)
                    if isinstance(results, list):
                        for result in results:
                            _add_deal(result)
                    elif results:
                        _add_deal(results)
                except Exception:
                    pass

    logger.info(f"Total Amazon deals: {len(deals)}")

    with ThreadPoolExecutor(max_workers=6) as pool:
        fk_futures = [pool.submit(_process_flipkart_seed, url) for url in FLIPKART_SEED_URLS]
        for future in as_completed(fk_futures):
            try:
                result = future.result(timeout=25)
                _add_deal(result)
            except Exception:
                pass

    logger.info(f"Total deals (Amazon + Flipkart): {len(deals)}")

    if not deals:
        logger.warning("No trending deals were successfully scraped. Aborting table update.")
        return

    success_count = 0
    current_timestamp = datetime.utcnow().isoformat() + "Z"

    for deal in deals:
        try:
            item = {
                "item_id": deal["id"],
                "product_name": deal["name"],
                "product_image_url": deal.get("image", ""),
                "product_url": deal["url"],
                "store": deal["store"],
                "previous_price": Decimal(str(deal.get("originalPrice", deal["price"]))),
                "current_price": Decimal(str(deal["price"])),
                "drop_percentage": Decimal(str(deal.get("discount", 0))),
                "updated_at": current_timestamp,
            }
            trending_table.put_item(Item=item)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to insert trending deal {deal.get('id')} into DynamoDB: {e}")

    logger.info(f"Successfully stored {success_count} trending deals into the database.")