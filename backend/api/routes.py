import html
from urllib.parse import urlparse

from db.database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from models import models
from models.check_state import ProductCheckState, mark_checked
from schemas import schemas
from services.auth import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from services.notifications import (
    build_price_alert,
    format_price,
    send_alert,
    send_email_message,
    send_telegram_message,
)
from services.parser import get_product_data, normalize_url
from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter()

MSG_GENERIC_PARSE_ERROR = "Не вдалося отримати дані зі сторінки. Спробуйте пізніше."


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = (
        db.query(models.User).filter(models.User.username == user.username).first()
    )
    if db_user:
        raise HTTPException(
            status_code=400, detail="User with this username already exists"
        )

    hashed_password = get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=schemas.Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = (
        db.query(models.User).filter(models.User.username == form_data.username).first()
    )
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/track")
async def track_product(
    item: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user_id = current_user.id
    raw_url = str(item.url)

    try:
        clean_url, _host = normalize_url(raw_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    url_variants = list({raw_url, clean_url})

    def already_tracked() -> bool:
        return (
            db.query(models.Product.id)
            .filter(models.Product.user_id == user_id, models.Product.url.in_(url_variants))
            .first()
            is not None
        )

    if already_tracked():
        raise HTTPException(
            status_code=400, detail="This product is already being tracked"
        )

    db.rollback()

    try:
        parsed_data = await get_product_data(clean_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[routes] /track помилка: {e!r}", flush=True)
        raise HTTPException(status_code=400, detail=MSG_GENERIC_PARSE_ERROR)

    if already_tracked():
        raise HTTPException(
            status_code=400, detail="This product is already being tracked"
        )

    new_product = models.Product(
        name=parsed_data["name"],
        url=clean_url,
        current_price=parsed_data["price"],
        image_url=parsed_data["image_url"],
        user_id=user_id,
    )
    db.add(new_product)
    db.flush()
    product_id = new_product.id

    db.add(models.PriceHistory(product_id=product_id, price=parsed_data["price"]))
    mark_checked(db, product_id)
    db.commit()

    return {"status": "success", "product_id": product_id}


@router.get("/products", response_model=list[schemas.ProductResponse])
def get_products(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    products = (
        db.query(models.Product).filter(models.Product.user_id == current_user.id).all()
    )
    return products


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = (
        db.query(models.Product)
        .filter(
            models.Product.id == product_id, models.Product.user_id == current_user.id
        )
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.query(models.PriceHistory).filter(
        models.PriceHistory.product_id == product_id
    ).delete()
    db.query(ProductCheckState).filter(
        ProductCheckState.product_id == product_id
    ).delete()
    db.delete(product)
    db.commit()

    return {"status": "success", "message": "Product and its history deleted"}


@router.post("/products/{product_id}/force-update")
async def force_update_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user_id = current_user.id

    def load_product():
        return (
            db.query(models.Product)
            .filter(models.Product.id == product_id, models.Product.user_id == user_id)
            .first()
        )

    product = load_product()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    url = product.url
    db.rollback()

    try:
        parsed_data = await get_product_data(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[routes] force-update помилка: {e!r}", flush=True)
        raise HTTPException(status_code=400, detail=MSG_GENERIC_PARSE_ERROR)

    product = load_product()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_price = parsed_data["price"]
    old_price = product.current_price
    changed = new_price != old_price

    if not product.image_url and parsed_data.get("image_url"):
        product.image_url = parsed_data["image_url"]

    alert = None
    if changed:
        product.current_price = new_price
        db.add(models.PriceHistory(product_id=product.id, price=new_price))

        settings = (
            db.query(models.SystemSettings)
            .filter(models.SystemSettings.user_id == user_id)
            .first()
        )
        alert = build_price_alert(
            settings, product.name, product.url, product.image_url, old_price, new_price
        )

    mark_checked(db, product.id)
    db.commit()

    if alert:
        await send_alert(alert)

    if changed:
        return {"status": "success", "message": f"Price updated: {format_price(new_price)} UAH"}
    return {"status": "success", "message": "Price has not changed"}


@router.get("/settings", response_model=schemas.SettingsResponse)
async def get_settings(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    settings = (
        db.query(models.SystemSettings)
        .filter(models.SystemSettings.user_id == current_user.id)
        .first()
    )
    if not settings:
        settings = models.SystemSettings(user_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.post("/settings")
async def update_settings(
    new_settings: schemas.SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user_id = current_user.id
    settings = (
        db.query(models.SystemSettings)
        .filter(models.SystemSettings.user_id == user_id)
        .first()
    )
    if not settings:
        settings = models.SystemSettings(user_id=user_id)
        db.add(settings)

    settings.update_freq = new_settings.update_freq
    settings.notify_drop = new_settings.notify_drop
    settings.notify_rise = new_settings.notify_rise
    settings.notify_method = new_settings.notify_method
    settings.contact_info = new_settings.contact_info

    db.commit()

    if new_settings.contact_info:
        products = (
            db.query(models.Product)
            .filter(models.Product.user_id == user_id)
            .all()
        )
        products_count = len(products)

        conditions = []
        if new_settings.notify_drop:
            conditions.append("Price Drops")
        if new_settings.notify_rise:
            conditions.append("Price Increases")

        conditions_text = ", ".join(conditions) if conditions else "None"

        message = (
            f"<b>PriceFlow Alerts Enabled!</b>\n\n"
            f"<b>Check Frequency:</b> {html.escape(str(new_settings.update_freq))}\n"
            f"<b>Alert Conditions:</b> {conditions_text}\n\n"
            f"<b>Currently tracking ({products_count} items):</b>\n"
        )

        for p in products:
            message += f"- {html.escape(p.name or '')} (<b>{format_price(p.current_price)} UAH</b>)\n"

        image_url = products[-1].image_url if products else None
        db.rollback()

        if new_settings.notify_method == "telegram":
            await send_telegram_message(new_settings.contact_info, message, image_url)

        elif new_settings.notify_method == "email":
            subject = "PriceFlow: Tracking Enabled"
            await send_email_message(new_settings.contact_info, subject, message)

    return {"status": "success", "message": "Settings saved"}


@router.get("/analytics")
async def get_analytics_data(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    products = (
        db.query(models.Product).filter(models.Product.user_id == current_user.id).all()
    )
    product_ids = [p.id for p in products]

    if product_ids:
        checks_performed = (
            db.query(func.count(models.PriceHistory.id))
            .filter(models.PriceHistory.product_id.in_(product_ids))
            .scalar()
            or 0
        )
        recent_histories = (
            db.query(models.PriceHistory)
            .filter(models.PriceHistory.product_id.in_(product_ids))
            .order_by(models.PriceHistory.checked_at.desc())
            .limit(8)
            .all()
        )
    else:
        checks_performed = 0
        recent_histories = []

    total_value = sum(p.current_price for p in products if p.current_price)
    active_items = len(products)

    colors = [
        "#00a046",
        "#7b61ff",
        "#3b82f6",
        "#f59e0b",
        "#ef4444",
        "#ec4899",
        "#8b5cf6",
    ]
    platform_counts = {}

    for p in products:
        domain = urlparse(p.url).netloc.replace("www.", "")
        platform_counts[domain] = platform_counts.get(domain, 0) + 1

    platform_distribution = []
    for i, (name, count) in enumerate(platform_counts.items()):
        platform_distribution.append(
            {"name": name.capitalize(), "value": count, "fill": colors[i % len(colors)]}
        )

    budget = sum(1 for p in products if p.current_price and p.current_price < 1000)
    mid = sum(
        1 for p in products if p.current_price and 1000 <= p.current_price <= 10000
    )
    premium = sum(1 for p in products if p.current_price and p.current_price > 10000)

    price_segments = [
        {"name": "Budget (< 1K)", "count": budget, "fill": "#3b82f6"},
        {"name": "Mid (1K-10K)", "count": mid, "fill": "#f59e0b"},
        {"name": "Premium (> 10K)", "count": premium, "fill": "#ef4444"},
    ]

    activity_logs = []
    for h in recent_histories:
        prod = next((p for p in products if p.id == h.product_id), None)
        prod_name = (
            prod.name[:45] + "..."
            if prod and len(prod.name) > 45
            else (prod.name if prod else "Unknown")
        )

        first_record = (
            db.query(models.PriceHistory.id)
            .filter(models.PriceHistory.product_id == h.product_id)
            .order_by(models.PriceHistory.checked_at.asc())
            .first()
        )
        is_first = bool(first_record) and first_record[0] == h.id

        activity_logs.append(
            {
                "id": f"hist-{h.id}",
                "date": h.checked_at.strftime("%d.%m.%Y"),
                "type": "add" if is_first else "update",
                "message": (
                    f"Started tracking: {prod_name}"
                    if is_first
                    else f"Price update: {prod_name} -> {h.price} UAH"
                ),
            }
        )

    return {
        "status": "success",
        "metrics": {
            "total_value": total_value,
            "active_items": active_items,
            "checks_performed": checks_performed,
        },
        "charts": {
            "platforms": platform_distribution,
            "price_segments": price_segments,
        },
        "logs": activity_logs,
    }