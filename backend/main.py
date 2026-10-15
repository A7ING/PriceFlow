import asyncio
import contextlib
import faulthandler
import signal
from contextlib import asynccontextmanager

import uvicorn
from api.routes import router
from db.database import Base, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import models
from models.check_state import ProductCheckState  # noqa: F401  (реєструє таблицю для create_all)
from services.tasks import auto_update_prices

if hasattr(signal, "SIGUSR1"):
    faulthandler.register(signal.SIGUSR1, all_threads=True)


def _on_background_task_done(task: asyncio.Task) -> None:
    if task.cancelled():
        return
    print(f"[main] Фонова задача оновлення цін зупинилась: {task.exception()!r}", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    if Base is not models.Base:
        Base.metadata.create_all(bind=engine)

    task = asyncio.create_task(auto_update_prices())
    task.add_done_callback(_on_background_task_done)
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="PricePulse API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001)