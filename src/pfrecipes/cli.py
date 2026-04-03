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


@app.command()
def ingest(path: str = typer.Argument(help="File, directory, or URL to ingest.")):
    """Import recipes into the knowledge base."""
    from pfrecipes.ingest import ingest_directory, ingest_source

    if path.startswith("http://") or path.startswith("https://"):
        count = ingest_source(path)
        typer.echo(f"Ingested URL: {count} chunks stored.")
    elif Path(path).is_dir():
        count = ingest_directory(Path(path))
        typer.echo(f"Ingested directory: {count} chunks stored.")
    elif Path(path).is_file():
        count = ingest_source(path)
        typer.echo(f"Ingested {Path(path).name}: {count} chunks stored.")
    else:
        typer.echo(f"Error: '{path}' is not a valid file, directory, or URL.", err=True)
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


def _handle_chat_input(line: str) -> bool:
    """Handle a single line of chat input. Returns False to quit."""
    from pfrecipes.ingest import ingest_directory, ingest_source
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
        try:
            if path.startswith("http://") or path.startswith("https://"):
                count = ingest_source(path)
                typer.echo(f"\nIngested URL: {count} chunks stored.\n")
            elif Path(path).is_dir():
                count = ingest_directory(Path(path))
                typer.echo(f"\nIngested directory: {count} chunks stored.\n")
            elif Path(path).is_file():
                count = ingest_source(path)
                typer.echo(f"\nIngested {Path(path).name}: {count} chunks stored.\n")
            else:
                typer.echo(f"\nError: '{path}' is not a valid file, directory, or URL.\n")
        except Exception as e:
            typer.echo(f"\nError: {e}\n")
        return True

    if line.startswith("/"):
        typer.echo(f"\nUnknown command: {line.split()[0]}. Type /help for commands.\n")
        return True

    answer = search_recipes(line)
    typer.echo(f"\n{_format_answer(answer)}\n")
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
    while True:
        try:
            line = session.prompt("> ")
        except (KeyboardInterrupt, EOFError):
            typer.echo()
            break
        if not _handle_chat_input(line):
            break
