# pfrecipes — Plan

## Context

An AI-powered CLI tool that turns a personal recipe collection into a searchable knowledge base. Import recipes from any source — markdown files, PDFs, text, bookmarked links — and ask natural language questions like "what can I make with chicken thighs and gochujang," "give me a quick weeknight noodle dish," or "which of my recipes are vegetarian and serve 4+." Answers are grounded in your actual saved recipes, not generic internet results.

Recipes live as documents (markdown, PDF, text, URLs), indexed into a local ChromaDB vector store. Primary interface is an interactive chat CLI with conversation memory. An MCP server is also provided so any MCP-compatible AI assistant can query the knowledge base as a tool.

## Architecture

```
recipes/              <- raw recipe files (md, txt, pdf, urls)
  |
  v
[Loaders]             <- per-format document loaders
  |
  v
[Splitter]            <- RecursiveCharacterTextSplitter (1500/200)
  |
  v
[ChromaDB]            <- local vector store (OpenAI embeddings)
  |
  v
[RAG Chain]           <- similarity search → LLM generation
  |
  v
[CLI chat] + [MCP Server]  <- user interfaces
```

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11+ |
| Document loaders | LangChain Community (TextLoader, PyPDFLoader, WebBaseLoader) |
| Chunking | LangChain RecursiveCharacterTextSplitter |
| Embeddings | OpenAI text-embedding-3-small (via langchain-openai) |
| Vector DB | ChromaDB (local, persists to `.chroma/`) |
| LLM | OpenAI gpt-4o-mini (via langchain-openai) |
| CLI | Typer |
| Chat input | prompt_toolkit (autocomplete dropdown) |
| MCP Server | FastMCP (mcp Python SDK) |
| Testing | pytest |

Provider and model are configurable via env vars — swap to Ollama or any OpenAI-compatible endpoint without code changes.

## Project Structure

```
pfrecipes/
  src/
    pfrecipes/
      __init__.py
      config.py          # env var loading
      ingest.py          # loading, chunking, embedding, ChromaDB storage
      search.py          # RAG retrieval chain, list, remove
      cli.py             # Typer CLI + interactive chat loop
      mcp_server.py      # MCP tool server (recipe_search, recipe_list)
      loaders/
        __init__.py      # dispatcher: URL vs file extension routing
        markdown.py      # .md loader
        text.py          # .txt loader
        pdf.py           # .pdf loader (suppresses pypdf noise)
        url.py           # URL loader: JSON-LD extraction → raw text fallback
  tests/
    fixtures/            # sample_recipe.md, .txt, .pdf, sample_jsonld.html
    test_loaders.py      # unit: loader parsing and dispatch
    test_ingest.py       # unit: chunking, embeddings (mocked)
    test_search.py       # unit: RAG pipeline (mocked)
    test_mcp_server.py   # unit: MCP tool registration
    test_chat.py         # unit: slash command routing, history growth
    test_quality.py      # integration: retrieval + response quality (needs API key)
  pyproject.toml
  .env.example
  PLAN.md
  README.md
```

## Features

### 1. Ingestion Pipeline
- **File loaders**: markdown, plain text, PDF
- **URL loader**: JSON-LD `@type: Recipe` schema extraction first; falls back to raw text scraping via BeautifulSoup
- **Chunking**: `chunk_size=1500, chunk_overlap=200` — most recipes stay as 1 chunk
- **Metadata**: source path/URL and import date stored alongside each chunk
- **CLI**: `pfrecipes ingest <path-or-url>` — single file, directory scan (`.md/.txt/.pdf`), or URL

### 2. Semantic Search + RAG
- Natural language query → embed → similarity search (top 5 chunks) → LLM answers grounded in retrieved recipes
- System prompt instructs the LLM to cite recipe names and be honest when nothing matches
- **CLI**: `pfrecipes search "<query>"`

### 3. Knowledge Base Management
- `pfrecipes list` — all ingested recipes with a short preview
- `pfrecipes remove <source>` — delete all chunks for a given source

### 4. Interactive Chat (primary interface)
- `pfrecipes chat` — persistent REPL with multi-turn conversation memory (last 10 turns)
- Slash commands: `/ingest`, `/list`, `/remove`, `/help`, `/quit`
- `/` triggers an autocomplete dropdown (prompt_toolkit)
- Everything else → RAG answer
- Answers word-wrapped with margins for readability
- Directory ingestion shows file count and per-file progress (`[1/N] filename → K chunks`)

### 5. MCP Server
- `pfrecipes-mcp` — stdio MCP server exposing `recipe_search` and `recipe_list` tools
- Lets any MCP-compatible AI assistant (e.g., Claude Desktop, Claude Code) query your recipe knowledge base as a tool
- Requires absolute paths in MCP config env vars (`RECIPE_CHROMA_DIR`, `RECIPE_RECIPES_DIR`) since the server is launched from a different working directory

### 6. AI Quality Tests
Three-layer test suite in `tests/test_quality.py` — skipped automatically if `OPENAI_API_KEY` is unset or DB is empty:
- **Retrieval** — asserts the right recipe chunks appear in ChromaDB similarity search results for known queries
- **Golden set** — parametrized query → `must_contain` / `must_not_contain` assertions on real LLM responses
- **Sanity** — response length bounds, no empty answers, conversation memory used in follow-ups

## Deferred

- Web UI
- Event / occasion tagging
- Serving size scaling
- Shopping list generation
- Structured relational DB
- Metadata filters (cuisine, course) at search time

## Verification

```bash
pip install -e ".[dev]"
cp .env.example .env  # add OPENAI_API_KEY
pytest                 # 42 tests pass
pfrecipes ingest recipes/
pfrecipes chat
```
