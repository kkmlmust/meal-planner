from fastapi import FastAPI
from contextlib import asynccontextmanager

from config import settings
from db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Recipe Tracker API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "recipe-tracker-api"}


# Import routers after app is created to avoid circular imports
from routers import ingredients, recipes, cooking_log

app.include_router(ingredients.router)
app.include_router(recipes.router)
app.include_router(cooking_log.router)
