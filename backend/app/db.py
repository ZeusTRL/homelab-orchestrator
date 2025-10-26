from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://homelab:homelab@db:5432/homelab")


enjoy = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=enjoy, autoflush=False, autocommit=False)