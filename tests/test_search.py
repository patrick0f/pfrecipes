from unittest.mock import MagicMock, patch

import pytest


class TestGetLlm:
    def test_returns_chat_openai(self, monkeypatch):
        from pfrecipes import config
        from pfrecipes.search import get_llm

        monkeypatch.setattr(config, "LLM_MODEL", "gpt-4o-mini")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        llm = get_llm()
        assert type(llm).__name__ == "ChatOpenAI"
        assert llm.model_name == "gpt-4o-mini"


class TestSearchRecipes:
    def test_returns_llm_response(self, monkeypatch):
        from langchain_core.documents import Document

        from pfrecipes.search import search_recipes

        mock_store = MagicMock()
        mock_store.similarity_search.return_value = [
            Document(
                page_content="# Garlic Shrimp\nShrimp with garlic and butter.",
                metadata={"source": "shrimp.md"},
            )
        ]

        mock_response = MagicMock()
        mock_response.content = "Based on your recipes, try the Garlic Shrimp!"

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response

        monkeypatch.setattr("pfrecipes.search.get_vector_store", lambda: mock_store)
        monkeypatch.setattr("pfrecipes.search.get_llm", lambda: mock_llm)

        result = search_recipes("shrimp recipe")
        assert "Garlic Shrimp" in result
        mock_store.similarity_search.assert_called_once_with("shrimp recipe", k=5)
        mock_llm.invoke.assert_called_once()

    def test_empty_store(self, monkeypatch):
        from pfrecipes.search import search_recipes

        mock_store = MagicMock()
        mock_store.similarity_search.return_value = []

        monkeypatch.setattr("pfrecipes.search.get_vector_store", lambda: mock_store)

        result = search_recipes("anything")
        assert "No recipes found" in result


class TestListRecipes:
    def test_lists_unique_sources(self, monkeypatch):
        from pfrecipes.search import list_recipes

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "metadatas": [
                {"source": "shrimp.md"},
                {"source": "shrimp.md"},
                {"source": "ramen.md"},
            ],
            "documents": [
                "# Garlic Shrimp\nShrimp with garlic.",
                "Instructions: Cook shrimp.",
                "# Spicy Miso Ramen\nA warming bowl of ramen.",
            ],
        }

        mock_store = MagicMock()
        mock_store._collection = mock_collection

        monkeypatch.setattr("pfrecipes.search.get_vector_store", lambda: mock_store)

        recipes = list_recipes()
        assert len(recipes) == 2
        sources = [r["source"] for r in recipes]
        assert "ramen.md" in sources
        assert "shrimp.md" in sources

    def test_preview_truncated(self, monkeypatch):
        from pfrecipes.search import list_recipes

        long_content = "A" * 200

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "metadatas": [{"source": "long.md"}],
            "documents": [long_content],
        }

        mock_store = MagicMock()
        mock_store._collection = mock_collection

        monkeypatch.setattr("pfrecipes.search.get_vector_store", lambda: mock_store)

        recipes = list_recipes()
        assert recipes[0]["preview"].endswith("...")
        assert len(recipes[0]["preview"]) == 103  # 100 chars + "..."


class TestRemoveRecipe:
    def test_removes_matching_chunks(self, monkeypatch):
        from pfrecipes.search import remove_recipe

        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": ["id1", "id2", "id3"]}

        mock_store = MagicMock()
        mock_store._collection = mock_collection

        monkeypatch.setattr("pfrecipes.search.get_vector_store", lambda: mock_store)

        count = remove_recipe("shrimp.md")
        assert count == 3
        mock_collection.delete.assert_called_once_with(ids=["id1", "id2", "id3"])

    def test_no_matches(self, monkeypatch):
        from pfrecipes.search import remove_recipe

        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": []}

        mock_store = MagicMock()
        mock_store._collection = mock_collection

        monkeypatch.setattr("pfrecipes.search.get_vector_store", lambda: mock_store)

        count = remove_recipe("nonexistent.md")
        assert count == 0
        mock_collection.delete.assert_not_called()
