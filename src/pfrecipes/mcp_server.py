from mcp.server.fastmcp import FastMCP

mcp = FastMCP("pfrecipes")


@mcp.tool()
def recipe_search(query: str) -> str:
    """Search your recipe knowledge base with a natural language query.
    Returns an AI-generated answer grounded in your actual saved recipes."""
    from pfrecipes.search import search_recipes

    return search_recipes(query)


@mcp.tool()
def recipe_list() -> str:
    """List all recipes in the knowledge base with source and preview."""
    from pfrecipes.search import list_recipes

    recipes = list_recipes()
    if not recipes:
        return "No recipes in the knowledge base."

    lines = []
    for r in recipes:
        lines.append(f"- {r['source']}: {r['preview']}")
    return "\n".join(lines)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
