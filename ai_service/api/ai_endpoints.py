import json
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union
import inspect
from ai_service.services.gen_popquiz import generate_pop_quiz
from ai_service.services.gen_popquiz_explain import generate_answer_explanations
from ai_service.services.gen_finaltest import generate_final_mcq_test
from ai_service.services.gen_finaltest_explain import grade_and_explain_mcq_test
from ai_service.services.generate_explanation_parapgraphs import generate_paragraph_explanation
from ai_service.services.reformat_professor import refine_academic_text
from ai_service.db.database import get_db
from ai_service.db.repositories import AIRepository

router = APIRouter()


# --- Modele Pydantic ---

class PopQuizRequest(BaseModel):
    user_id: UUID = Field(..., description="UUID-ul utilizatorului")
    lesson_type: str = Field(default="General", description="Topic/category of the lesson")
    lesson_text: str = Field(..., description="Lesson content used to generate the pop quiz")
    difficulty: str = Field(default="easy", description="Quiz difficulty: easy|medium|hard")


class FinalTestRequest(BaseModel):
    user_id: UUID = Field(..., description="UUID-ul utilizatorului")
    topic_name: str = Field(..., description="The topic name for the final test")
    lesson_text: str = Field(..., description="Lesson content used to generate the final test")
    difficulty: str = Field(default="easy", description="Test difficulty: easy|medium|hard")


class FinalTestExplanationRequest(BaseModel):
    test_json: Union[list, str] = Field(..., description="Test JSON")
    lesson_text: str = Field(..., description="Lesson content")
    user_answers: dict = Field(..., description="User answers for grading")


class ParagraphExplanationRequest(BaseModel):
    topic_name: str = Field(..., description="Topic name")
    confusing_paragraph: str = Field(..., description="The confusing paragraph")
    education_level: str = Field(default="high_school", description="Education level")


class ProfessorReformatRequest(BaseModel):
    topic_name: str = Field(..., description="Topic name")
    ambiguous_text: str = Field(..., description="Ambiguous text to refine")


# --- Rute API ---

@router.post("/v1/pop-quiz")
async def get_pop_quiz(payload: PopQuizRequest, db: AsyncSession = Depends(get_db)):
    repo = AIRepository(db)

    # 1. Verificăm Cache
    cached = await repo.get_cached_response(payload.lesson_text)
    if cached:
        return cached

    # 2. Generăm cu AI
    quiz_json = generate_pop_quiz(
        lesson_type=payload.lesson_type,
        lesson_text=payload.lesson_text,
        difficulty=payload.difficulty
    )

    try:
        parsed = json.loads(quiz_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Generator returned invalid JSON") from exc

    if isinstance(parsed, dict) and parsed.get("error"):
        raise HTTPException(status_code=400, detail=parsed["error"])

    # 3. Salvăm în Cache și Istoric
    await repo.save_to_cache(payload.lesson_text, parsed)
    await repo.save_ai_record(
        user_id=payload.user_id,
        record_type="pop_quiz",
        subject_tag=payload.lesson_type,
        difficulty=payload.difficulty,
        context_text=payload.lesson_text[:200],  # Salvăm doar un snippet
        content=parsed
    )

    return parsed


@router.post("/v1/final-test")
async def get_final_test(payload: FinalTestRequest, db: AsyncSession = Depends(get_db)):
    repo = AIRepository(db)

    cached = await repo.get_cached_response(payload.lesson_text)
    if cached:
        return cached

    test_json = generate_final_mcq_test(
        topic_name=payload.topic_name,
        lesson_text=payload.lesson_text,
        difficulty=payload.difficulty
    )

    try:
        parsed = json.loads(test_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Generator returned invalid JSON") from exc

    if isinstance(parsed, dict) and parsed.get("error"):
        raise HTTPException(status_code=400, detail=parsed["error"])

    await repo.save_to_cache(payload.lesson_text, parsed)
    await repo.save_ai_record(
        user_id=payload.user_id,
        record_type="final_test",
        subject_tag=payload.topic_name,
        difficulty=payload.difficulty,
        context_text=payload.lesson_text[:200],
        content=parsed
    )

    return parsed


@router.post("/v1/final-test-explanation")
def final_test_explanation(payload: FinalTestExplanationRequest):
    test_json_str = (
        json.dumps(payload.test_json, ensure_ascii=False)
        if isinstance(payload.test_json, list)
        else payload.test_json
    )

    explanations_json = grade_and_explain_mcq_test(
        lesson_text=payload.lesson_text,
        test_json=test_json_str,
        user_answers=payload.user_answers,
    )

    try:
        parsed = json.loads(explanations_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500, detail="Generator returned invalid JSON") from exc

    if isinstance(parsed, dict) and parsed.get("error"):
        message = str(parsed["error"])
        status_code = 500
        lowered = message.lower()
        if (
                "api key" in lowered
                or "gemini_api_key" in lowered
                or "google_api_key" in lowered
                or "invalid test_json" in lowered
                or "mismatch" in lowered
        ):
            status_code = 400
        raise HTTPException(status_code=status_code, detail=message)

    return parsed


@router.post("/v1/paragraph-explanation")
async def paragraph_explanation(
        payload: ParagraphExplanationRequest,
        db: AsyncSession = Depends(get_db)
):
    maybe_awaitable = generate_paragraph_explanation(
        db=db,
        topic_name=payload.topic_name,
        confusing_paragraph=payload.confusing_paragraph,
        education_level=payload.education_level,
    )

    result = await maybe_awaitable if inspect.isawaitable(maybe_awaitable) else maybe_awaitable

    if isinstance(result, dict) and result.get("error"):
        message = result["error"]
        status_code = 500

        if "api key" in message.lower():
            status_code = 400

        raise HTTPException(status_code=status_code, detail=message)

    return result


@router.post("/v1/reformat-professor")
def reformat_professor(payload: ProfessorReformatRequest):
    result_json = refine_academic_text(
        topic_name=payload.topic_name, ambiguous_text=payload.ambiguous_text)

    try:
        parsed = json.loads(result_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500, detail="Generator returned invalid JSON") from exc

    if isinstance(parsed, dict) and parsed.get("error"):
        message = str(parsed["error"])
        status_code = 500
        lowered = message.lower()
        if "api key" in lowered or "gemini_api_key" in lowered or "google_api_key" in lowered:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=message)

    return parsed
