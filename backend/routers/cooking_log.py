from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from db.session import get_session
from db import crud
from models.models import CookingLogResponse
from routers.auth import verify_api_key

router = APIRouter(tags=["cooking-log"])


class CookingLogRequest(BaseModel):
    recipe_title: str
    notes: Optional[str] = None


class CookingHistoryResponse(BaseModel):
    logs: list[CookingLogResponse]


@router.post("/cooking-log/{telegram_id}", status_code=201)
async def log_cooking(
    telegram_id: str,
    data: CookingLogRequest,
    _api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Log that a user cooked a recipe."""
    log = await crud.log_cooking_by_title(
        session,
        telegram_id=telegram_id,
        recipe_title=data.recipe_title,
        notes=data.notes,
    )
    return {
        "message": f"Logged '{data.recipe_title}'",
        "log_id": log.id,
        "recipe_title": data.recipe_title,
        "cooked_at": log.cooked_at,
    }


@router.get("/cooking-log/{telegram_id}")
async def get_cooking_history(
    telegram_id: str,
    days: int = Query(default=7, ge=1, le=365),
    _api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Get cooking history for the last N days."""
    logs = await crud.get_cooking_history(session, telegram_id, days=days)
    return {"logs": logs, "days": days}


@router.delete("/cooking-log/{telegram_id}")
async def clear_cooking_history(
    telegram_id: str,
    _api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Clear all cooking history for a user."""
    success = await crud.clear_cooking_history(session, telegram_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Cooking history cleared"}


@router.delete("/cooking-log/{telegram_id}/{log_id}")
async def delete_single_cooking_log(
    telegram_id: str,
    log_id: int,
    _api_key: str = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Delete a single cooking log entry by ID."""
    success = await crud.delete_cooking_log(session, telegram_id, log_id)
    if not success:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return {"message": f"Log entry #{log_id} deleted"}
