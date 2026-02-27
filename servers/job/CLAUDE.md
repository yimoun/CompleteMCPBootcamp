# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Job Recommender MCP Server — a Python 3.13 application that analyzes resumes (PDF), identifies skill gaps, generates career roadmaps with Mermaid diagrams, and fetches job listings from free APIs (Remotive, Jooble). Runs in two modes: Streamlit web app and MCP server (stdio transport via FastMCP).

## Commands

```bash
# Install dependencies (UV preferred, pip also works)
uv sync
pip install -r requirements.txt

# Run the Streamlit web app (interactive UI)
streamlit run app.py

# Run the MCP server (stdio transport, used by Claude/LLM hosts)
python mcp_server.py

# Docker
docker build -t job-mcp-server .
docker run --rm -e GROQ_API_KEY=... -e JOOBLE_API_KEY=... job-mcp-server
```

No test suite, linter, or type checker is configured.

## Architecture

Two entry points share the same `src/` layer:

```
app.py (Streamlit UI)  ──┐
                          ├──> src/
mcp_server.py (MCP stdio) ┘
```

**`mcp_server.py`** — Exposes 4 FastMCP tools: `fetch_remote`, `extract_profile`, `match_jobs`, `analyze_gaps`. Thin wrappers around `src/ai_tools.py` and `src/job_api.py`.

**`app.py`** — Streamlit app with a sequential pipeline: PDF upload → resume summary → skill gap analysis → career roadmap (text + Mermaid diagram) → job search (keywords extracted by LLM, then fetched from Remotive + Jooble). Uses `st.session_state` for job search persistence across reruns.

### src/ modules

- **`helper.py`** — `extract_text_from_pdf()` (PyMuPDF/fitz) and `ask_groq()` (Groq LLM wrapper with exponential backoff, 3 retries). Default model comes from `GROQ_MODEL` env var.
- **`job_api.py`** — `fetch_remote_jobs()` (Remotive, no auth) and `fetch_jooble_jobs()` (requires `JOOBLE_API_KEY`). Both return `(jobs_list, error_string)` tuples.
- **`ai_tools.py`** — Higher-level AI functions (`extract_resume_profile`, `analyze_career_gaps`, `rank_jobs`, `build_roadmap_mermaid`) that combine prompts + `ask_groq()`.
- **`prompts.py`** — All LLM prompt templates. Mermaid prompts use fixed node IDs (A1–A4, B1–B6, C1–C6) for a 3-phase roadmap (0-3 / 3-6 / 6-12 months).
- **`ui_helpers.py`** — Mermaid diagram utilities: `clean_mermaid_code`, `normalize_mermaid` (fills a template with labels), `build_mermaid_from_labels`, `mermaid_image_url` (zlib-compressed URL for mermaid.ink). Primary rendering uses Kroki.io SVG POST; falls back to mermaid.ink URL.

### Mermaid roadmap flow (the trickiest part)

Labels are first extracted from the textual roadmap via LLM → JSON. If labels are valid (no placeholders), `build_mermaid_from_labels()` constructs the diagram directly. Otherwise, the LLM generates raw Mermaid code, which is cleaned and normalized against the fixed-node template. Debug info is exposed in the Streamlit "Debug Mermaid" expander.

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `GROQ_API_KEY` | Yes | Groq LLM API key |
| `GROQ_MODEL` | No | LLM model (default: `llama-3.3-70b-versatile`) |
| `JOOBLE_API_KEY` | Yes | Jooble job search API key |
| `JOOBLE_DEBUG` | No | Set `1`/`true`/`yes` for verbose Jooble logging |
| `APIFY_API_TOKEN` | No | Apify client (currently unused) |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | No | Adzuna API (currently unused) |

## Conventions

- All LLM calls go through `src/helper.ask_groq()` — never call Groq directly.
- Job API functions return `(list, error_or_None)` tuples; callers check both.
- Mermaid node IDs (A1, B1, C1, etc.) are fixed in the template and prompts — keep them in sync when editing either.
- The project mixes French and English in UI strings and comments.

## Règles Git

- Ne JAMAIS exécuter de commandes git (commit, push, pull, merge) 
  sans ma permission explicite.
- Je suis le seul à gérer les opérations git.
- Tu peux me SUGGÉRER des commandes git, mais ne les exécute pas.


