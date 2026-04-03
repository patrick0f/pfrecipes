import shutil
import textwrap
from pathlib import Path

import typer

app = typer.Typer(help="AI-powered personal recipe knowledge base.")


def _format_answer(text: str) -> str:
    cols = shutil.get_terminal_size().columns
    wrap_width = max(40, cols - 8)
    indent = "    "
    lines = text.split("\n")
    wrapped = []
    for line in lines:
        if line.strip():
            wrapped.append(textwrap.fill(line, width=wrap_width, initial_indent=indent, subsequent_indent=indent))
        else:
            wrapped.append("")
    return "\n".join(wrapped)


def _ingest_with_progress(path: str) -> int:
    from pfrecipes.ingest import ingest_source, list_ingestable_files

    if path.startswith("http://") or path.startswith("https://"):
        typer.echo(f"Ingesting URL...")
        count = ingest_source(path)
        typer.echo(f"Done: {count} chunks stored.")
        return count

    p = Path(path)

    if p.is_dir():
        files = list_ingestable_files(p)
        if not files:
            typer.echo("No supported files found.")
            return 0
        typer.echo(f"Found {len(files)} file{'s' if len(files) != 1 else ''}.")
        total = 0
        for i, filepath in enumerate(files, 1):
            typer.echo(f"  [{i}/{len(files)}] {filepath.name}", nl=False)
            chunks = ingest_source(str(filepath))
            total += chunks
            typer.echo(f"  →  {chunks} chunks")
        typer.echo(f"Done: {total} chunks stored.")
        return total

    if p.is_file():
        typer.echo(f"Ingesting {p.name}...")
        count = ingest_source(path)
        typer.echo(f"Done: {count} chunks stored.")
        return count

    raise ValueError(f"'{path}' is not a valid file, directory, or URL.")


@app.command()
def ingest(path: str = typer.Argument(help="File, directory, or URL to ingest.")):
    """Import recipes into the knowledge base."""
    try:
        _ingest_with_progress(path)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def search(query: str = typer.Argument(help="Natural language query.")):
    """Search your recipes with natural language."""
    from pfrecipes.search import search_recipes

    answer = search_recipes(query)
    typer.echo(_format_answer(answer))


@app.command(name="list")
def list_cmd():
    """List all ingested recipes."""
    from pfrecipes.search import list_recipes

    recipes = list_recipes()
    if not recipes:
        typer.echo("No recipes in the knowledge base.")
        return
    for r in recipes:
        typer.echo(f"  {r['source']}")
        typer.echo(f"    {r['preview']}")
        typer.echo()


@app.command()
def remove(source: str = typer.Argument(help="Source path/URL to remove.")):
    """Remove a recipe from the knowledge base by source."""
    from pfrecipes.search import remove_recipe

    count = remove_recipe(source)
    if count:
        typer.echo(f"Removed {count} chunks for '{source}'.")
    else:
        typer.echo(f"No chunks found for '{source}'.")


HELP_TEXT = """Commands:
  /ingest <path-or-url>  Add recipes to the knowledge base
  /list                  Show all ingested recipes
  /remove <source>       Remove a recipe by source
  /help                  Show this help message
  /quit                  Exit"""


def _handle_chat_input(line: str, history: list | None = None) -> bool:
    """Handle a single line of chat input. Returns False to quit."""
    from pfrecipes.search import list_recipes, remove_recipe, search_recipes

    line = line.strip()
    if not line:
        return True

    if line in ("/quit", "/exit"):
        return False

    if line == "/help":
        typer.echo(f"\n{HELP_TEXT}\n")
        return True

    if line == "/list":
        recipes = list_recipes()
        if not recipes:
            typer.echo("\nNo recipes in the knowledge base.\n")
        else:
            typer.echo()
            for r in recipes:
                typer.echo(f"  {r['source']}  —  {r['preview']}")
            typer.echo()
        return True

    if line == "/remove" or line.startswith("/remove "):
        source = line[len("/remove"):].strip()
        if not source:
            typer.echo("\nUsage: /remove <source>\n")
            return True
        count = remove_recipe(source)
        if count:
            typer.echo(f"\nRemoved {count} chunks for '{source}'.\n")
        else:
            typer.echo(f"\nNo chunks found for '{source}'.\n")
        return True

    if line == "/ingest" or line.startswith("/ingest "):
        path = line[len("/ingest"):].strip()
        if not path:
            typer.echo("\nUsage: /ingest <path-or-url>\n")
            return True
        typer.echo()
        try:
            _ingest_with_progress(path)
        except Exception as e:
            typer.echo(f"Error: {e}")
        typer.echo()
        return True

    if line.startswith("/"):
        typer.echo(f"\nUnknown command: {line.split()[0]}. Type /help for commands.\n")
        return True

    from langchain_core.messages import AIMessage, HumanMessage

    answer = search_recipes(line, history)
    typer.echo(f"\n{_format_answer(answer)}\n")
    if history is not None:
        history.append(HumanMessage(content=line))
        history.append(AIMessage(content=answer))
        del history[:-20]
    return True


@app.command()
def chat():
    """Interactive chat mode — ask questions or use /commands."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.styles import Style

    completer = WordCompleter(
        ["/ingest", "/list", "/remove", "/help", "/quit"],
        meta_dict={
            "/ingest": "Add recipes to the knowledge base",
            "/list": "Show all ingested recipes",
            "/remove": "Remove a recipe by source",
            "/help": "Show available commands",
            "/quit": "Exit",
        },
        sentence=True,
    )
    style = Style.from_dict({
        "completion-menu": "bg:#ffffff #000000",
        "completion-menu.completion": "bg:#ffffff #000000",
        "completion-menu.completion.current": "bg:#dddddd #000000 bold",
        "completion-menu.meta.completion": "bg:#ffffff #666666",
        "completion-menu.meta.completion.current": "bg:#dddddd #444444",
    })
    session = PromptSession(completer=completer, style=style)

    typer.echo("pfrecipes — type a question or /help for commands.")
    typer.echo()
    history: list = []
    while True:
        try:
            line = session.prompt("> ")
        except (KeyboardInterrupt, EOFError):
            typer.echo()
            break
        if not _handle_chat_input(line, history):
            break
