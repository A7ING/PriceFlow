import asyncio
import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from models import models
from services.notifications import send_email_message, send_telegram_message
from services.parser import get_product_data
from sqlalchemy.orm import Session

FREQ_MAP = {"6h": 6, "12h": 12, "24h": 24, "72h": 72}


async def check_prices():
    """Функція, яка перевіряє ціни з урахуванням персональних налаштувань користувача"""
    db: Session = SessionLocal()
    products = db.query(models.Product).all()

    if not products:
        db.close()
        return

    print(f"[планувальник] Перевірка черги для {len(products)} товарів...")

    for product in products:
        try:
            settings = (
                db.query(models.SystemSettings)
                .filter(models.SystemSettings.user_id == product.user_id)
                .first()
            )
            hours_interval = FREQ_MAP.get(
                settings.update_freq if settings else "12h", 12
            )
            last_record = (
                db.query(models.PriceHistory)
                .filter(models.PriceHistory.product_id == product.id)
                .order_by(models.PriceHistory.checked_at.desc())
                .first()
            )

            if last_record:
                next_check = last_record.checked_at + timedelta(hours=hours_interval)
                if datetime.utcnow() < next_check:
                    continue

            print(f"[планувальник] Оновлення ціни для: {product.name[:30]}...")
            parsed_data = await get_product_data(product.url)
            new_price = parsed_data["price"]

            if new_price and new_price != product.current_price:
                old_price = product.current_price
                product.current_price = new_price

                history_record = models.PriceHistory(
                    product_id=product.id, price=new_price
                )
                db.add(history_record)
                db.commit()

                if settings and settings.contact_info:
                    msg = ""
                    subject = ""

                    if new_price < old_price and settings.notify_drop:
                        subject = f"Price Drop Alert: {product.name[:30]}..."
                        msg = (
                            f"<b>Price Drop Alert!</b>\n\n{product.name}\n\n"
                            f"Old price: <s>{old_price} UAH</s>\n"
                            f"New price: <b>{new_price} UAH</b>\n"
                            f"Discount: <b>{old_price - new_price} UAH</b>\n\n"
                            f"<a href='{product.url}'>View Product</a>"
                        )
                    elif new_price > old_price and settings.notify_rise:
                        subject = f"Price Increase Alert: {product.name[:30]}..."
                        msg = (
                            f"<b>Price Increase Alert!</b>\n\n{product.name}\n\n"
                            f"Old price: {old_price} UAH\n"
                            f"New price: <b>{new_price} UAH</b>\n"
                            f"Increased by: {new_price - old_price} UAH\n\n"
                            f"<a href='{product.url}'>View Product</a>"
                        )

                    if msg:
                        if settings.notify_method == "telegram":
                            await send_telegram_message(
                                settings.contact_info, msg, product.image_url
                            )
                        elif settings.notify_method == "email":
                            html_msg = (
                                f"<img src='{product.image_url}' width='200'><br><br>{msg}"
                                if product.image_url
                                else msg
                            )
                            await send_email_message(
                                settings.contact_info,
                                subject,
                                msg,
                                product.image_url
                            )

        except Exception as e:
            print(f"[планувальник] Помилка оновлення {product.url}: {str(e)}")

    db.close()


async def auto_update_prices():
    """перевірка черги кожні 60 хвилин"""
    while True:
        await check_prices()
        await asyncio.sleep(3600)
