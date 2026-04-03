# pfrecipes

An AI-powered personal recipe knowledge base. Import your recipe files and ask natural language questions — answers are grounded in your actual recipes, not the internet.

```
> what can I make with chicken thighs and gochujang?
> do I have any vegetarian pasta dishes?
> give me the fastest weeknight recipe I have
```

## How it works

Recipes are indexed into a local vector database (ChromaDB). When you ask a question, the most relevant recipe chunks are retrieved and passed to an LLM, which answers based only on what you've saved.

```
Your files / URLs
      ↓
  Loaders + Splitter       parse and chunk documents
      ↓
  ChromaDB (local)         store embeddings on disk
      ↓  (at query time)
  Similarity search        retrieve top 5 relevant chunks
      ↓
  LLM (gpt-4o-mini)        answer grounded in your recipes
```

## Setup

**Requirements**: Python 3.11+, an OpenAI API key

```bash
git clone https://github.com/patrick0f/pfrecipes.git
cd pfrecipes
pip install -e .
cp .env.example .env
```

Edit `.env` and add your `OPENAI_API_KEY`.

## Usage

### Interactive chat (recommended)

```bash
pfrecipes chat
```

Type questions naturally. Use `/` commands for direct actions:

| Command | What it does |
|---|---|
| `/ingest <path-or-url>` | Add a recipe file, directory, or URL |
| `/list` | Show all ingested recipes |
| `/remove <source>` | Remove a recipe by its source path or URL |
| `/help` | Show available commands |
| `/quit` | Exit |

The chat loop remembers the last 10 turns — follow-up questions work naturally.

### CLI commands

```bash
pfrecipes ingest recipes/           # ingest a directory
pfrecipes ingest my_recipe.pdf      # ingest a single file
pfrecipes ingest https://...        # ingest a URL

pfrecipes search "chicken thighs"   # one-shot search
pfrecipes list                      # show all recipes
pfrecipes remove my_recipe.pdf      # remove a recipe
```

### MCP server

For use with Claude Desktop or any MCP-compatible AI assistant:

```bash
pfrecipes-mcp
```

Add to your MCP config to expose `recipe_search` and `recipe_list` as tools your AI assistant can call.

## Supported formats

| Format | Notes |
|---|---|
| `.md` | Markdown |
| `.txt` | Plain text |
| `.pdf` | PDF (multi-page) |
| URLs | JSON-LD recipe schema extraction; falls back to raw text |

## Configuration

All settings via environment variables (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Required |
| `RECIPE_LLM_MODEL` | `gpt-4o-mini` | LLM model |
| `RECIPE_EMBED_MODEL` | `text-embedding-3-small` | Embedding model |
| `RECIPE_RECIPES_DIR` | `recipes/` | Default recipe directory |
| `RECIPE_CHROMA_DIR` | `.chroma/` | Vector store location |

To use Ollama locally, install the `ollama` extra (`pip install -e ".[ollama]"`) and set `RECIPE_LLM_PROVIDER=ollama`.

## MCP server setup

To use with Claude Code or Claude Desktop, add to your MCP config:

```json
{
  "mcpServers": {
    "pfrecipes": {
      "command": "pfrecipes-mcp",
      "args": [],
      "env": {
        "RECIPE_CHROMA_DIR": "/absolute/path/to/pfrecipes/.chroma",
        "RECIPE_RECIPES_DIR": "/absolute/path/to/pfrecipes/recipes"
      }
    }
  }
}
```

Use absolute paths in `env` — the MCP server is launched from a different working directory than the project root.

## Development

```bash
pip install -e ".[dev]"
pytest                        # 42 unit tests, no API key needed
pytest tests/test_quality.py  # AI quality tests, requires OPENAI_API_KEY + ingested recipes
```

### Test structure

| File | Type | Requires API key |
|---|---|---|
| `test_loaders.py` | Unit — loader parsing and dispatch | No |
| `test_ingest.py` | Unit — chunking, embeddings (mocked) | No |
| `test_search.py` | Unit — RAG pipeline (mocked) | No |
| `test_mcp_server.py` | Unit — MCP tool registration | No |
| `test_chat.py` | Unit — slash command routing | No |
| `test_quality.py` | Integration — retrieval + response quality | Yes |

### Quality tests

`test_quality.py` has three layers:

- **Retrieval** — checks that the right recipe chunks surface from ChromaDB for a given query (e.g., "garlic butter shrimp" → `garlic_butter_shrimp.md` in top 5 results)
- **Golden set** — parametrized cases with `must_contain` / `must_not_contain` assertions on real LLM responses
- **Sanity** — invariants like response length, no empty answers, conversation memory used in follow-ups

These skip automatically if `OPENAI_API_KEY` is unset or the knowledge base is empty.
