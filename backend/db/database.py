import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://admin:adminpassword@db:5432/price_analytics"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=15,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={"connect_timeout": 10},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()