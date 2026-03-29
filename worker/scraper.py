from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup
from typing import Optional
import re

PRICE_SELECTORS = {
    "amazon": [
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
        "._30jeq3",
        "._16Jk6d",
    ],
}

TITLE_SELECTORS = {
    "amazon": ["#productTitle", "h1.product-title-word-break"],
    "newegg": [".product-title", "h1.product-title"],
    "bestbuy": [".sku-title h1", ".sku-title"],
    "flipkart": [".B_NuCI", "._35KyD6"],
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
        {"selector": "._2r_T1I img", "attr": "src"},
    ],
}

def fetch_product_page(url: str) -> str:
    response = curl_requests.get(
        url,
        impersonate="chrome120",
        timeout=15,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        },
    )
    response.raise_for_status()
    return response.text

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
