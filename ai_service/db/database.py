import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, JSON, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()
raw_url = os.getenv("DATABASE_URL", "").strip()

if raw_url.startswith(("sqlite", "postgresql", "mysql")):
    DATABASE_URL = raw_url
else:
    DATABASE_URL = "sqlite+aiosqlite:///./test_database.db"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ==========================================
# 3. Modelele SQL
# ==========================================
class AIRecord(Base):
    __tablename__ = "ai_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    record_type: Mapped[str] = mapped_column(String(50))
    subject_tag: Mapped[str] = mapped_column(String(100), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=True)
    context_text: Mapped[str] = mapped_column(Text, nullable=True)
    content: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    current_level: Mapped[int] = mapped_column(default=1)
    preferred_difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    total_quizzes_taken: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now())


class StudentMastery(Base):
    __tablename__ = "student_mastery"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.user_id", ondelete="CASCADE"))
    topic_name: Mapped[str] = mapped_column(String(100))
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)
    wrong_answers_count: Mapped[int] = mapped_column(default=0)
    last_practiced: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AICache(Base):
    __tablename__ = "ai_cache"

    content_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    cached_response: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
