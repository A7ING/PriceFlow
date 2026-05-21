import asyncio
from datetime import datetime, timedelta
from db.database import SessionLocal
from models import models
from services.notifications import send_email_message, send_telegram_message
from services.parser import get_product_data

FREQ_MAP = {"6h": 6, "12h": 12, "24h": 24, "72h": 72}


async def check_prices():
    db = SessionLocal()
    products = db.query(models.Product).all()

    for product in products:
        try:
            settings = db.query(models.SystemSettings).filter(models.SystemSettings.user_id == product.user_id).first()
            hours_interval = FREQ_MAP.get(settings.update_freq if settings else "12h", 12)

            last_record = db.query(models.PriceHistory).filter(models.PriceHistory.product_id == product.id).order_by(
                models.PriceHistory.checked_at.desc()).first()
            if last_record and datetime.utcnow() < last_record.checked_at + timedelta(hours=hours_interval):
                continue

            parsed_data = await get_product_data(product.url)
            new_price = parsed_data.get("price")
            current_image = product.image_url or parsed_data.get("image_url")

            if new_price and new_price != product.current_price:
                old_price = product.current_price
                product.current_price = new_price
                db.add(models.PriceHistory(product_id=product.id, price=new_price))
                db.commit()

                if settings and settings.contact_info:
                    msg = (f"<b>Price Alert!</b>\n\n{product.name}\n\n"
                           f"Old price: <s>{old_price} UAH</s>\n"
                           f"New price: <b>{new_price} UAH</b>\n"
                           f"Link: <a href='{product.url}'>View Product</a>")

                    if settings.notify_method == "telegram":
                        await send_telegram_message(settings.contact_info, msg, current_image)
                    elif settings.notify_method == "email":
                        await send_email_message(settings.contact_info, "Price Alert", msg, current_image)

        except Exception as e:
            print(f"[планувальник] Помилка: {str(e)}")
    db.close()


async def auto_update_prices():
    while True:
        await check_prices()
        await asyncio.sleep(3600)