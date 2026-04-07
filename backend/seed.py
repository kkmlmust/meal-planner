"""Seed the database with initial recipe data."""
from sqlmodel import SQLModel, Session, select
from sqlalchemy import create_engine
from config import settings
from models.models import RecipeTable, IngredientCatalog


SEED_RECIPES = [
    {
        "title": "Chicken Rice Bowl",
        "ingredients": ["chicken", "rice", "spices"],
        "instructions": "Cook rice. Season and cook chicken with spices. Serve chicken over rice.",
        "prep_time": 20,
        "source": "seed",
    },
    {
        "title": "Tomato Chicken Curry",
        "ingredients": ["chicken", "tomatoes", "onion", "spices"],
        "instructions": "Sauté onion, add chicken, tomatoes, and spices. Simmer until chicken is cooked through.",
        "prep_time": 35,
        "source": "seed",
    },
    {
        "title": "Fried Rice",
        "ingredients": ["rice", "eggs", "vegetables"],
        "instructions": "Cook rice and let it cool. Scramble eggs, add rice and vegetables. Stir-fry on high heat.",
        "prep_time": 15,
        "source": "seed",
    },
    {
        "title": "Pasta Bolognese",
        "ingredients": ["pasta", "ground beef", "tomatoes", "onion", "garlic"],
        "instructions": "Cook pasta. Brown beef with onion and garlic. Add tomatoes and simmer. Serve sauce over pasta.",
        "prep_time": 30,
        "source": "seed",
    },
    {
        "title": "Omelette",
        "ingredients": ["eggs", "cheese", "milk"],
        "instructions": "Beat eggs with milk. Pour into heated pan. Add cheese, fold and cook until set.",
        "prep_time": 10,
        "source": "seed",
    },
    {
        "title": "Caesar Salad",
        "ingredients": ["lettuce", "chicken", "croutons", "parmesan"],
        "instructions": "Grill chicken. Toss lettuce with dressing. Top with chicken, croutons, and parmesan.",
        "prep_time": 15,
        "source": "seed",
    },
    {
        "title": "Vegetable Stir Fry",
        "ingredients": ["rice", "vegetables", "soy sauce", "garlic"],
        "instructions": "Cook rice. Stir-fry vegetables with garlic and soy sauce. Serve over rice.",
        "prep_time": 15,
        "source": "seed",
    },
    {
        "title": "Chicken Tacos",
        "ingredients": ["chicken", "tortillas", "tomatoes", "onion", "spices"],
        "instructions": "Season and grill chicken. Chop and serve in tortillas with tomatoes, onion, and spices.",
        "prep_time": 25,
        "source": "seed",
    },
    {
        "title": "Борщ",
        "ingredients": ["свёкла", "капуста", "картофель", "морковь", "лук", "говядина", "томатная паста"],
        "instructions": "Сварить бульон из говядины. Обжарить свёклу с морковью и луком. Добавить картофель, капусту и зажарку. Варить до готовности.",
        "prep_time": 90,
        "source": "seed",
    },
    {
        "title": "Плов",
        "ingredients": ["рис", "курица", "морковь", "лук", "специи", "чеснок"],
        "instructions": "Обжарить мясо с луком и морковью. Добавить рис и специи. Залить водой, добавить чеснок. Томить на медленном огне до готовности риса.",
        "prep_time": 60,
        "source": "seed",
    },
    {
        "title": "Паста Карбонара",
        "ingredients": ["спагетти", "бекон", "яйца", "пармезан", "чеснок"],
        "instructions": "Отварить пасту. Обжарить бекон с чесноком. Смешать яйца с пармезаном. Соединить пасту с беконом, добавить яичную смесь, быстро перемешать.",
        "prep_time": 25,
        "source": "seed",
    },
]


def _get_or_create_ingredient(session: Session, name: str) -> IngredientCatalog:
    """Get or create ingredient in global catalog."""
    normalized = name.lower().strip()
    stmt = select(IngredientCatalog).where(IngredientCatalog.name == normalized)
    result = session.exec(stmt)
    existing = result.first()
    if existing:
        return existing
    catalog_item = IngredientCatalog(name=normalized)
    session.add(catalog_item)
    session.flush()
    return catalog_item


def seed_db():
    """Create tables and seed recipes using sync engine."""
    sync_engine = create_engine(settings.sync_database_url, echo=False)

    # Create tables
    SQLModel.metadata.create_all(sync_engine)

    with Session(sync_engine) as session:
        for recipe_data in SEED_RECIPES:
            stmt = select(RecipeTable).where(RecipeTable.title == recipe_data["title"])
            result = session.exec(stmt)
            existing = result.first()
            if existing:
                print(f"  ⏭️  Skipping '{recipe_data['title']}' (already exists)")
                continue

            # Populate ingredient catalog
            for ing_name in recipe_data["ingredients"]:
                _get_or_create_ingredient(session, ing_name)
            session.commit()

            recipe = RecipeTable(
                title=recipe_data["title"],
                ingredients=recipe_data["ingredients"],
                instructions=recipe_data["instructions"],
                prep_time=recipe_data["prep_time"],
                source=recipe_data["source"],
            )
            session.add(recipe)
            session.commit()
            print(f"  ✅ Added '{recipe_data['title']}' ({len(recipe_data['ingredients'])} ingredients)")

    print("🌱 Seeding complete!")


if __name__ == "__main__":
    print("🌱 Seeding database with recipes...")
    seed_db()
