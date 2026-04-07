from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from models.models import UserTable, IngredientTable, RecipeTable, CookingLogTable, IngredientCatalog
from datetime import datetime, timedelta


# ─── User CRUD ───

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: str) -> Optional[UserTable]:
    stmt = select(UserTable).where(UserTable.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def create_user(session: AsyncSession, telegram_id: str) -> UserTable:
    user = UserTable(telegram_id=telegram_id)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_user(session: AsyncSession, telegram_id: str) -> UserTable:
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        user = await create_user(session, telegram_id)
    return user


# ─── Ingredient CRUD ───

async def get_user_ingredients(session: AsyncSession, telegram_id: str) -> list[IngredientTable]:
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return []
    stmt = select(IngredientTable).where(IngredientTable.user_id == user.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def add_ingredient(
    session: AsyncSession, telegram_id: str, name: str, quantity: float, unit: str
) -> IngredientTable:
    user = await get_or_create_user(session, telegram_id)
    ingredient = IngredientTable(
        user_id=user.id, name=name, quantity=quantity, unit=unit
    )
    session.add(ingredient)
    await session.commit()
    await session.refresh(ingredient)
    return ingredient


async def remove_ingredient(session: AsyncSession, telegram_id: str, ingredient_id: int) -> bool:
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return False
    stmt = select(IngredientTable).where(
        IngredientTable.id == ingredient_id,
        IngredientTable.user_id == user.id,
    )
    result = await session.execute(stmt)
    ingredient = result.scalars().first()
    if not ingredient:
        return False
    await session.delete(ingredient)
    await session.commit()
    return True


# ─── Ingredient Catalog (global, populated when recipes are saved) ───

async def get_or_create_ingredient(session: AsyncSession, name: str) -> IngredientCatalog:
    """Get or create an ingredient in the global catalog (case-insensitive)."""
    normalized = name.lower().strip()
    stmt = select(IngredientCatalog).where(IngredientCatalog.name == normalized)
    result = await session.execute(stmt)
    existing = result.scalars().first()
    if existing:
        return existing
    catalog_item = IngredientCatalog(name=normalized)
    session.add(catalog_item)
    await session.commit()
    await session.refresh(catalog_item)
    return catalog_item


# ─── Recipe CRUD ───

async def get_recipe_by_title(session: AsyncSession, title: str) -> Optional[RecipeTable]:
    stmt = select(RecipeTable).where(RecipeTable.title == title)
    result = await session.execute(stmt)
    return result.scalars().first()


async def create_recipe(
    session: AsyncSession,
    title: str,
    ingredients: list,
    instructions: str,
    prep_time: int,
    source: str = "user",
) -> RecipeTable:
    recipe = RecipeTable(
        title=title,
        ingredients=ingredients,
        instructions=instructions,
        prep_time=prep_time,
        source=source,
    )
    session.add(recipe)
    await session.flush()

    # Populate ingredient catalog
    for ing_name in ingredients:
        await get_or_create_ingredient(session, ing_name)

    await session.commit()
    await session.refresh(recipe)
    return recipe


async def get_all_recipes(session: AsyncSession) -> list[RecipeTable]:
    stmt = select(RecipeTable)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_recipes_by_ingredients(session: AsyncSession, ingredient_names: list[str]) -> list[RecipeTable]:
    """Find recipes that can be made with the given ingredients.

    Uses the ingredient_catalog table for matching.
    A recipe matches if ALL its required ingredients are in the user's list.
    """
    user_ingredients = {name.lower().strip() for name in ingredient_names}

    stmt = select(RecipeTable)
    result = await session.execute(stmt)
    all_recipes = list(result.scalars().all())

    matching_recipes = []
    for recipe in all_recipes:
        recipe_ingredients = {ing.lower().strip() for ing in recipe.ingredients}

        if recipe_ingredients and recipe_ingredients.issubset(user_ingredients):
            matching_recipes.append(recipe)

    return matching_recipes


# ─── Cooking Log CRUD ───

async def log_cooking(
    session: AsyncSession,
    telegram_id: str,
    recipe_id: int,
    notes: Optional[str] = None,
) -> CookingLogTable:
    user = await get_or_create_user(session, telegram_id)
    log = CookingLogTable(
        user_id=user.id,
        recipe_id=recipe_id,
        notes=notes,
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


async def log_cooking_by_title(
    session: AsyncSession,
    telegram_id: str,
    recipe_title: str,
    notes: Optional[str] = None,
) -> CookingLogTable:
    """Log cooking, creating the recipe if it doesn't exist."""
    user = await get_or_create_user(session, telegram_id)

    recipe = await get_recipe_by_title(session, recipe_title)
    if not recipe:
        recipe = await create_recipe(
            session,
            title=recipe_title,
            ingredients=[],
            instructions="",
            prep_time=0,
            source="user",
        )

    log = CookingLogTable(
        user_id=user.id,
        recipe_id=recipe.id,
        notes=notes,
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


async def get_cooking_history(
    session: AsyncSession, telegram_id: str, days: int = 7
) -> list[dict]:
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return []

    cutoff = datetime.now() - timedelta(days=days)
    stmt = (
        select(CookingLogTable)
        .where(
            CookingLogTable.user_id == user.id,
            CookingLogTable.cooked_at >= cutoff,
        )
        .order_by(CookingLogTable.cooked_at.desc())
    )
    result = await session.execute(stmt)
    logs = list(result.scalars().all())

    # Enrich with recipe title
    enriched_logs = []
    for log in logs:
        recipe_stmt = select(RecipeTable).where(RecipeTable.id == log.recipe_id)
        recipe_result = await session.execute(recipe_stmt)
        recipe = recipe_result.scalars().first()
        title = recipe.title if recipe else "Unknown"
        enriched_logs.append({
            "id": log.id,
            "user_id": log.user_id,
            "recipe_id": log.recipe_id,
            "recipe_title": title,
            "cooked_at": log.cooked_at,
            "notes": log.notes,
        })

    return enriched_logs


async def clear_cooking_history(session: AsyncSession, telegram_id: str) -> bool:
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return False
    stmt = select(CookingLogTable).where(CookingLogTable.user_id == user.id)
    result = await session.execute(stmt)
    logs = list(result.scalars().all())
    for log in logs:
        await session.delete(log)
    await session.commit()
    return True


async def delete_cooking_log(session: AsyncSession, telegram_id: str, log_id: int) -> bool:
    """Delete a single cooking log entry by ID."""
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return False
    stmt = select(CookingLogTable).where(
        CookingLogTable.id == log_id,
        CookingLogTable.user_id == user.id,
    )
    result = await session.execute(stmt)
    log = result.scalars().first()
    if not log:
        return False
    await session.delete(log)
    await session.commit()
    return True


async def clear_user_ingredients(session: AsyncSession, telegram_id: str) -> bool:
    """Delete all ingredients for a user."""
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return False
    stmt = select(IngredientTable).where(IngredientTable.user_id == user.id)
    result = await session.execute(stmt)
    ingredients = list(result.scalars().all())
    for ing in ingredients:
        await session.delete(ing)
    await session.commit()
    return True
