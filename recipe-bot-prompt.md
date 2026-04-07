# Prompt: Recipe Tracker Telegram Bot with AI Suggestions

## Context

Build a Telegram bot application that tracks what users cook and uses an **LLM agent** (like the nanobot + qwen-code-api pattern in this project) to suggest recipes based on available ingredients. The application follows the exact architecture of SE Toolkit Lab 8.

> **Lab 9 Hackathon constraints apply:** This project is built as part of Lab 9. See the "Lab 9 Hackathon Mandatory Requirements" section below.

---

## Lab 9 Hackathon Mandatory Requirements

### Project must have these components (each fulfilling a useful function):
- **Backend** — FastAPI recipe API (this project has it)
- **Database** — PostgreSQL for persistence (this project has it)
- **End-user-facing client** — Telegram bot (this project's primary client)
  > Note: Telegram bots are blocked on Russian/university VMs. For demo on the VM, use the nanobot webchat channel + Flutter web as an alternative transport. The Telegram bot works everywhere else.

### Version 1 (shown to TA during lab):
- One core feature working well — recipe suggestion via LLM + MCP tools
- Functioning product, NOT a prototype
- TA tries it and gives feedback

### Version 2 (by Thursday 23:59):
- Improved functionality or additional feature
- Address TA feedback from the lab
- **Dockerize ALL services**
- **Deploy** and make accessible to use
- Push all code to GitHub repo called **se-toolkit-hackathon**
- Add **MIT license** file

### GitHub README.md must include:
- Product name (as title)
- One-line description
- Demo: a couple of relevant screenshots
- Product context: end users, problem, your solution
- Features: implemented and not yet implemented
- Usage: explain how to use the product
- Deployment: OS assumptions (Ubuntu 24.04), prerequisites, step-by-step instructions

### Task 5 — 5-slide presentation (submitted through Moodle):
1. **Title**: product title, your name, university email, group
2. **Context**: end-user, problem, product idea in one sentence
3. **Implementation**: how you built it, Version 1 vs Version 2, TA feedback points addressed
4. **Demo**: pre-recorded video of Version 2 with voice-over (max 2 minutes) — most important part
5. **Links**: GitHub repo + deployed product (link + QR code for each)

---

## Application Requirements

### Core Features

1. **Cooking History Tracking**: Remember what the user cooked in the last 7 days (stored in PostgreSQL)
2. **AI-Powered Recipe Suggestions**: An LLM agent analyzes available ingredients and suggests recipes the user can make — the same pattern as nanobot calling MCP tools to query the backend
3. **Recipe Selection & Memory**: User selects a recipe from suggestions, it gets saved to their cooking history
4. **Telegram Bot Interface**: Natural language interaction via Telegram, connected through a WebSocket channel (same as nanobot-websocket-channel pattern)

---

## Architecture (following SE Toolkit Lab 8 exactly)

### Component Diagram

```
[User] → [Telegram Bot] → [WebSocket] → [Recipe Agent (nanobot-like)] → [LLM via qwen-code-api]
                                                        |
                                                +-------+-------+
                                                |               |
                                        [Recipe Backend]   [MCP Tools]
                                        (FastAPI API)      (ingredients,
                                                             recipes,
                                                             cooking_log)
                                                |
                                           [PostgreSQL]
```

### Components to Build

#### 1. Telegram Bot (`client-telegram-bot/`)
- Connects to the agent via WebSocket (same pattern as `client-telegram-bot` in this project)
- Sends user messages to the agent, receives responses
- Environment: `BOT_TOKEN`, `NANOBOT_WS_URL`, `NANOBOT_ACCESS_KEY`

#### 2. Recipe Agent (`recipe-agent/`) — like `nanobot/`
- Entry point with `--test` mode for local testing
- MCP client that calls tools on the Recipe Backend
- System prompt that tells the LLM: "You are a recipe assistant. Use the available tools to check ingredients, suggest recipes, and log cooking history."
- Tool descriptions are critical — the LLM reads them to decide which tool to call (same pattern as Lab 8 Task 1 MCP tools)
- Configuration via pydantic-settings from env vars
- Uses `uv` and `pyproject.toml` (NOT pip/requirements.txt)

#### 3. Recipe Backend (`backend/`) — like the LMS FastAPI backend
- **Layered architecture**: `routers/` → `db/` → `models/`
- **Endpoints**:
  - `GET /health` — health check
  - `GET /ingredients/{telegram_id}` — list user's ingredients
  - `POST /ingredients/{telegram_id}` — add ingredients
  - `DELETE /ingredients/{telegram_id}/{ingredient_id}` — remove ingredient
  - `GET /recipes/suggest?telegram_id=...&ingredients=...` — get recipe suggestions (called by LLM via MCP tool)
  - `POST /cooking-log/{telegram_id}` — log a cooked recipe
  - `GET /cooking-log/{telegram_id}?days=7` — get cooking history
- **PostgreSQL schema**:
  - `user` — id, telegram_id (unique), created_at
  - `ingredient` — id, user_id (FK → user), name, quantity, unit, added_at
  - `recipe` — id, title, ingredients (JSONB array), instructions (TEXT), prep_time (INT), source (TEXT), created_at
  - `cooking_log` — id, user_id (FK → user), recipe_id (FK → recipe), cooked_at, notes (TEXT)
- **Bearer token authentication** for all API endpoints
- **async SQLAlchemy** for database operations
- **SQLModel** for schemas (table + request/response variants)

#### 4. MCP Server (`mcp/mcp_recipes/`) — like `mcp/mcp_lms/`
- Stdio MCP server with recipe-specific tools:
  - `get_ingredients(telegram_id)` — returns user's current ingredients
  - `add_ingredient(telegram_id, name, quantity, unit)` — adds an ingredient
  - `remove_ingredient(telegram_id, ingredient_id)` — removes an ingredient
  - `suggest_recipes(telegram_id)` — returns recipes the user can make with current ingredients
  - `log_cooking(telegram_id, recipe_title, notes)` — logs that user cooked something
  - `get_cooking_history(telegram_id, days=7)` — returns recent cooking history
- Each tool calls the Recipe Backend API with Bearer auth
- Tool descriptions must be clear so the LLM knows when to call each one

#### 5. Qwen Code API (`qwen-code-api/`) — reuse from this project
- OpenAI-compatible LLM proxy
- The Recipe Agent sends chat completions here
- Handles auth, retries, token refresh

#### 6. Docker Compose (`docker-compose.yml`)
- Services:
  - `recipe-agent` — the AI agent (like `nanobot`)
  - `backend` — FastAPI Recipe API
  - `postgres` — PostgreSQL database
  - `qwen-code-api` — LLM proxy (reuse from project)
  - `client-telegram-bot` — Telegram bot client
  - `caddy` — reverse proxy (optional)
- Single `recipe-network` for service-to-service communication
- Health checks for all services
- Volumes: `postgres_data` for persistence

---

## Configuration Pattern

### `.env.docker.secret` (gitignored)
```env
# Telegram
BOT_TOKEN=your-telegram-bot-token

# Backend
RECIPE_API_KEY=your-backend-api-key

# Database
POSTGRES_DB=recipe_db
POSTGRES_USER=recipe_user
POSTGRES_PASSWORD=your-postgres-password

# LLM (Qwen Code API)
QWEN_CODE_API_KEY=your-qwen-api-key
QWEN_CODE_API_MODEL=qwen-plus

# Agent
RECIPE_AGENT_ACCESS_KEY=your-agent-access-key
RECIPE_AGENT_LLM_BASE_URL=http://qwen-code-api:8080/v1
RECIPE_AGENT_BACKEND_URL=http://backend:8000

# Telegram client
NANOBOT_WS_URL=ws://recipe-agent:8765/ws/chat
NANOBOT_ACCESS_KEY=your-agent-access-key
```

### Config files use pydantic-settings
```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    api_key: str = Field(..., alias="RECIPE_API_KEY")
    db_host: str = Field(..., alias="DB_HOST")
    db_port: int = Field(..., alias="DB_PORT")
    db_name: str = Field(..., alias="POSTGRES_DB")
    db_user: str = Field(..., alias="POSTGRES_USER")
    db_password: str = Field(..., alias="POSTGRES_PASSWORD")

    model_config = {"env_file": ".env.docker.secret", "populate_by_name": True}
```

---

## Bot Commands

- `/start` — welcome message + explain how it works
- `/add_ingredient` — interactive: "What ingredient do you have?" → saves to DB
- `/my_ingredients` — show current ingredients list
- `/suggest` — **LLM agent analyzes ingredients via MCP tools and suggests recipes**
- `/cooked` — log what you just cooked (or select from recent suggestions)
- `/history` — show cooking history (last 7 days)
- `/clear_history` — clear cooking history
- `/help` — list all commands

---

## AI-Powered Recipe Suggestion Flow (the key feature)

This is the core pattern — same as nanobot using MCP tools to query the LMS:

```
User: /suggest

→ Telegram Bot sends message to Recipe Agent via WebSocket

→ Recipe Agent calls LLM (via qwen-code-api) with system prompt:
  "You are a recipe assistant. You have tools to check ingredients, suggest recipes,
   and log cooking. Use them to help the user."

→ LLM sees the user wants suggestions, decides to call MCP tool:
  suggest_recipes(telegram_id="12345")

→ MCP Server calls backend API:
  GET /recipes/suggest?telegram_id=12345
  Authorization: Bearer <RECIPE_API_KEY>

→ Backend queries database for recipes matching user's ingredients

→ Response flows back: LLM → Agent → WebSocket → Telegram Bot → User

Bot: Based on your ingredients (chicken, rice, tomatoes, onion), you can make:

     🍗 **Chicken Rice Bowl** (20 min)
     Needs: chicken, rice, spices
     You have: ✅ chicken, ✅ rice, ✅ spices

     🍅 **Tomato Chicken Curry** (35 min)
     Needs: chicken, tomatoes, onion, spices
     You have: ✅ chicken, ✅ tomatoes, ✅ onion, ✅ spices

     🍳 **Fried Rice** (15 min)
     Needs: rice, eggs, vegetables
     You have: ✅ rice, ❌ eggs, ❌ vegetables

     Reply with a number to cook it, or tell me what else you have!

User: 2

→ LLM calls MCP tool: log_cooking(telegram_id="12345", recipe_title="Tomato Chicken Curry")

→ Backend saves to cooking_log

Bot: ✅ Logged "Tomato Chicken Curry"!
     Cooked on: 2026-04-06 14:30

     Your recent meals:
     • Tomato Chicken Curry (today)
     • Pasta Bolognese (2 days ago)
     • Omelette (4 days ago)
```

### Why LLM, not hardcoded logic?

The LLM doesn't just match ingredients — it can:
- Explain **why** a recipe works with what you have
- Suggest **substitutions** ("You don't have eggs? Use yogurt instead")
- Answer **follow-up questions** ("How spicy is this?", "Can I make it vegetarian?")
- Handle **natural language** ("I want something quick and warm")
- Remember **context** across the conversation

This is the same reason nanobot uses an LLM instead of regex — the agent **reasons** about tools, it doesn't just route.

---

## Key Patterns to Follow

1. **Handler separation**: Handlers are plain functions — testable via `--test` mode, unit tests, or Telegram
2. **MCP tools**: The LLM calls tools via MCP — tool description quality > prompt engineering
3. **API client + Bearer auth**: Backend calls use Bearer tokens from env vars
4. **Layered architecture**: routers → db layer → models (3 distinct layers)
5. **pydantic-settings config**: All config from env vars with type validation
6. **Docker networking**: Services use service names, not `localhost`
7. **No hardcoded secrets**: All credentials from `.env.docker.secret`
8. **No secrets in git**: `.env.docker.secret` in `.gitignore`
9. **LLM routes via tool descriptions**: Don't use regex/keyword matching to decide which tool to call — let the LLM decide based on tool descriptions
10. **Real fallbacks only**: A fallback is for when the LLM service is unreachable, not for bypassing the LLM for "simple" queries

---

## Deliverables

- [ ] Working Telegram bot that responds to commands
- [ ] Recipe Agent with `--test` mode (e.g., `uv run agent.py --test "/suggest"`)
- [ ] Backend API with CRUD endpoints for ingredients, recipes, cooking logs
- [ ] PostgreSQL schema with proper foreign keys
- [ ] MCP Server with recipe tools (get_ingredients, suggest_recipes, log_cooking, etc.)
- [ ] Docker Compose setup to run everything
- [ ] `.env.docker.example` template for credentials
- [ ] System prompt for the LLM agent
- [ ] Tool descriptions that enable the LLM to make good decisions

---

## What NOT to do

- Don't use `pip` or `requirements.txt` — use `uv` and `pyproject.toml`
- Don't hardcode URLs, API keys, or passwords
- Don't commit `.env.docker.secret`
- Don't skip the `--test` mode — it's essential for development
- Don't use regex or keyword matching to decide which tool to call — if the LLM isn't calling tools correctly, fix the tool descriptions
- Don't build "reliable fallbacks" that handle common queries without the LLM — a real fallback is for when the LLM service is unreachable
- Don't create all files at once — build incrementally, one file at a time
- Don't implement features from later tasks

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent | Python, nanobot framework (or custom agent loop), `uv` |
| Telegram Client | Python, `python-telegram-bot` or `aiogram` |
| Backend | FastAPI, SQLModel, async SQLAlchemy |
| MCP Server | Python, `mcp` SDK |
| Database | PostgreSQL 18 |
| LLM Proxy | qwen-code-api (OpenAI-compatible) |
| Infrastructure | Docker Compose, Caddy (optional) |
| Config | pydantic-settings |

---

## Build Order (incremental, one file at a time)

1. Create `backend/` — FastAPI app with `/health` endpoint only
2. Add `backend/models/` — SQLModel schemas for user, ingredient, recipe, cooking_log
3. Add `backend/db/` — async CRUD operations
4. Add `backend/routers/` — HTTP endpoints for ingredients, recipes, cooking logs
5. Create `mcp/mcp_recipes/` — MCP server with recipe tools
6. Create `recipe-agent/` — agent entry point with `--test` mode, MCP client
7. Write system prompt for the agent
8. Create `client-telegram-bot/` — Telegram bot connecting to agent via WebSocket
9. Create `docker-compose.yml` — wire all services together
10. Create `.env.docker.example` — template for credentials

Each step: create ONE file, STOP, test it, then continue.
