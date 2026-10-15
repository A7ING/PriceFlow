import asyncio
from datetime import timedelta

from db.database import SessionLocal
from models import models
from models.check_state import ProductCheckState, mark_checked, utcnow
from services.notifications import build_price_alert, send_alert
from services.parser import get_product_data

FREQ_MAP = {"6h": 6, "12h": 12, "24h": 24, "72h": 72}

STARTUP_DELAY = 30
CYCLE_PAUSE = 3600
PAUSE_BETWEEN_PARSES = 3
MAX_BACKOFF_STEPS = 3


async def check_product(product_id: int) -> bool:
    """Перевіряє один товар. Повертає True, якщо запускався парсинг."""
    db = SessionLocal()
    try:
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if product is None:
            return False
        url = product.url
        user_id = product.user_id

        settings = (
            db.query(models.SystemSettings)
            .filter(models.SystemSettings.user_id == user_id)
            .first()
        )
        hours = FREQ_MAP.get(settings.update_freq if settings else "12h", 12)

        state = (
            db.query(ProductCheckState)
            .filter(ProductCheckState.product_id == product_id)
            .first()
        )
        if state is not None:
            last_checked, fails = state.last_checked_at, (state.fail_count or 0)
        else:
            last = (
                db.query(models.PriceHistory)
                .filter(models.PriceHistory.product_id == product_id)
                .order_by(models.PriceHistory.checked_at.desc())
                .first()
            )
            last_checked, fails = (last.checked_at if last else None), 0

        delay_hours = min(hours * (2 ** min(fails, MAX_BACKOFF_STEPS)), max(hours, 72))
        if last_checked and utcnow() < last_checked + timedelta(hours=delay_hours):
            return False

        db.rollback()

        try:
            parsed = await get_product_data(url, background=True)
        except Exception as exc:
            print(f"[планувальник] Не вдалося оновити {url}: {exc}", flush=True)
            if db.query(models.Product.id).filter(models.Product.id == product_id).first():
                mark_checked(db, product_id, error=str(exc))
                db.commit()
            return True

        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if product is None:
            return True

        new_price = parsed.get("price")
        old_price = product.current_price
        image = product.image_url or parsed.get("image_url")
        if not product.image_url and image:
            product.image_url = image

        alert = None
        if new_price and new_price != old_price:
            product.current_price = new_price
            db.add(models.PriceHistory(product_id=product_id, price=new_price))
            settings = (
                db.query(models.SystemSettings)
                .filter(models.SystemSettings.user_id == user_id)
                .first()
            )
            alert = build_price_alert(settings, product.name, product.url, image, old_price, new_price)

        mark_checked(db, product_id)
        db.commit()

        if alert:
            await send_alert(alert)
        return True
    except Exception as exc:
        db.rollback()
        print(f"[планувальник] Помилка для товару {product_id}: {exc!r}", flush=True)
        return True
    finally:
        db.close()


async def check_prices() -> None:
    db = SessionLocal()
    try:
        product_ids = [row[0] for row in db.query(models.Product.id).all()]
    finally:
        db.close()

    parsed_count = 0
    for product_id in product_ids:
        if await check_product(product_id):
            parsed_count += 1
            await asyncio.sleep(PAUSE_BETWEEN_PARSES)

    print(f"[планувальник] Цикл завершено: перевірено {parsed_count} з {len(product_ids)}", flush=True)


async def auto_update_prices() -> None:
    await asyncio.sleep(STARTUP_DELAY)
    while True:
        try:
            await check_prices()
        except Exception as exc:
            print(f"[планувальник] Критична помилка циклу: {exc!r}", flush=True)
        await asyncio.sleep(CYCLE_PAUSE)