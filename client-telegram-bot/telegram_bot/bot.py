import asyncio
import json
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram_bot.config import settings
from telegram_bot.ws_client import send_message

HELP_TEXT = """\
🍳 <b>Recipe Tracker Bot — Commands</b>

/add_ingredient — Add a new ingredient to your pantry
/my_ingredients — Show your current ingredients
/suggest — Get AI-powered recipe suggestions based on what you have
/cooked — Log a recipe you just cooked
/history — View your cooking history (last 7 days)
/clear_history — Clear your cooking history
/clear_ingredients — Clear all ingredients from your pantry
/delete_log — Delete a single cooking log entry by ID
/help — Show this help message

💡 <b>Tip:</b> You can also just talk to me naturally! Tell me what ingredients you have or ask for recipe ideas."""

WELCOME_TEXT = """\
👋 Welcome to the <b>Recipe Tracker Bot</b>!

I'm your AI-powered cooking assistant. I can help you:
🥘 Find recipes based on what you have in your fridge
📋 Track your ingredients
📝 Remember what you've cooked

Start by adding some ingredients with /add_ingredient or get instant suggestions with /suggest!

Type /help to see all commands."""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(WELCOME_TEXT, parse_mode="HTML")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(HELP_TEXT, parse_mode="HTML")


async def suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /suggest — get AI recipe suggestions."""
    telegram_id = str(update.effective_user.id)
    await _forward_to_agent(update, context, "/suggest")


async def my_ingredients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /my_ingredients."""
    telegram_id = str(update.effective_user.id)
    await _forward_to_agent(update, context, "Show me my current ingredients list")


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /history."""
    telegram_id = str(update.effective_user.id)
    await _forward_to_agent(update, context, "Show my cooking history for the last 7 days")


async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear_history."""
    telegram_id = str(update.effective_user.id)
    await _forward_to_agent(update, context, "Clear my cooking history")


async def clear_ingredients_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear_ingredients."""
    telegram_id = str(update.effective_user.id)
    await _forward_to_agent(update, context, "Clear all my ingredients")


async def delete_log_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delete_log — delete a single cooking log by ID."""
    if not context.args:
        await update.message.reply_text(
            "🗑️ Provide the log ID to delete.\n\n"
            "Usage: `/delete_log 12`\n\n"
            "Find the ID with `/history` — it shows as `#12 Recipe Name`.",
            parse_mode="Markdown",
        )
        return
    try:
        log_id = int(context.args[0])
        await _forward_to_agent(update, context, f"Delete cooking log #{log_id}")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid log ID. Please provide a number, e.g.: `/delete_log 12`",
            parse_mode="Markdown",
        )


async def add_ingredient_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add_ingredient — start interactive mode."""
    await update.message.reply_text(
        "🥕 What ingredient do you want to add?\n\n"
        "Reply with the ingredient name, quantity, and unit.\n"
        'Example: `chicken 500 g` or `eggs 6 pcs`',
        parse_mode="HTML",
    )
    context.user_data["waiting_for_ingredient"] = True


async def cooked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cooked — log a cooked recipe."""
    await update.message.reply_text(
        "🍽️ What did you cook? Reply with the recipe name.\n"
        "You can also add notes, e.g.: `Pasta Bolognese — too salty`",
        parse_mode="HTML",
    )
    context.user_data["waiting_for_cooked"] = True


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages — forward to the AI agent."""
    telegram_id = str(update.effective_user.id)
    text = update.message.text.strip()

    # Check if we're in interactive mode (waiting for ingredient)
    if context.user_data.get("waiting_for_ingredient"):
        context.user_data["waiting_for_ingredient"] = False
        # Always forward to the agent — it handles parsing of any format
        await _forward_to_agent(update, context, f"Add these ingredients: {text}")
        return

    if context.user_data.get("waiting_for_cooked"):
        context.user_data["waiting_for_cooked"] = False
        await _forward_to_agent(update, context, f"Log cooking: {text}")
        return

    # Normal message — forward to agent
    await _forward_to_agent(update, context, text)


async def _forward_to_agent(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    """Send a message to the recipe agent via WebSocket and reply to the user."""
    telegram_id = str(update.effective_user.id)

    # Send "thinking" message and typing action
    thinking_msg = await update.message.reply_text("💭 _Thinking..._", parse_mode="Markdown")
    await update.message.chat.send_action("typing")

    try:
        response = await send_message(telegram_id, message)

        # Delete thinking message
        try:
            await thinking_msg.delete()
        except Exception:
            pass

        # Telegram has a 4096 char limit
        chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode="Markdown")
    except Exception as e:
        # Delete thinking message on error too
        try:
            await thinking_msg.delete()
        except Exception:
            pass
        await update.message.reply_text(
            "⏱️ I'm taking too long to respond. Please try again or rephrase your request."
        )


def main():
    """Start the Telegram bot."""
    app = ApplicationBuilder().token(settings.bot_token).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("suggest", suggest))
    app.add_handler(CommandHandler("my_ingredients", my_ingredients))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("clear_history", clear_history))
    app.add_handler(CommandHandler("clear_ingredients", clear_ingredients_cmd))
    app.add_handler(CommandHandler("delete_log", delete_log_cmd))
    app.add_handler(CommandHandler("add_ingredient", add_ingredient_cmd))
    app.add_handler(CommandHandler("cooked", cooked))

    # Handle all other text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Set bot commands
    asyncio.get_event_loop().run_until_complete(
        app.bot.set_my_commands([
            BotCommand("start", "Welcome & instructions"),
            BotCommand("add_ingredient", "Add an ingredient to your pantry"),
            BotCommand("my_ingredients", "Show your current ingredients"),
            BotCommand("suggest", "Get AI-powered recipe suggestions"),
            BotCommand("cooked", "Log a recipe you cooked"),
            BotCommand("history", "View cooking history (7 days)"),
            BotCommand("clear_history", "Clear all cooking history"),
            BotCommand("clear_ingredients", "Clear all ingredients from pantry"),
            BotCommand("delete_log", "Delete a single cooking log entry"),
            BotCommand("help", "Show all commands"),
        ])
    )

    print("🤖 Telegram bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
