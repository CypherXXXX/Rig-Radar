import os
import json
import logging
from typing import Optional
from urllib.request import Request, urlopen
from urllib.parse import quote

logger = logging.getLogger("rigradar.notifier")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_SECRET", "")

def calculate_drop_percentage(old_price: float, new_price: float) -> float:
    if old_price <= 0:
        return 0.0
    return round(((old_price - new_price) / old_price) * 100, 1)

def build_discord_embed(
    product_name: str,
    product_image_url: str,
    old_price: float,
    new_price: float,
    product_url: str,
    store: str,
) -> dict:
    drop_percentage = calculate_drop_percentage(old_price, new_price)
    store_display_names = {
        "amazon": "Amazon",
        "newegg": "Newegg",
        "bestbuy": "Best Buy",
        "flipkart": "Flipkart",
    }
    store_name = store_display_names.get(store, store.title())

    embed = {
        "title": f"🔻 Price Drop Alert — {product_name[:100]}",
        "url": product_url,
        "color": 2067276,
        "fields": [
            {
                "name": "📦 Store",
                "value": store_name,
                "inline": True,
            },
            {
                "name": "💰 Old Price",
                "value": f"~~${old_price:.2f}~~",
                "inline": True,
            },
            {
                "name": "🔥 New Price",
                "value": f"**${new_price:.2f}**",
                "inline": True,
            },
            {
                "name": "📉 Drop",
                "value": f"**{drop_percentage}%** off",
                "inline": True,
            },
        ],
        "footer": {
            "text": "RigRadar — Secure the drop. Build the rig.",
        },
    }

    if product_image_url:
        embed["thumbnail"] = {"url": product_image_url}

    return embed

def send_discord_notification(
    webhook_url: str,
    product_name: str,
    product_image_url: str,
    old_price: float,
    new_price: float,
    product_url: str,
    store: str,
) -> bool:
    target_webhook = webhook_url or DISCORD_WEBHOOK_URL
    if not target_webhook:
        logger.warning("No Discord webhook URL configured")
        return False

    embed = build_discord_embed(
        product_name, product_image_url, old_price, new_price, product_url, store
    )

    payload = json.dumps(
        {
            "username": "RigRadar",
            "avatar_url": "https://i.imgur.com/k2RMKKY.png",
            "embeds": [embed],
        }
    ).encode("utf-8")

    request = Request(
        target_webhook,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request) as response:
            logger.info(f"Discord notification sent: {response.status}")
            return response.status in (200, 204)
    except Exception as discord_error:
        logger.error(f"Discord notification failed: {str(discord_error)}")
        return False

def build_email_body(
    product_name: str,
    old_price: float,
    new_price: float,
    product_url: str,
    store: str,
    drop_percentage: float,
) -> str:
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: 
        <div style="max-width: 600px; margin: 0 auto; background: 
            <h1 style="color: 
            <h2 style="color: 
            <table style="width: 100%; margin-bottom: 24px;">
                <tr>
                    <td style="padding: 12px; background: 
                        <div style="color: 
                        <div style="color: 
                    </td>
                    <td style="padding: 12px; background: 
                        <div style="color: 
                        <div style="color: 
                    </td>
                    <td style="padding: 12px; background: 
                        <div style="color: 
                        <div style="color: 
                    </td>
                </tr>
            </table>
            <a href="{product_url}" style="display: inline-block; background: linear-gradient(135deg, 
                View Product on {store.title()}
            </a>
            <p style="color: 
                RigRadar — Secure the drop. Build the rig.
            </p>
        </div>
    </body>
    </html>
    """

def send_email_notification(
    email_address: str,
    product_name: str,
    old_price: float,
    new_price: float,
    product_url: str,
    store: str,
) -> bool:
    drop_percentage = calculate_drop_percentage(old_price, new_price)

    logger.info(
        f"Email notification queued for {email_address}: "
        f"{product_name} dropped from ${old_price:.2f} to ${new_price:.2f} ({drop_percentage}%)"
    )

    return True

def send_notification(
    notification_type: str,
    contact_info: str,
    product_name: str,
    product_image_url: str,
    old_price: float,
    new_price: float,
    product_url: str,
    store: str,
) -> bool:
    if notification_type == "discord":
        return send_discord_notification(
            contact_info, product_name, product_image_url,
            old_price, new_price, product_url, store,
        )
    elif notification_type == "email":
        return send_email_notification(
            contact_info, product_name,
            old_price, new_price, product_url, store,
        )

    logger.warning(f"Unknown notification type: {notification_type}")
    return False
