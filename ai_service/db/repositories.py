from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update, func
import hashlib
from uuid import UUID

# Importă modelele tale
from .database import AICache, StudentProfile, StudentMastery, AIRecord

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

    # --- LOGICA DE MASTERY ---
    async def get_student_context(self, user_id: UUID):
        # dacă vine ca string din API, îl convertim
        if isinstance(user_id, str):
            user_id = UUID(user_id)
    
        mastery_stmt = select(StudentMastery.topic_name).where(
            StudentMastery.user_id == user_id,
            StudentMastery.mastery_score < 0.5
        )
    
        mastery_res = await self.db.execute(mastery_stmt)
    
        return {
            "weak_topics": mastery_res.scalars().all()
        }

    async def update_student_performance(self, user_id: UUID, topic: str, score_change : float, wrong_answers : int):
        """Updatează scorul folosind logica de Upsert (PostgreSQL specific)"""

        if isinstance(user_id, str):
            user_id = UUID(user_id)

        # PostgreSQL ON CONFLICT (user_id, topic_name) DO UPDATE
        stmt = insert(StudentMastery).values(
            user_id=user_id,
            topic_name=topic,
            mastery_score=max(0, score_change), # Start de la 0.1 sau 0
            wrong_answers_count=wrong_answers
        ).on_conflict_do_update(
            index_elements=['user_id', 'topic_name'],
            set_={
                "mastery_score": func.greatest(0, func.least(1, StudentMastery.mastery_score + score_change)),
                "wrong_answers_count": StudentMastery.wrong_answers_count + wrong_answers,
                "last_practiced": func.now()
            }
        )
        
        await self.db.execute(stmt)
        await self.db.commit()
