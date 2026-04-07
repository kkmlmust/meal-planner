#!/usr/bin/env python3
"""Recipe Agent — AI-powered recipe assistant with MCP tools.

Usage:
    uv run python -m recipe_agent.agent               # Start WebSocket server
    uv run python -m recipe_agent.agent --test "/suggest"  # Test a single message
"""

import argparse
import asyncio
import json
import sys

from recipe_agent.config import settings
from recipe_agent.handler import handle_message


async def test_mode(message: str):
    """Run a single message through the agent and print the response."""
    telegram_id = settings.default_telegram_id
    print(f"🤖 User ({telegram_id}): {message}")
    print("⏳ Thinking...")

    try:
        response = await handle_message(telegram_id, message)
        print(f"\n🤖 Agent:\n{response}")
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


async def websocket_handler(websocket):
    """Handle a WebSocket connection from a client (Telegram bot)."""
    print(f"📡 Client connected: {websocket.remote_address}")
    try:
        async for raw_message in websocket:
            try:
                data = json.loads(raw_message)
                telegram_id = data.get("telegram_id", settings.default_telegram_id)
                user_message = data.get("message", "")

                if not user_message:
                    await websocket.send(json.dumps({
                        "error": "Empty message",
                    }))
                    continue

                # Send thinking indicator
                await websocket.send(json.dumps({
                    "telegram_id": telegram_id,
                    "thinking": True,
                }))

                response = await handle_message(telegram_id, user_message)
                await websocket.send(json.dumps({
                    "telegram_id": telegram_id,
                    "response": response,
                }))
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "error": "Invalid JSON. Expected: {'telegram_id': '...', 'message': '...'}",
                }))
            except Exception as e:
                await websocket.send(json.dumps({
                    "error": str(e),
                }))
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        print("📡 Client disconnected")


async def run_server():
    """Start the WebSocket server."""
    from websockets.asyncio.server import serve

    print(f"🚀 Recipe Agent starting on {settings.host}:{settings.port}")
    print(f"📡 WebSocket: ws://{settings.host}:{settings.port}/ws/chat")

    async with serve(websocket_handler, settings.host, settings.port):
        print("✅ Server is running and waiting for connections...")
        await asyncio.Future()  # Run forever


def main():
    parser = argparse.ArgumentParser(description="Recipe Agent — AI Recipe Assistant")
    parser.add_argument(
        "--test",
        type=str,
        metavar="MESSAGE",
        help="Test mode: process a single message and exit",
    )
    args = parser.parse_args()

    if args.test:
        asyncio.run(test_mode(args.test))
    else:
        asyncio.run(run_server())


if __name__ == "__main__":
    main()
