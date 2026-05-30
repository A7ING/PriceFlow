from urllib.parse import urlparse
from db.database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from models import models
from schemas import schemas
from services.auth import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from services.notifications import send_email_message, send_telegram_message
from services.parser import get_product_data
from sqlalchemy.orm import Session

router = APIRouter()


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
    existing_product = (
        db.query(models.Product)
        .filter(
            models.Product.url == item.url, models.Product.user_id == current_user.id
        )
        .first()
    )

    if existing_product:
        raise HTTPException(
            status_code=400, detail="This product is already being tracked"
        )

    try:
        parsed_data = await get_product_data(item.url)

        new_product = models.Product(
            name=parsed_data["name"],
            url=item.url,
            current_price=parsed_data["price"],
            image_url=parsed_data["image_url"],
            user_id=current_user.id,
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        history_record = models.PriceHistory(
            product_id=new_product.id, price=parsed_data["price"]
        )
        db.add(history_record)
        db.commit()

        return {"status": "success", "product_id": new_product.id}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    db.delete(product)
    db.commit()

    return {"status": "success", "message": "Product and its history deleted"}


@router.post("/products/{product_id}/force-update")
async def force_update_product(
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

    try:
        parsed_data = await get_product_data(product.url)
        new_price = parsed_data["price"]
        old_price = product.current_price

        if new_price != old_price:
            product.current_price = new_price
            history_record = models.PriceHistory(product_id=product.id, price=new_price)
            db.add(history_record)
            db.commit()

            settings = (
                db.query(models.SystemSettings)
                .filter(models.SystemSettings.user_id == current_user.id)
                .first()
            )

            if settings and settings.contact_info:
                message = None

                if old_price and new_price < old_price and settings.notify_drop:
                    discount = old_price - new_price
                    message = (
                        f"<b>PRICE DROP ALERT!</b>\n\n"
                        f"<b>{product.name}</b>\n"
                        f"Old price: <s>{old_price} UAH</s>\n"
                        f"New price: <b>{new_price} UAH</b>\n"
                        f"Discount: <b>{discount} UAH</b>\n\n"
                        f"<a href='{product.url}'><b>View Product</b></a>"
                    )

                elif old_price and new_price > old_price and settings.notify_rise:
                    message = (
                        f"<b>PRICE INCREASE ALERT!</b>\n\n"
                        f"<b>{product.name}</b>\n"
                        f"Old price: <s>{old_price} UAH</s>\n"
                        f"New price: <b>{new_price} UAH</b>\n\n"
                        f"<a href='{product.url}'><b>View Product</b></a>"
                    )

                if message:
                    if settings.notify_method == "telegram":
                        await send_telegram_message(
                            settings.contact_info, message, product.image_url
                        )
                    elif settings.notify_method == "email":
                        await send_email_message(
                            settings.contact_info, "PriceFlow Alert!", message, product.image_url
                        )

            return {"status": "success", "message": f"Price updated: {new_price} UAH"}
        else:
            return {"status": "success", "message": "Price has not changed"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    settings = (
        db.query(models.SystemSettings)
        .filter(models.SystemSettings.user_id == current_user.id)
        .first()
    )
    if not settings:
        settings = models.SystemSettings(user_id=current_user.id)
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
            .filter(models.Product.user_id == current_user.id)
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
            f"<b>Check Frequency:</b> {new_settings.update_freq}\n"
            f"<b>Alert Conditions:</b> {conditions_text}\n\n"
            f"<b>Currently tracking ({products_count} items):</b>\n"
        )

        for p in products:
            message += f"- {p.name} (<b>{p.current_price} UAH</b>)\n"

        if new_settings.notify_method == "telegram":
            image_url = products[-1].image_url if products else None
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

    histories = (
        db.query(models.PriceHistory)
        .filter(models.PriceHistory.product_id.in_(product_ids))
        .order_by(models.PriceHistory.checked_at.desc())
        .all()
    )

    total_value = sum(p.current_price for p in products if p.current_price)
    active_items = len(products)
    checks_performed = len(histories)

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
    for h in histories[:8]:
        prod = next((p for p in products if p.id == h.product_id), None)
        prod_name = (
            prod.name[:45] + "..."
            if prod and len(prod.name) > 45
            else (prod.name if prod else "Unknown")
        )

        is_first = (
            db.query(models.PriceHistory)
            .filter(models.PriceHistory.product_id == h.product_id)
            .order_by(models.PriceHistory.checked_at.asc())
            .first()
            .id
            == h.id
        )

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
