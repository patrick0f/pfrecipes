from unittest.mock import MagicMock, patch


class TestMcpToolsRegistered:
    def test_has_recipe_search_tool(self):
        from pfrecipes.mcp_server import mcp

        tool_names = [t.name for t in mcp._tool_manager.list_tools()]
        assert "recipe_search" in tool_names

    def test_has_recipe_list_tool(self):
        from pfrecipes.mcp_server import mcp

        tool_names = [t.name for t in mcp._tool_manager.list_tools()]
        assert "recipe_list" in tool_names


class TestRecipeSearchTool:
    def test_calls_search_recipes(self, monkeypatch):
        from pfrecipes.mcp_server import recipe_search

        monkeypatch.setattr(
            "pfrecipes.search.search_recipes",
            lambda q: f"Found recipe for: {q}",
        )
        result = recipe_search("chicken")
        assert "Found recipe for: chicken" == result


class TestRecipeListTool:
    def test_formats_recipes(self, monkeypatch):
        from pfrecipes.mcp_server import recipe_list

        monkeypatch.setattr(
            "pfrecipes.search.list_recipes",
            lambda: [
                {"source": "shrimp.md", "preview": "Garlic Butter Shrimp..."},
                {"source": "ramen.md", "preview": "Spicy Miso Ramen..."},
            ],
        )
        result = recipe_list()
        assert "shrimp.md" in result
        assert "ramen.md" in result

    def test_empty_knowledge_base(self, monkeypatch):
        from pfrecipes.mcp_server import recipe_list

        monkeypatch.setattr("pfrecipes.search.list_recipes", lambda: [])
        result = recipe_list()
        assert "No recipes" in result
