from datetime import datetime, timezone

from db.database import Base
from sqlalchemy import Column, DateTime, Integer, String


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ProductCheckState(Base):
    __tablename__ = "product_check_state"

    product_id = Column(Integer, primary_key=True, autoincrement=False)
    last_checked_at = Column(DateTime, nullable=False, default=utcnow)
    fail_count = Column(Integer, nullable=False, default=0)
    last_error = Column(String(300), nullable=True)


def mark_checked(db, product_id: int, error: str | None = None) -> None:
    state = (
        db.query(ProductCheckState)
        .filter(ProductCheckState.product_id == product_id)
        .first()
    )
    if state is None:
        state = ProductCheckState(product_id=product_id, fail_count=0)
        db.add(state)

    state.last_checked_at = utcnow()
    if error:
        state.fail_count = (state.fail_count or 0) + 1
        state.last_error = error[:300]
    else:
        state.fail_count = 0
        state.last_error = None