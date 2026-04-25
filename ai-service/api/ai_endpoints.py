# AI Gateway router
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from services.gen_popquiz import generate_pop_quiz
from services.gen_popquiz_explain import generate_answer_explanations
from services.gen_finaltest import generate_final_mcq_test
from services.gen_finaltest_explain import grade_and_explain_mcq_test
from services.generate_explanation_parapgraphs import generate_paragraph_explanation
from services.reformat_professor import refine_academic_text
from db.database import get_db, StudentMastery  # Adăugat StudentMastery

router = APIRouter()


class DbPopQuizRequest(BaseModel):
    user_id: str = Field(...,
                         description="ID-ul studentului pentru preluarea mastery score-ului")
    lesson_type: str = Field(
        default="General", description="Topic/category of the lesson")
    lesson_text: str = Field(...,
                             description="Lesson content used to generate the pop quiz")


class PopQuizExplanationRequest(BaseModel):
    lesson_text: str = Field(...,
                             description="The original text of the lesson")
    quiz_json: str | list[dict[str, Any]] = Field(
        ...,
        description="The quiz JSON returned by the pop quiz generator. You may pass it as a JSON string.",
    )
    user_answers: list[list[str]] = Field(
        ...,
        description='User selected answers per question',
    )


class DbFinalTestRequest(BaseModel):
    user_id: str = Field(...,
                         description="ID-ul studentului pentru preluarea mastery score-ului")
    topic_name: str = Field(...,
                            description="The topic name for the final test")
    lesson_text: str = Field(...,
                             description="Lesson content used to generate the final test")


class FinalTestExplanationRequest(BaseModel):
    lesson_text: str = Field(...,
                             description="The original text of the lesson")
    test_json: str | list[dict[str, Any]] = Field(
        ...,
        description="The final test JSON returned by the generator. You may pass it as a JSON string.",
    )
    user_answers: list[list[str]] = Field(
        ...,
        description='User selected answers per question',
    )


class ParagraphExplanationRequest(BaseModel):
    topic_name: str = Field(..., description="The topic name")
    confusing_paragraph: str = Field(...,
                                     description="The paragraph the student struggled with")
    education_level: str = Field(
        default="Middle School", description="Student education level")


class ProfessorReformatRequest(BaseModel):
    topic_name: str = Field(..., description="Academic domain/topic")
    ambiguous_text: str = Field(...,
                                description="Text to rewrite more clearly and academically")


@router.post("/db-pop-quiz")
async def db_pop_quiz(payload: DbPopQuizRequest, db: AsyncSession = Depends(get_db)):

    # 1. Căutăm contextul studentului în Baza de Date
    stmt = select(StudentMastery.mastery_score).where(
        StudentMastery.user_id == payload.user_id,
        StudentMastery.topic_name == payload.lesson_type
    )
    result = await db.execute(stmt)
    # Setăm default la 0.5 dacă studentul/materia nu există
    score = result.scalar_one_or_none() or 0.5

    # 2. Calculăm dificultatea pe baza scorului de mastery
    if score < 0.4:
        calculated_difficulty = "easy"
    elif score < 0.7:
        calculated_difficulty = "medium"
    else:
        calculated_difficulty = "hard"

    # 3. Generăm testul
    quiz_json = generate_pop_quiz(
        lesson_type=payload.lesson_type,
        lesson_text=payload.lesson_text,
        difficulty=calculated_difficulty
    )

    try:
        parsed = json.loads(quiz_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500, detail="Generator returned invalid JSON") from exc

    if isinstance(parsed, dict) and parsed.get("error"):
        message = str(parsed["error"])
        status_code = 500
        if "api key" in message.lower() or "gemini_api_key" in message.lower() or "google_api_key" in message.lower():
            status_code = 400
        raise HTTPException(status_code=status_code, detail=message)

    return parsed


@router.post("/pop-quiz-explanation")
def pop_quiz_explanation(payload: PopQuizExplanationRequest):
    quiz_json_str = (
        json.dumps(payload.quiz_json, ensure_ascii=False)
        if isinstance(payload.quiz_json, list)
        else payload.quiz_json
    )

    explanations_json = generate_answer_explanations(
        lesson_text=payload.lesson_text,
        quiz_json=quiz_json_str,
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
            or "invalid quiz_json" in lowered
            or "mismatch" in lowered
        ):
            status_code = 400
        raise HTTPException(status_code=status_code, detail=message)

    return parsed


@router.post("/db-final-test")
async def db_final_test(payload: DbFinalTestRequest, db: AsyncSession = Depends(get_db)):

    # 1. Căutăm contextul studentului în Baza de Date
    stmt = select(StudentMastery.mastery_score).where(
        StudentMastery.user_id == payload.user_id,
        StudentMastery.topic_name == payload.topic_name
    )
    result = await db.execute(stmt)
    score = result.scalar_one_or_none() or 0.5

    # 2. Calculăm dificultatea
    if score < 0.4:
        calculated_difficulty = "easy"
    elif score < 0.7:
        calculated_difficulty = "medium"
    else:
        calculated_difficulty = "hard"

    # 3. Generăm testul final
    test_json = generate_final_mcq_test(
        topic_name=payload.topic_name,
        lesson_text=payload.lesson_text,
        difficulty=calculated_difficulty
    )

    try:
        parsed = json.loads(test_json)
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


@router.post("/final-test-explanation")
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


@router.post("/paragraph-explanation")
async def paragraph_explanation(
    payload: ParagraphExplanationRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await generate_paragraph_explanation(
        db=db,
        topic_name=payload.topic_name,
        confusing_paragraph=payload.confusing_paragraph,
        education_level=payload.education_level,
    )

    if isinstance(result, dict) and result.get("error"):
        message = result["error"]
        status_code = 500

        if "api key" in message.lower():
            status_code = 400

        raise HTTPException(status_code=status_code, detail=message)

    return result


@router.post("/reformat-professor")
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
