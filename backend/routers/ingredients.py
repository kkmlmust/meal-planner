from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_session
from db import crud
from models.models import IngredientResponse, IngredientCreate
from routers.auth import verify_api_key

router = APIRouter(tags=["ingredients"])


@router.get("/ingredients/{telegram_id}", response_model=list[IngredientResponse])
async def list_ingredients(
    telegram_id: str,
    _api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Get all ingredients for a user."""
    ingredients = await crud.get_user_ingredients(session, telegram_id)
    return ingredients


@router.post("/ingredients/{telegram_id}", response_model=IngredientResponse, status_code=201)
async def add_ingredient(
    telegram_id: str,
    data: IngredientCreate,
    _api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Add a new ingredient for a user."""
    ingredient = await crud.add_ingredient(
        session,
        telegram_id=telegram_id,
        name=data.name,
        quantity=data.quantity,
        unit=data.unit,
    )
    return ingredient


@router.delete("/ingredients/{telegram_id}/{ingredient_id}")
async def remove_ingredient(
    telegram_id: str,
    ingredient_id: int,
    _api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Remove an ingredient by ID."""
    success = await crud.remove_ingredient(session, telegram_id, ingredient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return {"message": "Ingredient deleted"}


@router.delete("/ingredients/{telegram_id}")
async def clear_ingredients(
    telegram_id: str,
    _api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Clear all ingredients for a user."""
    success = await crud.clear_user_ingredients(session, telegram_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "All ingredients cleared"}
