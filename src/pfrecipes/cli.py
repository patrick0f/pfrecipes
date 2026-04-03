from pathlib import Path

import typer

app = typer.Typer(help="AI-powered personal recipe knowledge base.")


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
    typer.echo(answer)


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
