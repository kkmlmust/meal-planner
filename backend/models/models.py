from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, DateTime, func, JSON, Text, Integer, String, ForeignKey


# ─── Base Models (for requests/responses) — defined FIRST ───

class UserBase(SQLModel):
    telegram_id: str


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    created_at: datetime


class IngredientBase(SQLModel):
    name: str
    quantity: float
    unit: str


class IngredientCreate(IngredientBase):
    pass


class IngredientResponse(IngredientBase):
    id: int
    user_id: int
    added_at: datetime


class RecipeBase(SQLModel):
    title: str
    ingredients: list
    instructions: str
    prep_time: int
    source: str = "user"


class RecipeCreate(RecipeBase):
    pass


class RecipeResponse(RecipeBase):
    id: int
    created_at: datetime


class CookingLogBase(SQLModel):
    recipe_id: int
    notes: Optional[str] = None


class CookingLogCreate(CookingLogBase):
    recipe_title: str


class CookingLogResponse(SQLModel):
    id: int
    user_id: int
    recipe_id: int
    recipe_title: str
    cooked_at: datetime
    notes: Optional[str] = None


# ─── Table Models (database) ───

class UserTable(UserBase, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_id: str = Field(unique=True, index=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    ingredients: List["IngredientTable"] = Relationship(back_populates="user")
    cooking_logs: List["CookingLogTable"] = Relationship(back_populates="user")


class IngredientTable(IngredientBase, table=True):
    __tablename__ = "ingredient"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    quantity: float
    unit: str
    added_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    user: UserTable = Relationship(back_populates="ingredients")


class IngredientCatalog(SQLModel, table=True):
    """Global catalog of ingredient names (normalized)."""
    __tablename__ = "ingredient_catalog"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)


class RecipeTable(RecipeBase, table=True):
    __tablename__ = "recipe"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    ingredients: list = Field(sa_column=Column(JSON))
    instructions: str = Field(sa_column=Column(Text))
    prep_time: int = Field(sa_column=Column(Integer))
    source: str = Field(default="user", sa_column=Column(String))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    cooking_logs: List["CookingLogTable"] = Relationship(back_populates="recipe")


class CookingLogTable(CookingLogBase, table=True):
    __tablename__ = "cooking_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    recipe_id: int = Field(foreign_key="recipe.id")
    cooked_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))

    user: UserTable = Relationship(back_populates="cooking_logs")
    recipe: RecipeTable = Relationship(back_populates="cooking_logs")
