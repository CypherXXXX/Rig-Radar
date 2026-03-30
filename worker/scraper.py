from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup
from typing import Optional
import re

BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8,hi;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Upgrade-Insecure-Requests": "1",
}

PRICE_SELECTORS = {
    "amazon": [
        "span.a-price span.a-offscreen",
        "span.a-offscreen",
        "span.a-price-whole",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
    ],
    "newegg": [
        "li.price-current",
        ".price-current strong",
    ],
    "bestbuy": [
        ".priceView-customer-price span",
        ".priceView-hero-price span",
    ],
    "flipkart": [
        "div._30jeq3",
        "div._1vC4OE",
        "div.Nx9bqj",
        "div.CEmiEU div",
        "div._16Jk6d",
        "div.hl05eU div.Nx9bqj",
        "div.yRaY8j",
        "div._25b18c div",
    ],
}

TITLE_SELECTORS = {
    "amazon": ["#productTitle", "h1.product-title-word-break"],
    "newegg": [".product-title", "h1.product-title"],
    "bestbuy": [".sku-title h1", ".sku-title"],
    "flipkart": ["span.VU-ZEz", "span.B_NuCI", "h1._9E25nV", "h1.yhB1nd"],
}

IMAGE_SELECTORS = {
    "amazon": [
        {"selector": "#landingImage", "attr": "src"},
        {"selector": "img[data-old-hires]", "attr": "data-old-hires"},
        {"selector": "#imgTagWrapperId img", "attr": "src"},
    ],
    "newegg": [
        {"selector": ".product-view-img-original", "attr": "src"},
        {"selector": ".swiper-slide img", "attr": "src"},
    ],
    "bestbuy": [
        {"selector": ".primary-image", "attr": "src"},
        {"selector": ".shop-media-gallery img", "attr": "src"},
    ],
    "flipkart": [
        {"selector": "img._396cs4", "attr": "src"},
        {"selector": "img._2r_T1I", "attr": "src"},
        {"selector": "div._3kidJX img", "attr": "src"},
        {"selector": "img.DByuf4", "attr": "src"},
        {"selector": "img.qqDXDz", "attr": "src"},
    ],
}

def fetch_product_page(url: str) -> str:
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

def clean_price_text(raw_text: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d.,]", "", raw_text.strip())
    cleaned = cleaned.replace(",", "")
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None

def scrape_price(html: str, store: str) -> Optional[float]:
    soup = BeautifulSoup(html, "lxml")

    selectors = PRICE_SELECTORS.get(store, [])
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            price = clean_price_text(element.get_text())
            if price and price > 0:
                return price

    price_texts = soup.find_all(string=re.compile(r"₹[\d,]+"))
    for pt in price_texts:
        price = clean_price_text(pt)
        if price and price > 100:
            return price

    return None

def scrape_title(html: str, store: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")

    og_tag = soup.find("meta", property="og:title")
    if og_tag and og_tag.get("content"):
        return og_tag["content"].strip()[:200]

    selectors = TITLE_SELECTORS.get(store, [])
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            title = element.get_text().strip()
            if title:
                return title[:200]

    return None

def scrape_image(html: str, store: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")

    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        return og_image["content"]

    twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
    if twitter_image and twitter_image.get("content"):
        return twitter_image["content"]

    selectors = IMAGE_SELECTORS.get(store, [])
    for selector_config in selectors:
        element = soup.select_one(selector_config["selector"])
        if element:
            image_url = element.get(selector_config["attr"])
            if image_url:
                return image_url

    return None

def scrape_product(url: str, store: str) -> dict:
    html = fetch_product_page(url)

    return {
        "price": scrape_price(html, store),
        "title": scrape_title(html, store),
        "image": scrape_image(html, store),
    }
