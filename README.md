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

## Development

```bash
pip install -e ".[dev]"
pytest
```
