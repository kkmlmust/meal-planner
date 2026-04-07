import httpx
from config import settings


class RecipeAPIClient:
    """HTTP client for the Recipe Backend API with Bearer token auth."""

    def __init__(self):
        self.base_url = settings.backend_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {settings.api_key}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=self.headers, **kwargs
            )
            response.raise_for_status()
            return response.json()

    # ─── Ingredients ───

    async def get_ingredients(self, telegram_id: str) -> list[dict]:
        return await self._request("GET", f"/ingredients/{telegram_id}")

    async def add_ingredient(
        self, telegram_id: str, name: str, quantity: float, unit: str
    ) -> dict:
        return await self._request(
            "POST",
            f"/ingredients/{telegram_id}",
            json={"name": name, "quantity": quantity, "unit": unit},
        )

    async def remove_ingredient(self, telegram_id: str, ingredient_id: int) -> dict:
        return await self._request(
            "DELETE", f"/ingredients/{telegram_id}/{ingredient_id}"
        )

    # ─── Recipes ───

    async def suggest_recipes(self, telegram_id: str) -> list[dict]:
        return await self._request(
            "GET", f"/recipes/suggest", params={"telegram_id": telegram_id}
        )

    # ─── Cooking Log ───

    async def log_cooking(
        self, telegram_id: str, recipe_title: str, notes: str | None = None
    ) -> dict:
        return await self._request(
            "POST",
            f"/cooking-log/{telegram_id}",
            json={"recipe_title": recipe_title, "notes": notes},
        )

    async def get_cooking_history(self, telegram_id: str, days: int = 7) -> dict:
        return await self._request(
            "GET", f"/cooking-log/{telegram_id}", params={"days": days}
        )


api_client = RecipeAPIClient()
