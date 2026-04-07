from mcp.server.fastmcp import FastMCP
from mcp_recipes.api_client import api_client

mcp = FastMCP(
    "recipe-tracker",
    description="MCP server for recipe tracking: manage ingredients, get recipe suggestions, and log cooking history.",
)


@mcp.tool()
async def get_ingredients(telegram_id: str) -> str:
    """Get the list of ingredients currently available for a user.
    Use this when the user asks about their ingredients, or before suggesting recipes.
    Returns a formatted list of ingredients with quantities and units.
    """
    ingredients = await api_client.get_ingredients(telegram_id)
    if not ingredients:
        return "You have no ingredients in your list. Use add_ingredient to add some!"
    lines = [f"• {ing['name']}: {ing['quantity']} {ing['unit']}" for ing in ingredients]
    return "Your current ingredients:\n" + "\n".join(lines)


@mcp.tool()
async def add_ingredient(telegram_id: str, name: str, quantity: float, unit: str) -> str:
    """Add a single ingredient to the user's list.
    Use this when the user tells you they have ONE new ingredient.
    For multiple ingredients sent as a comma-separated list, use add_ingredients instead.
    Parameters:
    - name: the ingredient name (e.g., 'chicken', 'рис', 'томатная паста')
    - quantity: how much (e.g., 500, 2.0, 1)
    - unit: the unit of measurement (e.g., 'g', 'pcs', 'ml', 'cups', 'г', 'кг', 'шт', 'банка', 'пачка')
    Returns confirmation of the added ingredient.
    """
    result = await api_client.add_ingredient(telegram_id, name, quantity, unit)
    return f"✅ Added: {result['name']} — {result['quantity']} {result['unit']}"


@mcp.tool()
async def add_ingredients(telegram_id: str, ingredients: list) -> str:
    """Add multiple ingredients to the user's pantry at once.
    Use this when the user sends a list of ingredients (comma-separated or in any format).
    Each item in the list must be an object with:
    - name: ingredient name (e.g., 'томатная паста', 'макароны', 'сыр')
    - quantity: numeric amount (e.g., 1, 500, 2.5) — use 1 if not specified
    - unit: measurement unit (e.g., 'г', 'кг', 'шт', 'банка', 'пачка', 'мл', 'ч.л.', 'ст.л.', 'cups', 'pcs') — use 'шт' if not specified

    Example ingredients:
    [{"name": "томатная паста", "quantity": 1, "unit": "банка"},
     {"name": "макароны", "quantity": 1, "unit": "пачка"},
     {"name": "филе курицы", "quantity": 1, "unit": "кг"},
     {"name": "сыр", "quantity": 1, "unit": "шт"}]

    Returns a summary of all added items.
    """
    added = []
    errors = []
    for item in ingredients:
        name = item.get("name", "")
        quantity = item.get("quantity", 1)
        unit = item.get("unit", "шт")
        if not name:
            errors.append("Empty ingredient name skipped")
            continue
        try:
            result = await api_client.add_ingredient(telegram_id, name, float(quantity), unit)
            added.append(f"{result['name']} — {result['quantity']} {result['unit']}")
        except Exception as e:
            errors.append(f"Failed to add {name}: {e}")

    lines = [f"✅ Added {len(added)} ingredient(s):"] + [f"• {a}" for a in added]
    if errors:
        lines.append(f"\n⚠️ {len(errors)} error(s):") + [f"• {e}" for e in errors]
    return "\n".join(lines)


@mcp.tool()
async def remove_ingredient(telegram_id: str, ingredient_id: int) -> str:
    """Remove an ingredient by its ID.
    Use this when the user wants to remove a specific ingredient from their list.
    Returns confirmation of removal.
    """
    result = await api_client.remove_ingredient(telegram_id, ingredient_id)
    return result.get("message", "Ingredient removed")


@mcp.tool()
async def suggest_recipes(telegram_id: str) -> str:
    """Suggest recipes that the user can make with their current ingredients.
    Use this when the user asks for recipe suggestions, says '/suggest',
    or wants to know what they can cook.
    This checks the user's ingredients against the recipe database and returns matching recipes.
    Returns a list of recipes with titles, prep times, and required ingredients.
    """
    recipes = await api_client.suggest_recipes(telegram_id)
    if not recipes:
        return (
            "No matching recipes found for your current ingredients. "
            "Try adding more ingredients, or describe what you'd like to cook and I can suggest ideas!"
        )
    lines = []
    for i, recipe in enumerate(recipes, 1):
        ingredients_str = ", ".join(recipe["ingredients"]) if isinstance(recipe["ingredients"], list) else recipe["ingredients"]
        lines.append(
            f"{i}. **{recipe['title']}** ({recipe['prep_time']} min)\n"
            f"   Ingredients: {ingredients_str}"
        )
    return "Here's what you can make:\n\n" + "\n\n".join(lines)


@mcp.tool()
async def log_cooking(telegram_id: str, recipe_title: str, notes: str = "") -> str:
    """Log that the user cooked a recipe.
    Use this when the user confirms they cooked something or wants to save a recipe to their cooking history.
    Parameters:
    - recipe_title: the title of the recipe they cooked
    - notes: optional notes about the cooking experience (e.g., 'too salty', 'family loved it')
    Returns confirmation with the logged recipe and timestamp.
    """
    result = await api_client.log_cooking(telegram_id, recipe_title, notes or None)
    return f"✅ Logged \"{result['recipe_title']}\" on {result['cooked_at']}"


@mcp.tool()
async def get_cooking_history(telegram_id: str, days: int = 7) -> str:
    """Get the user's cooking history for the last N days (default 7).
    Use this when the user asks about their recent meals, cooking history, or says '/history'.
    Returns a list of recently cooked recipes with dates.
    """
    result = await api_client.get_cooking_history(telegram_id, days)
    logs = result.get("logs", [])
    if not logs:
        return f"No cooking history in the last {days} days."
    lines = []
    for log in logs:
        cooked_date = log["cooked_at"][:10] if log["cooked_at"] else "unknown"
        notes_text = f" — {log['notes']}" if log.get("notes") else ""
        lines.append(f"• {log['recipe_title']} ({cooked_date}){notes_text}")
    return f"Your recent meals (last {days} days):\n" + "\n".join(lines)


def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
