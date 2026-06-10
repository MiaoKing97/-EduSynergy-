# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EduSynergy (杏坛智析) is a full-stack AI education platform. The frontend is Vue 3 + Vite + Vue Router with ECharts/Mermaid renderers; the backend is an async FastAPI service that integrates SQLite auth, Feishu Bitable homework workflows, LLM APIs (Doubao/DeepSeek-compatible chat completions), local ChromaDB RAG, PDF/tabular parsing, and Playwright screenshots.

## Common Commands

### Backend

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend environment is read from `backend/.env`. Common keys from the README/code are:

```env
FEISHU_APP_ID=...
FEISHU_APP_SECRET=...
OPENAI_API_KEY=...
CHROMA_PERSIST_DIRECTORY=./chroma_data
JWT_SECRET_KEY=...
```

`JWT_SECRET_KEY` should be explicitly set outside local demo use. The backend seeds a default admin account (`admin` / `123`) on first startup.

### Frontend

```bash
cd frontend
npm install
npm run dev      # Vite dev server on localhost:5173; proxies /api to localhost:8000
npm run build    # production build to frontend/dist
```

### One-click local startup

```bash
./start_mac.sh          # macOS/Linux shell startup
start_windows.bat       # Windows startup
```

Both scripts install dependencies, start the backend on port 8000 and the frontend on port 5173, then open the browser.

### Tests and linting

No project test runner, lint command, pytest config, ESLint config, or Vitest config is currently defined in the repository. If tests are added later, document the exact commands here (for example, a single backend test would typically be run from `backend/` with `pytest path/to/test.py::test_name`).

## Architecture

### Backend (`backend/`)

- `main.py` creates the FastAPI app, sets the Windows Proactor event loop policy for Playwright compatibility, initializes the SQLite user store in lifespan startup, cleans up the Playwright browser on shutdown, applies CORS for `http://localhost:5173`, and mounts `/api/auth`, `/api/chat`, and `/api/homework`.
- `app/api/auth.py` exposes login/register/current-user/user-list routes. It uses the auth package for password hashing, SQLite-backed user persistence, and JWT bearer tokens.
- `app/api/chat.py` is the AI chat endpoint. It builds system prompts, handles uploaded images/PDF/tabular files, can ingest PDFs into RAG, can inject Feishu table data as context, and streams LLM output with `StreamingResponse`.
- `app/api/homework.py` owns the Feishu homework workflow: creating Bitable apps/tables, extracting grading templates from images, saving rubric rules, uploading student work, capturing web screenshots/local HTML submissions, fetching workspace data, grading with vision models, dashboard stats, and ChatBI over table data.
- `app/auth/` contains auth models, token helpers, middleware/current-user extraction, and SQLite store logic. Roles include `admin`, `teacher`, `web_teacher`, and `student`.
- `app/services/llm_service.py` wraps async LLM calls through `httpx.AsyncClient`, including text streaming and Doubao vision/multi-image calls.
- `app/services/feishu_service.py` is an async Feishu Bitable client for tenant tokens, app/table/field creation, record CRUD, batch inserts, and Bitable image upload/download.
- `app/services/rag_service.py` persists vectors in ChromaDB. PDF extraction and chunking run off the event loop via `asyncio.to_thread`.
- `app/services/file_parser.py` parses CSV/XLSX content and provides an async wrapper for event-loop safety.
- `app/services/screenshot_service.py` maintains a singleton Playwright Chromium worker (`PersistentBrowser`) and captures responsive PC/mobile screenshots plus DOM text for submitted pages.
- `app/core/prompts.py` centralizes module-specific prompts and strict visualization output formats for Mermaid, ECharts, word clouds, graph JSON, and related markdown fence variants.

### Frontend (`frontend/`)

- `src/main.js` bootstraps Vue with the router.
- `src/router/index.js` defines route-level navigation for login, dashboard, teacher/student homework flows, grading, analytics, grades, table management, and account management. The navigation guard reads `ai_assistant_auth` from localStorage and redirects by role.
- `src/App.vue` provides the main three-panel shell: sidebar navigation, central `<router-view>` workspace wrapped in `<keep-alive>` and transitions, and the right configuration panel.
- `src/store.js` is the global reactive store persisted to localStorage. It exports actions such as `login`, `logout`, and `saveConfig` separately from `globalStore` to avoid reactive proxy issues.
- `src/components/views/` contains the routed screens for AI chat/table creation, teacher template setup, student upload, grading queue, analytics, grade profiles, Feishu table management, login, and account management.
- `src/components/renderers/` contains ECharts/Mermaid/word-cloud/graph renderers used for structured AI outputs.
- `src/utils/aiDataParser.js` extracts structured chart/diagram JSON blocks from streamed AI responses.
- `vite.config.js` pins the dev server to port 5173 and proxies `/api` to the backend at `http://localhost:8000`.

## Cross-cutting Patterns

- Backend route handlers and service methods are async-first; use `httpx.AsyncClient` for external HTTP from async contexts.
- LLM responses stream to the frontend as SSE-style chunks; frontend code appends tokens incrementally and then parses visualization blocks.
- Authenticated frontend calls should include `Authorization: Bearer ${globalStore.auth.token}` when calling protected backend routes.
- Feishu App ID/Secret and model API keys are user-configurable from the frontend and/or environment; many homework routes expect these credentials in request payloads.
- The homework status flow is: submission upload/capture → `待批改` → AI grading → `已批改` plus result records.
- `homework.py` includes self-healing table helpers such as `get_or_create_submit_table()` for the "作业提交看板" table.
- Do not create a new Playwright browser per request; reuse `PersistentBrowser.get()` / `capture_responsive_screenshots()` and let FastAPI lifespan cleanup close it.
- When editing prompts, preserve the strict output contracts in `prompts.py` (Mermaid node ID rules, ECharts JSON shape, and fence names like `json_wordcloud`, `json_graph`, `json_array`).

## Repository Notes

- No Cursor rules (`.cursor/rules/` or `.cursorrules`) or Copilot instructions (`.github/copilot-instructions.md`) are present.
- Generated/runtime data exists in places such as `frontend/dist/`, `frontend/node_modules/`, `backend/chroma_data/`, `backend/data/`, `__pycache__/`, and `.venv/`; avoid treating these as source when analyzing or editing.
