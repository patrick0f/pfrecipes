# RecipeRAG — Plan

## Context

An AI-powered CLI tool that turns a personal recipe collection into a searchable knowledge base. Import recipes from any source — markdown files, PDFs, text, bookmarked links — and ask natural language questions like "what can I make with chicken thighs and gochujang," "give me a quick weeknight noodle dish," or "which of my recipes are vegetarian and serve 4+." Answers are grounded in your actual saved recipes, not generic internet results.

Recipes live as documents (markdown, PDF, text, URLs), indexed into a local vector DB for semantic search. Primary interface is a CLI with built-in conversational AI. An MCP server is also provided so any MCP-compatible AI assistant can query the knowledge base as a tool.

## Architecture

```
recipes/              <- raw recipe files (md, txt, pdf)
  |
  v
[Ingestion Pipeline]  <- document loaders + chunking
  |
  v
[ChromaDB]            <- local vector store (embeddings)
  |
  v
[RAG Chain]           <- retrieval + LLM generation
  |
  v
[CLI] + [MCP Server]  <- user interfaces
```

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python |
| Orchestration | LangChain (doc loaders, chunking, retrieval chain, provider abstraction) |
| Vector DB | ChromaDB (local, no external service) |
| Embeddings | Provider-agnostic via env vars (OpenAI, Cohere, etc.) |
| LLM | Provider-agnostic via env vars (OpenAI, Anthropic, Ollama, etc.) |
| CLI | Typer |
| MCP Server | MCP Python SDK |
| Testing | pytest |

### Provider Config

Environment variables control which LLM/embedding provider is used:
```
RECIPE_LLM_PROVIDER=openai        # or anthropic, ollama, etc.
RECIPE_LLM_MODEL=gpt-4o-mini
RECIPE_EMBED_PROVIDER=openai
RECIPE_EMBED_MODEL=text-embedding-3-small
OPENAI_API_KEY=...                 # or ANTHROPIC_API_KEY, etc.
```

LangChain handles the provider switching — no custom abstraction needed.

## Project Structure

```
pfrecipes/
  src/
    pfrecipes/
      __init__.py
      config.py          # env var loading, provider config
      ingest.py          # document loading, chunking, embedding
      search.py          # RAG retrieval chain
      cli.py             # Typer CLI entrypoint
      mcp_server.py      # MCP tool server
      loaders/
        __init__.py
        markdown.py      # markdown recipe loader
        pdf.py           # PDF loader
        text.py          # plain text loader
        url.py           # URL scraper (JSON-LD first, raw text fallback)
  recipes/               # default recipe storage directory
  tests/
    test_ingest.py
    test_search.py
    test_loaders.py
  pyproject.toml
  .env.example
  PLAN.md
```

## v1 Features

### 1. Ingestion Pipeline
- **File loaders**: markdown, PDF, plain text
- **URL loader**: attempt JSON-LD recipe schema extraction (most recipe sites embed this), fall back to raw text extraction if not present
- **Chunking**: split recipes into semantically meaningful chunks (LangChain RecursiveCharacterTextSplitter, tuned for recipe-sized docs)
- **Metadata**: store source filename, import date, any extracted tags (course type, cuisine) as ChromaDB metadata
- **CLI command**: `pfrecipes ingest <path-or-url>` — ingests a single file/URL or a directory of files

### 2. Semantic Search + RAG
- **Query**: natural language question goes in, relevant recipe chunks are retrieved from ChromaDB, passed to LLM with a prompt that grounds answers in the retrieved recipes
- **Prompt design**: system prompt instructs the LLM to only answer based on retrieved recipes, cite which recipe(s) it's drawing from, and say "I don't have a recipe for that" when nothing matches
- **CLI command**: `pfrecipes search "what can I make with chicken thighs and gochujang"`
- **Filters** (stretch): filter by metadata (course, cuisine) before semantic search

### 3. MCP Server
- Exposes tools so any MCP-compatible AI assistant can query the recipe knowledge base:
  - `recipe_search(query: str)` — semantic search, returns relevant recipes with context
  - `recipe_list()` — list all ingested recipes (names + metadata)

### 4. CLI Commands (Typer)
- `pfrecipes ingest <path-or-url>` — add recipes to the knowledge base
- `pfrecipes search <query>` — natural language search
- `pfrecipes list` — show all ingested recipes
- `pfrecipes remove <recipe-name>` — remove a recipe from the index

## Deferred (not v1)

- Web UI (read-only browser or Streamlit — add later if wanted)
- Event tagging (e.g., tagging recipes to supper club events)
- Scaling / unit conversion
- Shopping list generation
- Structured relational DB

## Development Phases

### Phase 1: Project Scaffolding
Set up the project skeleton so everything has a place before writing real logic.
- Python project with pyproject.toml (dependencies, entry points)
- Directory structure (src/pfrecipes/, tests/, recipes/)
- config.py — env var loading for LLM/embedding provider settings
- .env.example with all expected variables
- Verify: `pip install -e .` works, `pfrecipes --help` shows a stub CLI

### Phase 2: Document Loaders + Ingestion
Get recipes into ChromaDB. This is the foundation everything else builds on.
- Markdown and plain text loaders
- PDF loader
- URL loader (JSON-LD recipe schema extraction with raw text fallback)
- Chunking strategy (RecursiveCharacterTextSplitter, tuned for recipe docs)
- ChromaDB storage with metadata (source file, import date, extracted tags)
- CLI command: `pfrecipes ingest <path-or-url>`
- Tests: unit tests for each loader, integration test for ingest → ChromaDB round-trip

### Phase 3: Search + RAG
The core feature — ask questions, get answers grounded in your recipes.
- RAG retrieval chain: query → embed → retrieve chunks → LLM generation
- System prompt design (answer only from retrieved recipes, cite sources, admit gaps)
- CLI command: `pfrecipes search <query>`
- CLI commands: `pfrecipes list`, `pfrecipes remove <name>`
- Tests: search returns relevant results, irrelevant queries get "no match" response

### Phase 4: MCP Server
Expose the knowledge base as tools for external AI assistants.
- MCP server with `recipe_search` and `recipe_list` tools
- Test: register with an MCP-compatible assistant, verify tools work

### Phase 5+: TBD
Room for additional phases as needs emerge during development — web UI, event tagging, new loaders, etc.

## Verification

- Ingest a few test recipe markdown files, run `pfrecipes search` queries, verify relevant recipes are returned
- Test URL ingestion on a real recipe site (e.g., seriouseats.com)
- Add MCP server to an AI assistant's config, verify `recipe_search` tool appears and returns results
- Run `pytest` — all tests pass
