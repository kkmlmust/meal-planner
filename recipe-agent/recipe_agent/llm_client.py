from openai import AsyncOpenAI
from recipe_agent.config import settings
import json


class LLMClient:
    """Async OpenAI-compatible LLM client."""

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )
        self.model = settings.llm_model

    async def chat_completion(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        """Get a chat completion from the LLM."""
        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message

    def format_tools_for_openai(self, tools: list) -> list[dict]:
        """Convert MCP tool definitions to OpenAI function calling format."""
        openai_tools = []
        for tool in tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            }
            # Parse input schema if available
            if hasattr(tool, "inputSchema") and tool.inputSchema:
                schema = tool.inputSchema
                openai_tool["function"]["parameters"] = {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", []),
                }
            openai_tools.append(openai_tool)
        return openai_tools


llm_client = LLMClient()
