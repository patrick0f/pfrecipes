import typer

app = typer.Typer(help="AI-powered personal recipe knowledge base.")


@app.command()
def ingest(path: str = typer.Argument(help="File, directory, or URL to ingest.")):
    """Import recipes into the knowledge base."""
    typer.echo(f"[stub] ingest: {path}")


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
