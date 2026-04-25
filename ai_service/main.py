from fastapi import FastAPI
from ai_service.api.ai_endpoints import router as ai_endpoints_router

app = FastAPI()


@app.get("/")
def root():
    return {"message": "AI Service Running"}

app.include_router(ai_endpoints_router)
