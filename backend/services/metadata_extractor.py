import re
import json
import random
import requests
from urllib.parse import urlparse, parse_qs, urlencode, unquote
from typing import Optional
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
]

STORE_DETECTION_PATTERNS = {
    "amazon": ["amazon.com", "amazon.in", "amazon.co.uk", "amzn.in", "amzn.com", "amzn.to"],
    "newegg": ["newegg.com"],
    "bestbuy": ["bestbuy.com"],
    "flipkart": ["flipkart.com", "dl.flipkart.com"],
}

def detect_store(url: str) -> Optional[str]:
    hostname = urlparse(url).hostname or ""
    for store, patterns in STORE_DETECTION_PATTERNS.items():
        for pattern in patterns:
            if pattern in hostname:
                return store
    return None

def _extract_asin(url: str) -> Optional[str]:
    patterns = [
        r"/dp/([A-Z0-9]{10})",
        r"/gp/product/([A-Z0-9]{10})",
        r"/product/([A-Z0-9]{10})",
        r"asin=([A-Z0-9]{10})",
    ]
    for p in patterns:
        m = re.search(p, url, re.IGNORECASE)
        if m:
            return m.group(1).upper()
    return None

def _clean_amazon_url(url: str) -> str:
    asin = _extract_asin(url)
    if asin:
        return f"https://www.amazon.in/dp/{asin}"
    return url

def _clean_flipkart_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        path = parsed.path
        if "/dl/" in path:
            path = path.replace("/dl/", "/")
        clean = f"https://www.flipkart.com{path}"
        if "pid=" in (parsed.query or ""):
            pid = parse_qs(parsed.query).get("pid", [None])[0]
            if pid:
                clean += f"?pid={pid}"
        return clean
    except Exception:
        return url

def _get_headers(referer: str = "", mobile: bool = False) -> dict:
    ua = random.choice(MOBILE_USER_AGENTS if mobile else USER_AGENTS)
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
    }
    if not mobile:
        h["Sec-CH-UA"] = '"Chromium";v="131", "Not_A Brand";v="24", "Google Chrome";v="131"'
        h["Sec-CH-UA-Mobile"] = "?0"
        h["Sec-CH-UA-Platform"] = '"Windows"'
    if referer:
        h["Referer"] = referer
        h["Sec-Fetch-Site"] = "same-origin"
    return h

def _safe_get(url: str, referer: str = "", timeout: int = 20, mobile: bool = False) -> Optional[requests.Response]:
    session = requests.Session()
    session.headers.update(_get_headers(referer, mobile))
    for attempt in range(3):
        try:
            if attempt > 0:
                session.headers.update(_get_headers(referer, mobile))
            r = session.get(url, timeout=timeout, allow_redirects=True)
            if r.status_code == 200:
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
        if r.status_code == 200:
            return r
    except Exception:
        pass
    return None

def _pricehistory_lookup(product_url: str) -> dict:
    try:
        session = requests.Session()
        session.headers.update(_get_headers("https://pricehistory.app/"))
        session.headers["Content-Type"] = "application/json"
        session.headers["Origin"] = "https://pricehistory.app"

        r = session.post(
            "https://pricehistory.app/api/search",
            json={"url": product_url},
            timeout=15,
        )
        if r and r.status_code == 200:
            data = r.json()
            if data.get("status") and data.get("code"):
                return {"slug": data["code"], "name": data.get("name", "")}
    except Exception:
        pass
    return {}

def _pricehistory_page(slug: str) -> Optional[str]:
    r = _safe_get(f"https://pricehistory.app/p/{slug}", referer="https://pricehistory.app/")
    if r and len(r.text) > 3000:
        return r.text
    return None

def _ph_extract_image(html: str) -> Optional[str]:
    try:
        soup = BeautifulSoup(html, "lxml")
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            img = og["content"].strip()
            if img and "placeholder" not in img.lower() and img.startswith("http"):
                return img
        for img_tag in soup.find_all("img"):
            src = img_tag.get("src", "")
            if src and ("m.media-amazon.com" in src or "rukminim" in src):
                return src
    except Exception:
        pass
    return None

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
        r'"current_price"\s*:\s*(\d+(?:\.\d+)?)',
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

def _ph_extract_name(html: str) -> Optional[str]:
    try:
        soup = BeautifulSoup(html, "lxml")
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            name = og_title["content"].strip()
            name = re.sub(r"\s*[-|]\s*Price\s*History.*$", "", name, flags=re.IGNORECASE).strip()
            name = re.sub(r"\s*[-|]\s*PriceHistory.*$", "", name, flags=re.IGNORECASE).strip()
            if name and len(name) > 5:
                return name[:200]
        title_tag = soup.find("title")
        if title_tag:
            name = title_tag.get_text().strip()
            name = re.sub(r"\s*[-|]\s*Price\s*History.*$", "", name, flags=re.IGNORECASE).strip()
            if name and len(name) > 5:
                return name[:200]
    except Exception:
        pass
    return None

def _ph_extract_highest(html: str) -> Optional[float]:
    pairs = re.findall(r'\[\s*\d{10,13}\s*,\s*(\d+(?:\.\d+)?)\s*\]', html)
    if pairs:
        try:
            prices = [float(p) for p in pairs if float(p) > 10]
            if prices:
                return max(prices)
        except (ValueError, TypeError):
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
    "flipkart": [
        "div.Nx9bqj.CxhGGd",
        "div.Nx9bqj",
        "div._30jeq3._16Jk6d",
        "div._30jeq3",
        "div._25b18c span",
        "div.CEmiEU div.UOCQB1",
        "div._1vC4OE._3qQ9m1",
        "div._1vC4OE",
    ],
}

TITLE_SELECTORS = {
    "amazon": ["#productTitle", "h1#title span"],
    "newegg": [".product-title"],
    "bestbuy": [".sku-title h1", ".sku-title"],
    "flipkart": [
        "span.VU-ZEz",
        "h1.yhB1nd",
        "span.B_NuCI",
        "h1._9E25nV",
        "h1.s1Q9rs",
    ],
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
        {"s": "img._396cs4._2amPTt._3qGmMb", "a": "src"},
        {"s": "img._396cs4", "a": "src"},
        {"s": "img.DByuf4.IZexXJ.jLEJ7H", "a": "src"},
        {"s": "img.DByuf4", "a": "src"},
        {"s": "img._2r_T1I", "a": "src"},
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

def _extract_flipkart_preloaded_state(html: str) -> dict:
    result = {}
    try:
        m = re.search(r'window\.__PRELOADED_STATE__\s*=\s*(\{.+?\})\s*;?\s*(?:</script>|\n)', html, re.DOTALL)
        if not m:
            return {}
        state = json.loads(m.group(1))
        page_data = state.get("pageDataV4", {})
        if not page_data:
            for key in state:
                if "page" in key.lower() and isinstance(state[key], dict):
                    page_data = state[key]
                    break
        if page_data:
            page = page_data.get("page", {})
            if isinstance(page, dict):
                data = page.get("data", page.get("pageData", {}))
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, dict) and v.get("value"):
                            val = v["value"]
                            if isinstance(val, dict):
                                title = val.get("title") or val.get("name")
                                if title:
                                    result["name"] = str(title)[:200]
                                pricing = val.get("pricing") or val.get("price")
                                if isinstance(pricing, dict):
                                    for pk in ("finalPrice", "sellingPrice", "value", "amount"):
                                        if pricing.get(pk):
                                            price_data = pricing[pk]
                                            if isinstance(price_data, dict):
                                                pv = price_data.get("value") or price_data.get("amount")
                                            else:
                                                pv = price_data
                                            if pv:
                                                try:
                                                    result["price"] = float(pv)
                                                    break
                                                except (ValueError, TypeError):
                                                    pass
    except Exception:
        pass
    return result

def _extract_flipkart_name_from_url(url: str) -> Optional[str]:
    parsed = urlparse(url)
    path = parsed.path
    parts = [p for p in path.split("/") if p and p not in ("a", "p", "dl")]
    for part in parts:
        if part.startswith("itm") or part.startswith("pid"):
            continue
        decoded = unquote(part).replace("-", " ").strip()
        if len(decoded) > 5 and not re.match(r'^[a-f0-9]+$', decoded):
            return decoded.title()[:200]
    return None

def _flipkart_direct_scrape(url: str) -> dict:
    result = {}
    try:
        session = requests.Session()
        session.headers.update(_get_headers())
        session.get("https://www.flipkart.com", timeout=10)

        session.headers.update(_get_headers(referer="https://www.flipkart.com/"))
        r = session.get(url, timeout=20, allow_redirects=True)
        if not r or r.status_code != 200:
            return {}

        html = r.text

        preloaded = _extract_flipkart_preloaded_state(html)
        if preloaded.get("name"):
            result["name"] = preloaded["name"]
        if preloaded.get("price"):
            result["price"] = preloaded["price"]

        soup = BeautifulSoup(html, "lxml")
        jd = _jsonld_product(soup)
        if jd:
            offers = jd.get("offers", {})
            if isinstance(offers, list) and offers:
                offers = offers[0]
            if isinstance(offers, dict) and not result.get("price"):
                for f in ("price", "lowPrice"):
                    v = offers.get(f)
                    if v:
                        try:
                            p = float(v)
                            if p > 0:
                                result["price"] = p
                                break
                        except (ValueError, TypeError):
                            pass
            if not result.get("name") and jd.get("name"):
                result["name"] = jd["name"][:200]
            if not result.get("image"):
                img = jd.get("image")
                if isinstance(img, str):
                    result["image"] = img
                elif isinstance(img, list) and img:
                    result["image"] = img[0]
                elif isinstance(img, dict):
                    result["image"] = img.get("url")

        if not result.get("name"):
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                t = re.sub(r"\s*[-|:]\s*(Flipkart|Buy|Online).*$", "", og_title["content"], flags=re.IGNORECASE).strip()
                if t and len(t) > 5:
                    result["name"] = t[:200]

        if not result.get("name"):
            title_tag = soup.find("title")
            if title_tag:
                t = re.sub(r"\s*[-|:]\s*(Flipkart|Buy|Online).*$", "", title_tag.get_text(), flags=re.IGNORECASE).strip()
                if t and len(t) > 5:
                    result["name"] = t[:200]

        if not result.get("name"):
            for sel in TITLE_SELECTORS.get("flipkart", []):
                el = soup.select_one(sel)
                if el:
                    t = el.get_text().strip()
                    if t:
                        result["name"] = t[:200]
                        break

        if not result.get("image"):
            og_img = soup.find("meta", property="og:image")
            if og_img and og_img.get("content") and "placeholder" not in og_img["content"].lower():
                result["image"] = og_img["content"]

        if not result.get("image"):
            for cfg in IMAGE_SELECTORS.get("flipkart", []):
                el = soup.select_one(cfg["s"])
                if el:
                    src = el.get(cfg["a"])
                    if src and "placeholder" not in src.lower():
                        result["image"] = src
                        break

        if not result.get("price"):
            for sel in PRICE_SELECTORS.get("flipkart", []):
                el = soup.select_one(sel)
                if el:
                    p = _parse_price(el.get_text())
                    if p and p > 0:
                        result["price"] = p
                        break
    except Exception:
        pass
    return result

def _flipkart_mobile_scrape(url: str) -> dict:
    mobile_url = url.replace("www.flipkart.com", "m.flipkart.com")
    r = _safe_get(mobile_url, mobile=True)
    if not r:
        return {}

    result = {}
    try:
        soup = BeautifulSoup(r.text, "lxml")

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
                                result["price"] = p
                                break
                        except (ValueError, TypeError):
                            pass
            if jd.get("name"):
                result["name"] = jd["name"][:200]
            img = jd.get("image")
            if isinstance(img, str):
                result["image"] = img
            elif isinstance(img, list) and img:
                result["image"] = img[0]
            elif isinstance(img, dict):
                result["image"] = img.get("url")

        if not result.get("name"):
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                t = re.sub(r"\s*[-|:]\s*(Flipkart).*$", "", og_title["content"], flags=re.IGNORECASE).strip()
                if t and len(t) > 5:
                    result["name"] = t[:200]

        if not result.get("image"):
            og_img = soup.find("meta", property="og:image")
            if og_img and og_img.get("content") and "placeholder" not in og_img["content"].lower():
                result["image"] = og_img["content"]

        if not result.get("price"):
            for sel in PRICE_SELECTORS.get("flipkart", []):
                el = soup.select_one(sel)
                if el:
                    p = _parse_price(el.get_text())
                    if p and p > 0:
                        result["price"] = p
                        break
    except Exception:
        pass
    return result

def _amazon_direct_scrape(url: str) -> dict:
    r = _safe_get(url)
    if not r:
        return {}
    result = {}
    try:
        soup = BeautifulSoup(r.text, "lxml")

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
                                result["price"] = p
                                break
                        except (ValueError, TypeError):
                            pass
            if jd.get("name"):
                result["name"] = jd["name"][:200]
            img = jd.get("image")
            if isinstance(img, str):
                result["image"] = img
            elif isinstance(img, list) and img:
                result["image"] = img[0]

        if not result.get("price"):
            for sel in PRICE_SELECTORS.get("amazon", []):
                el = soup.select_one(sel)
                if el:
                    p = _parse_price(el.get_text())
                    if p and p > 0:
                        result["price"] = p
                        break

        if not result.get("name"):
            name_el = soup.select_one("#productTitle")
            if name_el:
                result["name"] = name_el.get_text(strip=True)[:200]

        if not result.get("image"):
            result["image"] = _amazon_image_from_script(soup)
        if not result.get("image"):
            for cfg in IMAGE_SELECTORS.get("amazon", []):
                el = soup.select_one(cfg["s"])
                if el:
                    src = el.get(cfg["a"])
                    if src and "placeholder" not in src.lower():
                        result["image"] = re.sub(r"\._[A-Z]+\d+_", "._SL500_", src)
                        break
        if not result.get("image"):
            og_img = soup.find("meta", property="og:image")
            if og_img and og_img.get("content"):
                result["image"] = og_img["content"]

        if not result.get("name"):
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                t = re.sub(r"\s*[-|:]\s*(Amazon\.).*$", "", og_title["content"], flags=re.IGNORECASE).strip()
                if t and len(t) > 5:
                    result["name"] = t[:200]
    except Exception:
        pass
    return result

def _normalize_flipkart_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        if "dl.flipkart.com" in (parsed.hostname or ""):
            session = requests.Session()
            session.headers.update(_get_headers())
            r = session.head(url, timeout=10, allow_redirects=True)
            if r.url and "flipkart.com" in r.url:
                return _clean_flipkart_url(r.url)
        return _clean_flipkart_url(url)
    except Exception:
        return _clean_flipkart_url(url)

def extract_product_metadata(url: str) -> dict:
    store = detect_store(url)
    if not store:
        raise ValueError(f"Unsupported store URL: {url}")

    name = image = price = None

    if store == "amazon":
        resolved_url = _clean_amazon_url(url)
    elif store == "flipkart":
        resolved_url = _normalize_flipkart_url(url)
    else:
        resolved_url = url

    ph = _pricehistory_lookup(resolved_url)
    if ph.get("slug"):
        if ph.get("name") and len(ph["name"]) > 5:
            name = ph["name"]
        ph_html = _pricehistory_page(ph["slug"])
        if ph_html:
            if not name:
                name = _ph_extract_name(ph_html)
            image = _ph_extract_image(ph_html)
            price = _ph_extract_price(ph_html)

    if store == "flipkart" and not (name and price):
        direct = _flipkart_direct_scrape(resolved_url)
        name = name or direct.get("name")
        image = image or direct.get("image")
        price = price or direct.get("price")

        if not (name and price):
            mobile = _flipkart_mobile_scrape(resolved_url)
            name = name or mobile.get("name")
            image = image or mobile.get("image")
            price = price or mobile.get("price")

        if not name:
            name = _extract_flipkart_name_from_url(resolved_url)

    elif store == "amazon" and not (name and price):
        direct = _amazon_direct_scrape(resolved_url)
        name = name or direct.get("name")
        image = image or direct.get("image")
        price = price or direct.get("price")

    elif not (name and image and price):
        direct = _amazon_direct_scrape(resolved_url) if store == "amazon" else {}
        name = name or direct.get("name")
        image = image or direct.get("image")
        price = price or direct.get("price")

    return {
        "store": store,
        "product_name": name or "Unknown Product",
        "product_image_url": image or "",
        "current_price": price,
    }
