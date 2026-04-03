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
    typer.echo(f"[stub] search: {query}")


@app.command()
def list():
    """List all ingested recipes."""
    typer.echo("[stub] list")


@app.command()
def remove(name: str = typer.Argument(help="Recipe name to remove.")):
    """Remove a recipe from the knowledge base."""
    typer.echo(f"[stub] remove: {name}")
