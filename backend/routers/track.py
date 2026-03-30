import traceback
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from models import (
    TrackRequest,
    TrackedItemResponse,
    PriceHistoryEntry,
    TrendingDealResponse,
    ApiResponse,
    generate_item_id,
    get_current_timestamp,
)
from services.dynamodb_service import (
    put_tracked_item,
    get_tracked_items_by_user,
    get_tracked_item,
    delete_tracked_item as db_delete_tracked_item,
    get_price_history as db_get_price_history,
    put_price_history_entry,
    get_trending_deals as db_get_trending_deals,
    update_tracked_item_price,
)
from services.metadata_extractor import extract_product_metadata, detect_store
from services.trending_scraper import get_trending_products
from services.price_history_scraper import fetch_external_price_history

router = APIRouter(prefix="/api", tags=["tracking"])

PERIOD_TO_MONTHS = {
    "1m": 1,
    "3m": 3,
    "6m": 6,
    "1y": 12,
}

@router.post("/track")
async def create_tracking_rule(request: TrackRequest):
    store = detect_store(request.product_url)
    if not store:
        raise HTTPException(
            status_code=400,
            detail="Unsupported store. Supported: Amazon, Newegg, BestBuy, Flipkart",
        )

    try:
        metadata = extract_product_metadata(request.product_url)
    except Exception as extraction_error:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to extract product metadata: {str(extraction_error)}",
        )

    item_id = generate_item_id()
    current_timestamp = get_current_timestamp()

    tracked_item = {
        "item_id": item_id,
        "user_id": request.user_id,
        "product_url": request.product_url,
        "product_name": metadata["product_name"],
        "product_image_url": metadata["product_image_url"],
        "store": metadata["store"],
        "current_price": metadata["current_price"] or 0.0,
        "target_price": request.target_price,
        "notification_type": request.notification_type.value,
        "contact_info": request.contact_info,
        "created_at": current_timestamp,
        "updated_at": current_timestamp,
    }

    put_tracked_item(tracked_item)

    if metadata["current_price"]:
        put_price_history_entry(
            {
                "item_id": item_id,
                "timestamp": current_timestamp,
                "price": metadata["current_price"],
            }
        )

    return {"data": tracked_item, "message": "Product tracking started", "success": True}

@router.get("/items/{user_id}")
async def get_user_tracked_items(user_id: str):
    items = get_tracked_items_by_user(user_id)
    return {"data": items, "message": "Tracked items retrieved", "success": True}

@router.delete("/items/{item_id}")
async def remove_tracked_item(item_id: str):
    existing_item = get_tracked_item(item_id)
    if not existing_item:
        raise HTTPException(status_code=404, detail="Tracked item not found")

    db_delete_tracked_item(item_id)
    return {"data": None, "message": "Tracking rule removed", "success": True}

@router.get("/history/{item_id}")
async def get_item_price_history(item_id: str):
    history = db_get_price_history(item_id)

    if len(history) == 0:
        item = get_tracked_item(item_id)
        if item and item.get("current_price"):
            entry = {
                "item_id": item_id,
                "timestamp": item.get("created_at", get_current_timestamp()),
                "price": item["current_price"],
            }
            put_price_history_entry(entry)
            history = [entry]

    return {"data": history, "message": "Price history retrieved", "success": True}

@router.get("/analytics/{item_id}")
async def get_analytics(
    item_id: str,
    period: Optional[str] = Query(None, description="1m, 3m, 6m, 1y"),
):
    item = get_tracked_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Tracked item not found")

    live_price = None
    try:
        metadata = extract_product_metadata(item["product_url"])
        live_price = metadata.get("current_price")
        if live_price:
            current_timestamp = get_current_timestamp()
            update_tracked_item_price(item_id, live_price, current_timestamp)
            put_price_history_entry({
                "item_id": item_id,
                "timestamp": current_timestamp,
                "price": live_price,
            })
            item = get_tracked_item(item_id)
    except Exception:
        pass

    current = live_price or item.get("current_price", 0)

    if not period:
        db_history = db_get_price_history(item_id)
        return {
            "data": {
                "item": item,
                "history": db_history,
                "stats": {
                    "current": current,
                    "lowest": None,
                    "highest": None,
                    "average": None,
                    "data_points": len(db_history),
                },
                "external_history": False,
                "period": None,
            },
            "message": "Current price fetched",
            "success": True,
        }

    months = PERIOD_TO_MONTHS.get(period, 6)
    external_history = []
    scraped_stats = {}
    try:
        external_history, scraped_stats = fetch_external_price_history(
            item["product_url"], months, current_price=current,
            product_name=item.get("product_name", ""),
        )
    except Exception as e:
        traceback.print_exc()
        pass

    db_history = db_get_price_history(item_id)

    combined_history = []
    if external_history:
        for entry in external_history:
            combined_history.append(entry)

    for entry in db_history:
        combined_history.append(entry)

    combined_history.sort(key=lambda x: x.get("timestamp", ""))

    seen_dates = set()
    deduplicated = []
    for entry in combined_history:
        ts = entry.get("timestamp", "")[:10]
        if ts not in seen_dates:
            seen_dates.add(ts)
            deduplicated.append(entry)

    all_prices = [e["price"] for e in deduplicated if e.get("price") and e["price"] > 0]
    if current and current > 0:
        all_prices.append(current)

    valid_scraped = (
        scraped_stats.get("highest")
        and scraped_stats.get("lowest")
        and scraped_stats["lowest"] > 0
        and scraped_stats["highest"] > 0
        and scraped_stats["lowest"] <= scraped_stats["highest"]
    )

    if valid_scraped and current and current > 0:
        if scraped_stats["lowest"] < current * 0.10 or scraped_stats["highest"] > current * 5.0:
            valid_scraped = False

    if valid_scraped:
        avg = scraped_stats.get("average")
        if not avg or avg <= 0:
            avg = round(sum(all_prices) / len(all_prices), 2) if all_prices else current
        stats = {
            "current": current,
            "lowest": scraped_stats["lowest"],
            "highest": scraped_stats["highest"],
            "average": avg,
            "data_points": len(deduplicated),
        }
    elif all_prices:
        stats = {
            "current": current,
            "lowest": min(all_prices),
            "highest": max(all_prices),
            "average": round(sum(all_prices) / len(all_prices), 2),
            "data_points": len(deduplicated),
        }
    else:
        stats = {
            "current": current,
            "lowest": current,
            "highest": current,
            "average": current,
            "data_points": 1 if current and current > 0 else 0,
        }

    if not deduplicated and current and current > 0:
        now_ts = get_current_timestamp()
        deduplicated = [{"timestamp": now_ts, "price": current}]
        stats["data_points"] = 1

    return {
        "data": {
            "item": item,
            "history": deduplicated,
            "stats": stats,
            "external_history": len(external_history) > 0,
            "period": period,
        },
        "message": f"Analytics for {period or 'current'}",
        "success": True,
    }

@router.post("/refresh/{item_id}")
async def refresh_item_price(item_id: str):
    item = get_tracked_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Tracked item not found")

    try:
        metadata = extract_product_metadata(item["product_url"])
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to scrape current price: {str(e)}",
        )

    new_price = metadata.get("current_price")
    if not new_price:
        raise HTTPException(status_code=422, detail="Could not extract current price")

    current_timestamp = get_current_timestamp()
    update_tracked_item_price(item_id, new_price, current_timestamp)
    put_price_history_entry(
        {
            "item_id": item_id,
            "timestamp": current_timestamp,
            "price": new_price,
        }
    )

    updated_item = get_tracked_item(item_id)
    return {"data": updated_item, "message": "Price refreshed", "success": True}

@router.get("/trending")
async def get_trending():
    deals = db_get_trending_deals()
    return {"data": deals, "message": "Trending deals retrieved", "success": True}

@router.get("/trending-products")
async def get_trending_tech(force: bool = False):
    try:
        products = get_trending_products(force_refresh=force)
        return {"data": products, "message": "Trending tech products", "success": True}
    except Exception as e:
        return {"data": [], "message": f"Error: {str(e)}", "success": False}
