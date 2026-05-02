from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
import hashlib
from uuid import UUID

# Importă modelele tale
from .database import AICache, AIRecord


class AIRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Salvarea quiz-urilor generate ---
    async def save_ai_record(
            self,
            user_id: UUID,
            record_type: str,
            subject_tag: str | None,
            difficulty: str | None,
            context_text: str | None,
            content: dict
    ):
        # conversie defensivă (în caz că vine string din API)
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        new_record = AIRecord(
            user_id=user_id,
            record_type=record_type,
            subject_tag=subject_tag,
            difficulty=difficulty,
            context_text=context_text,
            content=content
        )

        self.db.add(new_record)
        await self.db.commit()
        await self.db.refresh(new_record)  # ca să ai id-ul generat

        return new_record

    # --- LOGICA DE CACHE ---
    async def get_cached_response(self, text_content: str):
        normalized = text_content.strip().lower()
        content_hash = hashlib.sha256(normalized.encode()).hexdigest()
        stmt = select(AICache.cached_response).where(AICache.content_hash == content_hash)
        result = await self.db.execute(stmt)
        return result.scalar()

    async def save_to_cache(self, text_content: str, response_json: dict):
        normalized = text_content.strip().lower()
        content_hash = hashlib.sha256(normalized.encode()).hexdigest()
        # on_conflict_do_nothing previne erorile la generări simultane identice
        stmt = insert(AICache).values(
            content_hash=content_hash,
            cached_response=response_json
        ).on_conflict_do_nothing()
        await self.db.execute(stmt)
        await self.db.commit()
