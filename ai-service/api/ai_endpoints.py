# AI Gateway router
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from services.gen_popquiz import generate_pop_quiz
from services.gen_popquiz_explain import generate_answer_explanations
from services.gen_finaltest import generate_final_mcq_test
from services.gen_finaltest_explain import grade_and_explain_mcq_test
from services.generate_explanation_parapgraphs import generate_paragraph_explanation
from services.reformat_professor import refine_academic_text
from db.database import get_db

router = APIRouter()


class PopQuizRequest(BaseModel):
    lesson_type: str = Field(default="General", description="Topic/category of the lesson")
    lesson_text: str = Field(..., description="Lesson content used to generate the pop quiz")
    difficulty: str = Field(default="easy", description="Quiz difficulty")


class PopQuizExplanationRequest(BaseModel):
    lesson_text: str = Field(..., description="The original text of the lesson")
    quiz_json: str | list[dict[str, Any]] = Field(
        ...,
        description="The quiz JSON returned by the pop quiz generator (array of objects). You may also pass it as a JSON-encoded string for compatibility.",
    )
    user_answers: list[list[str]] = Field(
        ...,
        description='User selected answers per question',
    )


class FinalTestRequest(BaseModel):
    topic_name: str = Field(..., description="The topic name for the final test")
    lesson_text: str = Field(..., description="Lesson content used to generate the final test")
    difficulty: str = Field(default="easy", description="Quiz difficulty")


class FinalTestExplanationRequest(BaseModel):
    lesson_text: str = Field(..., description="The original text of the lesson")
    test_json: str | list[dict[str, Any]] = Field(
        ...,
        description="The final test JSON returned by the generator (array of objects). You may also pass it as a JSON-encoded string for compatibility.",
    )
    user_answers: list[list[str]] = Field(
        ...,
        description='User selected answers per question',
    )


class ParagraphExplanationRequest(BaseModel):
    topic_name: str = Field(..., description="The topic name")
    confusing_paragraph: str = Field(..., description="The paragraph the student struggled with")
    education_level: str = Field(default="Middle School", description="Student education level")


class ProfessorReformatRequest(BaseModel):
    topic_name: str = Field(..., description="Academic domain/topic")
    ambiguous_text: str = Field(..., description="Text to rewrite more clearly and academically")


@router.post("/pop-quiz")
@router.post("/get-pop-quiz", include_in_schema=False, deprecated=True)
def create_pop_quiz(payload: PopQuizRequest):
    quiz_json = generate_pop_quiz(lesson_type=payload.lesson_type, lesson_text=payload.lesson_text, difficulty=payload.difficulty)

    try:
        parsed = json.loads(quiz_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Generator returned invalid JSON") from exc

    if isinstance(parsed, dict) and parsed.get("error"):
        message = str(parsed["error"])
        status_code = 500
        if "api key" in message.lower() or "gemini_api_key" in message.lower() or "google_api_key" in message.lower():
            status_code = 400
        raise HTTPException(status_code=status_code, detail=message)

    return parsed


@router.post("/pop-quiz/explanations")
@router.post("/get-pop-quiz-explanation", include_in_schema=False, deprecated=True)
def create_pop_quiz_explanations(payload: PopQuizExplanationRequest):
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
        raise HTTPException(status_code=500, detail="Generator returned invalid JSON") from exc

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


@router.post("/final-test")
@router.post("/get-final-test", include_in_schema=False, deprecated=True)
def create_final_test(payload: FinalTestRequest):
    test_json = generate_final_mcq_test(topic_name=payload.topic_name, lesson_text=payload.lesson_text, difficulty=payload.difficulty)

    try:
        parsed = json.loads(test_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Generator returned invalid JSON") from exc

    if isinstance(parsed, dict) and parsed.get("error"):
        message = str(parsed["error"])
        status_code = 500
        lowered = message.lower()
        if "api key" in lowered or "gemini_api_key" in lowered or "google_api_key" in lowered:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=message)

    return parsed


@router.post("/final-test/explanations")
@router.post("/get-final-test-explanation", include_in_schema=False, deprecated=True)
def create_final_test_explanations(payload: FinalTestExplanationRequest):
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
        raise HTTPException(status_code=500, detail="Generator returned invalid JSON") from exc

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
@router.post("/get-paragraph-explanation", include_in_schema=False, deprecated=True)
async def create_paragraph_explanation(
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


@router.post("/professor/reformat")
@router.post("/reformat-professor", include_in_schema=False, deprecated=True)
def reformat_professor(payload: ProfessorReformatRequest):
    result_json = refine_academic_text(topic_name=payload.topic_name, ambiguous_text=payload.ambiguous_text)

    try:
        parsed = json.loads(result_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Generator returned invalid JSON") from exc

    if isinstance(parsed, dict) and parsed.get("error"):
        message = str(parsed["error"])
        status_code = 500
        lowered = message.lower()
        if "api key" in lowered or "gemini_api_key" in lowered or "google_api_key" in lowered:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=message)

    return parsed