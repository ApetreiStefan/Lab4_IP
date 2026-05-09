from fastapi import FastAPI
from ai_service.api.ai_endpoints import router as ai_endpoints_router

from ai_service.db.database import engine, Base

app = FastAPI()


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
def root():
    return {"message": "AI Service Running"}


app.include_router(ai_endpoints_router)
