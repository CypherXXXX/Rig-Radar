import os
import asyncio
import logging
import boto3
from decimal import Decimal
from datetime import datetime
from scraper import scrape_product
from throttle import process_all_items
from notifier import send_notification, calculate_drop_percentage

logger = logging.getLogger("rigradar.worker")
logger.setLevel(logging.INFO)

REGION = os.getenv("AWS_REGION", "us-east-1")
TABLE_TRACKED = os.getenv("DYNAMODB_TABLE_TRACKED", "RigRadar_TrackedItems")
TABLE_HISTORY = os.getenv("DYNAMODB_TABLE_HISTORY", "RigRadar_PriceHistory")
TABLE_TRENDING = os.getenv("DYNAMODB_TABLE_TRENDING", "RigRadar_Trending")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
tracked_table = dynamodb.Table(TABLE_TRACKED)
history_table = dynamodb.Table(TABLE_HISTORY)
trending_table = dynamodb.Table(TABLE_TRENDING)

def get_all_tracked_items() -> list[dict]:
    items = []
    response = tracked_table.scan()
    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        response = tracked_table.scan(
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items", []))

    return items

def process_single_item(item: dict) -> dict:
    item_id = item["item_id"]
    product_url = item["product_url"]
    store = item["store"]
    old_price = float(item.get("current_price", 0))
    target_price = float(item.get("target_price", 0))

    try:
        scraped_data = scrape_product(product_url, store)
        new_price = scraped_data.get("price")

        if new_price is None:
            logger.warning(f"Could not extract price for item {item_id}")
            return {"item_id": item_id, "status": "price_extraction_failed"}

        current_timestamp = datetime.utcnow().isoformat() + "Z"

        tracked_table.update_item(
            Key={"item_id": item_id},
            UpdateExpression="SET current_price = :price, updated_at = :updated",
            ExpressionAttributeValues={
                ":price": Decimal(str(new_price)),
                ":updated": current_timestamp,
            },
        )

        history_table.put_item(
            Item={
                "item_id": item_id,
                "timestamp": current_timestamp,
                "price": Decimal(str(new_price)),
            }
        )

        if new_price <= target_price and old_price > target_price:
            notification_sent = send_notification(
                notification_type=item.get("notification_type", "discord"),
                contact_info=item.get("contact_info", ""),
                product_name=item.get("product_name", "Unknown Product"),
                product_image_url=item.get("product_image_url", ""),
                old_price=old_price,
                new_price=new_price,
                product_url=product_url,
                store=store,
            )

            if notification_sent:
                logger.info(f"Notification sent for item {item_id}")

        if old_price > 0 and new_price < old_price:
            drop_pct = calculate_drop_percentage(old_price, new_price)
            if drop_pct >= 5:
                trending_table.put_item(
                    Item={
                        "item_id": item_id,
                        "product_name": item.get("product_name", ""),
                        "product_image_url": item.get("product_image_url", ""),
                        "product_url": product_url,
                        "store": store,
                        "previous_price": Decimal(str(old_price)),
                        "current_price": Decimal(str(new_price)),
                        "drop_percentage": Decimal(str(drop_pct)),
                        "updated_at": current_timestamp,
                    }
                )

        return {
            "item_id": item_id,
            "status": "success",
            "old_price": old_price,
            "new_price": new_price,
        }

    except Exception as scrape_error:
        logger.error(f"Failed to scrape item {item_id}: {str(scrape_error)}")
        return {"item_id": item_id, "status": "error", "error": str(scrape_error)}

def lambda_handler(event, context):
    logger.info("RigRadar scraper worker triggered")

    all_items = get_all_tracked_items()
    logger.info(f"Found {len(all_items)} tracked items to process")

    if not all_items:
        return {
            "statusCode": 200,
            "body": "No tracked items to process",
        }

    serialized_items = []
    for item in all_items:
        serialized = {}
        for key, value in item.items():
            if isinstance(value, Decimal):
                serialized[key] = float(value)
            else:
                serialized[key] = value
        serialized_items.append(serialized)

    results = asyncio.get_event_loop().run_until_complete(
        process_all_items(serialized_items, process_single_item)
    )

    successful_count = sum(
        1 for r in results if r and r.get("status") == "success"
    )
    failed_count = sum(
        1 for r in results if r and r.get("status") in ("error", "price_extraction_failed")
    )

    logger.info(
        f"Scraping complete: {successful_count} succeeded, {failed_count} failed out of {len(all_items)} items"
    )

    return {
        "statusCode": 200,
        "body": {
            "total_items": len(all_items),
            "successful": successful_count,
            "failed": failed_count,
        },
    }
