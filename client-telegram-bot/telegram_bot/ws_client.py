import json
import asyncio
from websockets.asyncio.client import connect
from telegram_bot.config import settings


async def send_message(telegram_id: str, message: str) -> str:
    """Send a message to the agent via WebSocket and get the response.

    Creates a fresh connection per request for reliability.
    """
    payload = json.dumps({
        "telegram_id": str(telegram_id),
        "message": message,
    })

    try:
        async with connect(
            settings.agent_ws_url,
            additional_headers={
                "Authorization": f"Bearer {settings.agent_access_key}",
            },
            ping_interval=15,
            ping_timeout=10,
            close_timeout=10,
        ) as ws:
            await ws.send(payload)

            # Read messages until we get the final response (with timeout)
            while True:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=120)
                except asyncio.TimeoutError:
                    return "⏱️ Sorry, I took too long to respond. Please try again."

                data = json.loads(response)

                if "error" in data:
                    return f"⚠️ Error: {data['error']}"

                if "thinking" in data and data["thinking"]:
                    # Agent is still thinking — continue waiting
                    continue

                if "response" in data:
                    return data["response"]

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        raise
