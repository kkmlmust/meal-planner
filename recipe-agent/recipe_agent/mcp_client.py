import asyncio
import os
from pathlib import Path
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from recipe_agent.config import settings


# The mcp_recipes package is bundled with the recipe-agent
# Find it relative to this file or as a fallback use the project root
_PACKAGE_DIR = Path(__file__).parent.parent / "mcp_recipes"
if not _PACKAGE_DIR.exists():
    _PACKAGE_DIR = Path(__file__).resolve().parent.parent


class MCPRecipeClient:
    """MCP client that connects to the recipe MCP server via stdio."""

    def __init__(self):
        self._session: ClientSession | None = None
        self._exit_stack = AsyncExitStack()
        self._connected = False

    async def connect(self):
        """Connect to the MCP server."""
        if self._connected:
            return

        # Run from /app so mcp_recipes module is discoverable
        server_params = StdioServerParameters(
            command="/app/.venv/bin/python",
            args=["-m", "mcp_recipes.server"],
            cwd="/app",
        )

        import os
        server_params.env = {
            **os.environ,
            "RECIPE_AGENT_BACKEND_URL": settings.backend_url,
            "RECIPE_API_KEY": settings.backend_api_key,
        }

        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read, write = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self._session.initialize()
        self._connected = True

    async def list_tools(self) -> list:
        """List available MCP tools."""
        await self.connect()
        result = await self._session.list_tools()
        return result.tools

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Call an MCP tool by name with arguments."""
        await self.connect()
        result = await self._session.call_tool(name, arguments)
        # Extract text content from the result
        text_parts = []
        for content in result.content:
            if hasattr(content, "text"):
                text_parts.append(content.text)
            else:
                text_parts.append(str(content))
        return "\n".join(text_parts)

    async def close(self):
        """Close the connection."""
        if self._exit_stack:
            await self._exit_stack.aclose()
        self._connected = False


mcp_client = MCPRecipeClient()
