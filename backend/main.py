import asyncio
from contextlib import asynccontextmanager

import uvicorn
from api.routes import router
from db.database import engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import models
from services.tasks import auto_update_prices

@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    task = asyncio.create_task(auto_update_prices())
    yield
    task.cancel()

app = FastAPI(title="PricePulse API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001)
