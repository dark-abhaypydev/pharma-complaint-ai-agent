from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Integer, Float
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./complaints.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    complaint_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    batch_lot_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manufacturing_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    expiry_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quantity_affected: Mapped[str | None] = mapped_column(String(100), nullable=True)
    complaint_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    complaint_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    detailed_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    initial_severity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(50), nullable=True)
    risk_classification: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    capa_recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    completeness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
