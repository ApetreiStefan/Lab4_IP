from fastapi import FastAPI
from api.ai_gateway import router as ai_router

app = FastAPI()

@app.get("/")
def root():
    return {"message": "AI Service Running"}

app.include_router(ai_router)
