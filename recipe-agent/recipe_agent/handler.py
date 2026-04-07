import json
from pathlib import Path
from recipe_agent.mcp_client import mcp_client
from recipe_agent.llm_client import llm_client
from recipe_agent.config import settings

SYSTEM_PROMPT = Path(__file__).parent / "system_prompt.txt"
_system_prompt_text = SYSTEM_PROMPT.read_text().strip()

# Conversation state per user (telegram_id -> messages list)
_conversations: dict[str, list[dict]] = {}


def _get_messages(telegram_id: str) -> list[dict]:
    if telegram_id not in _conversations:
        _conversations[telegram_id] = [
            {"role": "system", "content": _system_prompt_text}
        ]
    return _conversations[telegram_id]


async def handle_message(telegram_id: str, user_message: str) -> str:
    """Process a user message through the LLM + MCP tool loop.

    This is the core handler — tested via --test mode, WebSocket, or Telegram.
    """
    # Ensure MCP connection
    await mcp_client.connect()

    # Get conversation history
    messages = _get_messages(telegram_id)
    messages.append({"role": "user", "content": user_message})

    # Get available tools
    tools = await mcp_client.list_tools()
    openai_tools = llm_client.format_tools_for_openai(tools)

    max_tool_rounds = 5  # Prevent infinite loops

    for _ in range(max_tool_rounds):
        # Call LLM
        response = await llm_client.chat_completion(
            messages=messages,
            tools=openai_tools,
        )

        # If no tool calls, return the text response
        if not response.tool_calls:
            messages.append({"role": "assistant", "content": response.content or ""})
            return response.content or "I'm not sure how to help with that. Try asking about recipes or ingredients!"

        # Execute tool calls
        assistant_msg = {
            "role": "assistant",
            "content": response.content,
            "tool_calls": [],
        }
        tool_messages = []

        for tool_call in response.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

            # Inject telegram_id if not provided
            if "telegram_id" not in fn_args:
                fn_args["telegram_id"] = telegram_id

            try:
                result = await mcp_client.call_tool(fn_name, fn_args)
            except Exception as e:
                result = f"Error calling tool '{fn_name}': {e}"

            assistant_msg["tool_calls"].append({
                "id": tool_call.id,
                "type": "function",
                "function": {"name": fn_name, "arguments": tool_call.function.arguments},
            })
            tool_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

        messages.append(assistant_msg)
        messages.extend(tool_messages)

    # Final response
    final_response = await llm_client.chat_completion(messages=messages)
    return final_response.content or "I processed your request. Is there anything else I can help with?"


def reset_conversation(telegram_id: str):
    """Reset conversation history for a user."""
    if telegram_id in _conversations:
        del _conversations[telegram_id]
