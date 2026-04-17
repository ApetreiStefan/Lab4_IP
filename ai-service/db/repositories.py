from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update, func
import hashlib

# Importă modelele tale
from .database import AICache, StudentProfile, StudentMastery, AIRecord

class AIRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Salvarea quiz-urilor generate ---
    async def save_ai_record(self, user_id, record_type, subject_tag, difficulty, context_text, content):
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

    # --- LOGICA DE PROFIL & MASTERY ---
    async def get_student_context(self, user_id: str):
        # 1. Obținem profilul
        profile_stmt = select(StudentProfile).where(StudentProfile.user_id == user_id)
        profile_res = await self.db.execute(profile_stmt)
        profile = profile_res.scalar_one_or_none()

        # 2. Obținem punctele slabe
        mastery_stmt = select(StudentMastery.topic_name).where(
            StudentMastery.user_id == user_id,
            StudentMastery.mastery_score < 0.5
        )
        mastery_res = await self.db.execute(mastery_stmt)
        
        return {
            "profile": profile,
            "weak_topics": mastery_res.scalars().all()
        }

    async def update_student_performance(self, user_id: str, topic: str, is_correct: bool):
        """Updatează scorul folosind logica de Upsert (PostgreSQL specific)"""
        score_change = 0.1 if is_correct else -0.1
        wrong_inc = 0 if is_correct else 1

        # PostgreSQL ON CONFLICT (user_id, topic_name) DO UPDATE
        stmt = insert(StudentMastery).values(
            user_id=user_id,
            topic_name=topic,
            mastery_score=max(0, score_change), # Start de la 0.1 sau 0
            wrong_answers_count=wrong_inc
        ).on_conflict_do_update(
            index_elements=['user_id', 'topic_name'],
            set_={
                "mastery_score": func.greatest(0, func.least(1, StudentMastery.mastery_score + score_change)),
                "wrong_answers_count": StudentMastery.wrong_answers_count + wrong_inc,
                "last_practiced": func.now()
            }
        )
        
        await self.db.execute(stmt)
        await self.db.commit()