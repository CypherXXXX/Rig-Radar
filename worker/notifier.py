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
        "title": f"🚨 PRICE DROP ALERT: {product_name[:80]}...",
        "url": product_url,
        "color": 15158332,
        "description": f"Great news! A product you are tracking on **{store_name}** just dropped in price.",
        "fields": [
            {
                "name": "🛍️ Store",
                "value": store_name,
                "inline": True,
            },
            {
                "name": "💰 Previous Price",
                "value": f"~~₹{old_price:,.2f}~~",
                "inline": True,
            },
            {
                "name": "🔥 Current Price",
                "value": f"**₹{new_price:,.2f}**",
                "inline": True,
            },
            {
                "name": "📉 Total Discount",
                "value": f"**{drop_percentage}%** off",
                "inline": True,
            },
            {
                "name": "🔗 Product Link",
                "value": f"[Click here to grab the deal!]({product_url})",
                "inline": False,
            }
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
    <!DOCTYPE html>
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f1115; margin: 0; padding: 40px 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #161b22; border-radius: 12px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); border: 1px solid #30363d;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #58a6ff; margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;">RigRadar Alert</h1>
                <p style="color: #8b949e; font-size: 16px; margin-top: 8px;">We spotted a price drop for you.</p>
            </div>
            
            <h2 style="color: #c9d1d9; font-size: 20px; line-height: 1.4; margin-bottom: 24px; text-align: center;">{product_name}</h2>
            
            <div style="background: #0d1117; border-radius: 8px; padding: 20px; margin-bottom: 30px; border: 1px solid #21262d;">
                <table style="width: 100%; text-align: center; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; border-right: 1px solid #30363d; width: 33%;">
                            <div style="color: #8b949e; font-size: 12px; text-transform: uppercase; font-weight: 600; margin-bottom: 4px;">Store</div>
                            <div style="color: #c9d1d9; font-size: 18px; font-weight: bold;">{store.title()}</div>
                        </td>
                        <td style="padding: 10px; border-right: 1px solid #30363d; width: 33%;">
                            <div style="color: #8b949e; font-size: 12px; text-transform: uppercase; font-weight: 600; margin-bottom: 4px;">Previous</div>
                            <div style="color: #8b949e; font-size: 16px; text-decoration: line-through;">₹{old_price:,.2f}</div>
                        </td>
                        <td style="padding: 10px; width: 33%;">
                            <div style="color: #2ea043; font-size: 12px; text-transform: uppercase; font-weight: 600; margin-bottom: 4px;">Current</div>
                            <div style="color: #3fb950; font-size: 20px; font-weight: bold;">₹{new_price:,.2f}</div>
                        </td>
                    </tr>
                </table>
            </div>
            
            <div style="text-align: center; margin-bottom: 30px;">
                <h3 style="color: #ff7b72; margin: 0; font-size: 18px;">Total Discount: {drop_percentage}% OFF</h3>
            </div>
            
            <div style="text-align: center;">
                <a href="{product_url}" style="display: inline-block; background-color: #238636; color: #ffffff; text-decoration: none; padding: 14px 32px; font-size: 16px; font-weight: 600; border-radius: 6px; box-shadow: 0 1px 0 rgba(27,31,36,0.1);">
                    View Product Deal
                </a>
            </div>
            
            <hr style="border: 0; border-top: 1px solid #30363d; margin: 40px 0 20px 0;">
            <p style="color: #8b949e; font-size: 12px; text-align: center; margin: 0;">
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
    html_body = build_email_body(product_name, old_price, new_price, product_url, store, drop_percentage)

    logger.info(
        f"Email notification queued for {email_address}: "
        f"{product_name} dropped from ₹{old_price:,.2f} to ₹{new_price:,.2f} ({drop_percentage}%)"
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
