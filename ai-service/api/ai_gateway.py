# AI Gateway router
from fastapi import APIRouter

router = APIRouter()

@router.get("/getPopQuiz")
def get_pop_quiz():
    return {
        "question": "7 + 5 = ?",
        "options": [10, 11, 12, 13],
        "answer": 12
    }