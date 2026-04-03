from unittest.mock import MagicMock

from pfrecipes.cli import _handle_chat_input


class TestSlashCommands:
    def test_quit(self):
        assert _handle_chat_input("/quit") is False

    def test_exit(self):
        assert _handle_chat_input("/exit") is False

    def test_empty_input(self):
        assert _handle_chat_input("") is True
        assert _handle_chat_input("   ") is True

    def test_help(self, capsys):
        assert _handle_chat_input("/help") is True
        output = capsys.readouterr().out
        assert "/ingest" in output
        assert "/list" in output
        assert "/remove" in output

    def test_list(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "pfrecipes.search.list_recipes",
            lambda: [{"source": "shrimp.md", "preview": "Garlic Butter Shrimp..."}],
        )
        assert _handle_chat_input("/list") is True
        output = capsys.readouterr().out
        assert "shrimp.md" in output

    def test_list_empty(self, monkeypatch, capsys):
        monkeypatch.setattr("pfrecipes.search.list_recipes", lambda: [])
        assert _handle_chat_input("/list") is True
        output = capsys.readouterr().out
        assert "No recipes" in output

    def test_remove(self, monkeypatch, capsys):
        monkeypatch.setattr("pfrecipes.search.remove_recipe", lambda s: 3)
        assert _handle_chat_input("/remove shrimp.md") is True
        output = capsys.readouterr().out
        assert "Removed 3 chunks" in output

    def test_remove_no_arg(self, capsys):
        assert _handle_chat_input("/remove ") is True
        output = capsys.readouterr().out
        assert "Usage" in output

    def test_ingest_file(self, monkeypatch, capsys, tmp_path):
        recipe = tmp_path / "test.md"
        recipe.write_text("# Test Recipe")
        monkeypatch.setattr("pfrecipes.ingest.ingest_source", lambda s: 1)
        assert _handle_chat_input(f"/ingest {recipe}") is True
        output = capsys.readouterr().out
        assert "1 chunks stored" in output

    def test_unknown_command(self, capsys):
        assert _handle_chat_input("/foo") is True
        output = capsys.readouterr().out
        assert "Unknown command" in output


class TestSearchFallthrough:
    def test_plain_text_goes_to_search(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "pfrecipes.search.search_recipes",
            lambda q, history=None: f"Answer for: {q}",
        )
        assert _handle_chat_input("what shrimp recipes do I have?") is True
        output = capsys.readouterr().out
        assert "Answer for: what shrimp recipes do I have?" in output

    def test_history_grows_after_search(self, monkeypatch):
        from langchain_core.messages import AIMessage, HumanMessage

        monkeypatch.setattr(
            "pfrecipes.search.search_recipes",
            lambda q, history=None: "some answer",
        )
        history: list = []
        _handle_chat_input("first question", history)
        assert len(history) == 2
        assert isinstance(history[0], HumanMessage)
        assert isinstance(history[1], AIMessage)
        assert history[0].content == "first question"
        assert history[1].content == "some answer"
