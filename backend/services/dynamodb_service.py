import os
import time
import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import Any, Optional
from decimal import Decimal
from datetime import datetime

REGION = os.getenv("AWS_REGION", "us-east-1")
TABLE_TRACKED = os.getenv("DYNAMODB_TABLE_TRACKED", "RigRadar_TrackedItems")
TABLE_HISTORY = os.getenv("DYNAMODB_TABLE_HISTORY", "RigRadar_PriceHistory")
TABLE_USERS = os.getenv("DYNAMODB_TABLE_USERS", "RigRadar_Users")
TABLE_TRENDING = os.getenv("DYNAMODB_TABLE_TRENDING", "RigRadar_Trending")

dynamodb_resource = boto3.resource("dynamodb", region_name=REGION)
tracked_items_table = dynamodb_resource.Table(TABLE_TRACKED)
price_history_table = dynamodb_resource.Table(TABLE_HISTORY)
users_table = dynamodb_resource.Table(TABLE_USERS)
trending_table = dynamodb_resource.Table(TABLE_TRENDING)

def convert_floats_to_decimal(data: dict[str, Any]) -> dict[str, Any]:
    converted: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, float):
            converted[key] = Decimal(str(value))
        elif isinstance(value, dict):
            converted[key] = convert_floats_to_decimal(value)
        else:
            converted[key] = value
    return converted

def convert_decimals_to_float(data: dict[str, Any]) -> dict[str, Any]:
    converted: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, Decimal):
            converted[key] = float(value)
        elif isinstance(value, dict):
            converted[key] = convert_decimals_to_float(value)
        else:
            converted[key] = value
    return converted

def put_tracked_item(item_data: dict) -> dict:
    safe_data = convert_floats_to_decimal(item_data)
    tracked_items_table.put_item(Item=safe_data)
    return item_data

def get_tracked_items_by_user(user_id: str) -> list[dict]:
    response = tracked_items_table.scan(
        FilterExpression=Attr("user_id").eq(user_id),
    )
    items = [convert_decimals_to_float(item) for item in response.get("Items", [])]

    while "LastEvaluatedKey" in response:
        response = tracked_items_table.scan(
            FilterExpression=Attr("user_id").eq(user_id),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(
            [convert_decimals_to_float(item) for item in response.get("Items", [])]
        )

    return items

def get_tracked_item(item_id: str) -> Optional[dict]:
    response = tracked_items_table.get_item(Key={"item_id": item_id})
    item = response.get("Item")
    if item:
        return convert_decimals_to_float(item)
    return None

def delete_tracked_item(item_id: str) -> bool:
    tracked_items_table.delete_item(Key={"item_id": item_id})
    return True

def update_tracked_item_price(item_id: str, new_price: float, updated_at: str) -> None:
    tracked_items_table.update_item(
        Key={"item_id": item_id},
        UpdateExpression="SET current_price = :price, updated_at = :updated",
        ExpressionAttributeValues={
            ":price": Decimal(str(new_price)),
            ":updated": updated_at,
        },
    )

def put_price_history_entry(entry_data: dict) -> None:
    timestamp_val = entry_data.get("timestamp", "")
    if not isinstance(timestamp_val, str) or not timestamp_val:
        timestamp_val = datetime.utcnow().isoformat() + "Z"

    db_entry = {
        "item_id": entry_data.get("item_id", ""),
        "timestamp": timestamp_val,
        "price": Decimal(str(entry_data.get("price", 0))),
    }
    price_history_table.put_item(Item=db_entry)

def get_price_history(item_id: str) -> list[dict]:
    response = price_history_table.query(
        KeyConditionExpression=Key("item_id").eq(item_id),
        ScanIndexForward=True,
    )

    results = []
    for item in response.get("Items", []):
        entry = convert_decimals_to_float(item)
        results.append({
            "item_id": entry.get("item_id", item_id),
            "timestamp": entry.get("timestamp", ""),
            "price": entry.get("price", 0),
        })

    return results

def get_all_tracked_items() -> list[dict]:
    response = tracked_items_table.scan()
    items = [convert_decimals_to_float(item) for item in response.get("Items", [])]

    while "LastEvaluatedKey" in response:
        response = tracked_items_table.scan(
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(
            [convert_decimals_to_float(item) for item in response.get("Items", [])]
        )

    return items

def put_trending_deal(deal_data: dict) -> None:
    safe_data = convert_floats_to_decimal(deal_data)
    trending_table.put_item(Item=safe_data)

def get_trending_deals() -> list[dict[str, Any]]:
    response = trending_table.scan()
    deals: list[dict[str, Any]] = [convert_decimals_to_float(item) for item in response.get("Items", [])]
    sorted_deals: list[dict[str, Any]] = sorted(deals, key=lambda x: x.get("drop_percentage", 0), reverse=True)
    return list(sorted_deals[:20])

def batch_write_price_history(entries: list[dict]) -> None:
    with price_history_table.batch_writer() as batch:
        for entry in entries:
            timestamp_val = entry.get("timestamp", "")
            if not isinstance(timestamp_val, str) or not timestamp_val:
                timestamp_val = datetime.utcnow().isoformat() + "Z"

            db_entry = {
                "item_id": entry.get("item_id", ""),
                "timestamp": timestamp_val,
                "price": Decimal(str(entry.get("price", 0))),
            }
            batch.put_item(Item=db_entry)
