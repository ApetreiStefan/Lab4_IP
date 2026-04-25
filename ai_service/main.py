from fastapi import FastAPI
from ai_service.api.endpoints import router as ai_gateway_router

app = FastAPI()


@app.get("/")
def root():
    return {"message": "AI Service Running"}


app.include_router(ai_gateway_router)
