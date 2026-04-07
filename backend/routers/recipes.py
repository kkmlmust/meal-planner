from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_session
from db import crud
from models.models import RecipeResponse, RecipeCreate, RecipeTable
from routers.auth import verify_api_key

router = APIRouter(tags=["recipes"])


@router.get("/recipes/suggest", response_model=list[RecipeResponse])
async def suggest_recipes(
    telegram_id: str = Query(...),
    _api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Suggest recipes based on user's current ingredients."""
    # Get user's ingredients
    ingredients = await crud.get_user_ingredients(session, telegram_id)
    if not ingredients:
        raise HTTPException(status_code=400, detail="No ingredients found. Add some first!")

    ingredient_names = [ing.name for ing in ingredients]
    matching_recipes = await crud.get_recipes_by_ingredients(session, ingredient_names)
    return matching_recipes


@router.get("/recipes", response_model=list[RecipeResponse])
async def list_all_recipes(
    _api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
):
    """List all available recipes."""
    recipes = await crud.get_all_recipes(session)
    return recipes


@router.post("/recipes", response_model=RecipeResponse, status_code=201)
async def create_recipe(
    data: RecipeCreate,
    _api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Create a new recipe."""
    recipe = await crud.create_recipe(
        session,
        title=data.title,
        ingredients=data.ingredients,
        instructions=data.instructions,
        prep_time=data.prep_time,
        source=data.source,
    )
    return recipe
