import re
from urllib.parse import urlparse
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup
import json
from typing import Optional

SCRAPE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8,hi;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Upgrade-Insecure-Requests": "1",
}

STORE_DETECTION_PATTERNS = {
    "amazon": ["amazon.com", "amazon.in", "amazon.co.uk", "amzn.in", "amzn.com"],
    "newegg": ["newegg.com"],
    "bestbuy": ["bestbuy.com"],
    "flipkart": ["flipkart.com"],
}

def detect_store(url: str) -> Optional[str]:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    for store, patterns in STORE_DETECTION_PATTERNS.items():
        for pattern in patterns:
            if pattern in hostname:
                return store
    return None

def fetch_page_html(url: str) -> str:
    profiles = ["chrome120", "chrome110", "safari17_0", "chrome107"]
    last_error = None
    for profile in profiles:
        try:
            response = cffi_requests.get(
                url,
                headers=SCRAPE_HEADERS,
                impersonate=profile,
                timeout=25,
                allow_redirects=True,
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            last_error = e
    raise last_error

def extract_og_image(soup: BeautifulSoup) -> Optional[str]:
    og_tag = soup.find("meta", property="og:image")
    if og_tag and og_tag.get("content"):
        return og_tag["content"]
    return None

def extract_twitter_image(soup: BeautifulSoup) -> Optional[str]:
    twitter_tag = soup.find("meta", attrs={"name": "twitter:image"})
    if twitter_tag and twitter_tag.get("content"):
        return twitter_tag["content"]
    return None

def extract_jsonld_data(soup: BeautifulSoup) -> Optional[dict]:
    for script_tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script_tag.string)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        return item
                data = data[0]
            if isinstance(data, dict):
                if data.get("@type") == "Product":
                    return data
                if "@graph" in data:
                    for item in data["@graph"]:
                        if isinstance(item, dict) and item.get("@type") == "Product":
                            return item
        except (json.JSONDecodeError, TypeError, IndexError):
            continue
    return None

def extract_jsonld_image(soup: BeautifulSoup) -> Optional[str]:
    product_data = extract_jsonld_data(soup)
    if product_data:
        image = product_data.get("image")
        if isinstance(image, str):
            return image
        if isinstance(image, list) and len(image) > 0:
            return image[0]
        if isinstance(image, dict):
            return image.get("url")
    return None

def extract_og_title(soup: BeautifulSoup) -> Optional[str]:
    og_tag = soup.find("meta", property="og:title")
    if og_tag and og_tag.get("content"):
        return og_tag["content"].strip()
    return None

PRICE_PATTERNS = {
    "amazon": [
        {"selector": "span.a-price span.a-offscreen", "type": "text"},
        {"selector": "span.a-offscreen", "type": "text"},
        {"selector": "#priceblock_ourprice", "type": "text"},
        {"selector": "#priceblock_dealprice", "type": "text"},
        {"selector": "span.a-price-whole", "type": "text"},
    ],
    "newegg": [
        {"selector": "li.price-current", "type": "text"},
    ],
    "bestbuy": [
        {"selector": ".priceView-customer-price span", "type": "text"},
    ],
    "flipkart": [
        {"selector": "div._30jeq3", "type": "text"},
        {"selector": "div._1vC4OE", "type": "text"},
        {"selector": "div.Nx9bqj", "type": "text"},
        {"selector": "div.CEmiEU div", "type": "text"},
        {"selector": "div._16Jk6d", "type": "text"},
        {"selector": "div.hl05eU div.Nx9bqj", "type": "text"},
        {"selector": "div.yRaY8j", "type": "text"},
        {"selector": "div._25b18c div", "type": "text"},
    ],
}

TITLE_PATTERNS = {
    "amazon": [{"selector": "#productTitle", "type": "text"}],
    "newegg": [{"selector": ".product-title", "type": "text"}],
    "bestbuy": [{"selector": ".sku-title", "type": "text"}],
    "flipkart": [
        {"selector": "span.VU-ZEz", "type": "text"},
        {"selector": "span.B_NuCI", "type": "text"},
        {"selector": "h1._9E25nV", "type": "text"},
        {"selector": "h1.yhB1nd", "type": "text"},
    ],
}

IMAGE_PATTERNS = {
    "amazon": [
        {"selector": "#landingImage", "attr": "src"},
        {"selector": "#imgBlkFront", "attr": "src"},
        {"selector": "img[data-old-hires]", "attr": "data-old-hires"},
        {"selector": "#main-image-container img", "attr": "src"},
    ],
    "newegg": [
        {"selector": ".product-view-img-original", "attr": "src"},
    ],
    "bestbuy": [
        {"selector": ".primary-image", "attr": "src"},
    ],
    "flipkart": [
        {"selector": "img._396cs4", "attr": "src"},
        {"selector": "img._2r_T1I", "attr": "src"},
        {"selector": "div._3kidJX img", "attr": "src"},
        {"selector": "img.DByuf4", "attr": "src"},
        {"selector": "img.qqDXDz", "attr": "src"},
    ],
}

def parse_price_text(text: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d.,]", "", text.strip())
    cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None

def extract_price(soup: BeautifulSoup, store: str) -> Optional[float]:
    product_data = extract_jsonld_data(soup)
    if product_data:
        offers = product_data.get("offers")
        if isinstance(offers, dict):
            price_val = offers.get("price") or offers.get("lowPrice")
            if price_val:
                try:
                    p = float(price_val)
                    if p > 0:
                        return p
                except (ValueError, TypeError):
                    pass
        elif isinstance(offers, list):
            for offer in offers:
                price_val = offer.get("price") or offer.get("lowPrice")
                if price_val:
                    try:
                        p = float(price_val)
                        if p > 0:
                            return p
                    except (ValueError, TypeError):
                        continue

    patterns = PRICE_PATTERNS.get(store, [])
    for pattern in patterns:
        element = soup.select_one(pattern["selector"])
        if element:
            price = parse_price_text(element.get_text())
            if price and price > 0:
                return price

    price_texts = soup.find_all(string=re.compile(r"₹[\d,]+"))
    for pt in price_texts:
        price = parse_price_text(pt)
        if price and price > 100:
            return price

    return None

def extract_title(soup: BeautifulSoup, store: str) -> Optional[str]:
    og_title = extract_og_title(soup)
    if og_title:
        cleaned = re.sub(r"\s*[-|:]\s*(Amazon\.in|Flipkart|Newegg|Best Buy).*$", "", og_title, flags=re.IGNORECASE)
        if cleaned and len(cleaned) > 5:
            return cleaned.strip()

    product_data = extract_jsonld_data(soup)
    if product_data and product_data.get("name"):
        return product_data["name"][:200]

    patterns = TITLE_PATTERNS.get(store, [])
    for pattern in patterns:
        element = soup.select_one(pattern["selector"])
        if element:
            title = element.get_text().strip()
            if title:
                return title[:200]
    return None

def extract_image(soup: BeautifulSoup, store: str) -> Optional[str]:
    patterns = IMAGE_PATTERNS.get(store, [])
    for pattern in patterns:
        element = soup.select_one(pattern["selector"])
        if element:
            image_url = element.get(pattern.get("attr", "src"))
            if image_url and "placeholder" not in image_url.lower():
                if store == "amazon":
                    image_url = re.sub(r"\._[A-Z]+\d+_", "._SL500_", image_url)
                return image_url

    og_image = extract_og_image(soup)
    if og_image:
        return og_image

    twitter_image = extract_twitter_image(soup)
    if twitter_image:
        return twitter_image

    jsonld_image = extract_jsonld_image(soup)
    if jsonld_image:
        return jsonld_image

    return None

def extract_product_metadata(url: str) -> dict:
    store = detect_store(url)
    if not store:
        raise ValueError(f"Unsupported store URL: {url}")

    html = fetch_page_html(url)
    soup = BeautifulSoup(html, "lxml")

    product_name = extract_title(soup, store) or "Unknown Product"
    product_image_url = extract_image(soup, store) or ""
    current_price = extract_price(soup, store)

    return {
        "store": store,
        "product_name": product_name,
        "product_image_url": product_image_url,
        "current_price": current_price,
    }
