from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


class TestMarkdownLoader:
    def test_loads_document(self):
        from pfrecipes.loaders.markdown import load_markdown

        docs = load_markdown(FIXTURES / "sample_recipe.md")
        assert len(docs) == 1
        assert "Garlic Butter Shrimp" in docs[0].page_content
        assert "source" in docs[0].metadata

    def test_contains_ingredients(self):
        from pfrecipes.loaders.markdown import load_markdown

        docs = load_markdown(FIXTURES / "sample_recipe.md")
        assert "shrimp" in docs[0].page_content.lower()
        assert "garlic" in docs[0].page_content.lower()


class TestTextLoader:
    def test_loads_document(self):
        from pfrecipes.loaders.text import load_text

        docs = load_text(FIXTURES / "sample_recipe.txt")
        assert len(docs) == 1
        assert "Garlic Butter Shrimp" in docs[0].page_content
        assert "source" in docs[0].metadata


class TestPdfLoader:
    def test_loads_document(self):
        from pfrecipes.loaders.pdf import load_pdf

        docs = load_pdf(FIXTURES / "sample_recipe.pdf")
        assert len(docs) >= 1
        combined = " ".join(d.page_content for d in docs)
        assert "Garlic Butter Shrimp" in combined

    def test_contains_ingredients(self):
        from pfrecipes.loaders.pdf import load_pdf

        docs = load_pdf(FIXTURES / "sample_recipe.pdf")
        combined = " ".join(d.page_content for d in docs)
        assert "shrimp" in combined.lower()


class TestJsonLdExtraction:
    def test_extracts_recipe(self):
        from pfrecipes.loaders.url import _extract_recipe_from_jsonld

        html = (FIXTURES / "sample_jsonld.html").read_text()
        doc = _extract_recipe_from_jsonld(html)
        assert doc is not None
        assert "Spicy Miso Ramen" in doc.page_content
        assert "ramen noodles" in doc.page_content
        assert "miso paste" in doc.page_content
        assert doc.metadata["recipe_name"] == "Spicy Miso Ramen"

    def test_returns_none_for_no_recipe(self):
        from pfrecipes.loaders.url import _extract_recipe_from_jsonld

        doc = _extract_recipe_from_jsonld("<html><body>No recipe here</body></html>")
        assert doc is None


class TestLoadDispatcher:
    def test_markdown_dispatch(self):
        from pfrecipes.loaders import load

        docs = load(str(FIXTURES / "sample_recipe.md"))
        assert len(docs) == 1
        assert "Garlic Butter Shrimp" in docs[0].page_content

    def test_text_dispatch(self):
        from pfrecipes.loaders import load

        docs = load(str(FIXTURES / "sample_recipe.txt"))
        assert len(docs) == 1

    def test_pdf_dispatch(self):
        from pfrecipes.loaders import load

        docs = load(str(FIXTURES / "sample_recipe.pdf"))
        assert len(docs) >= 1

    def test_unsupported_extension(self):
        from pfrecipes.loaders import load

        with pytest.raises(ValueError, match="Unsupported file type"):
            load("recipe.docx")

    def test_url_detected(self, monkeypatch):
        from pfrecipes.loaders import load
        from pfrecipes.loaders import url as url_mod
        from langchain_core.documents import Document

        def mock_load_url(u):
            return [Document(page_content="mocked", metadata={"source": u})]

        monkeypatch.setattr(url_mod, "load_url", mock_load_url)
        docs = load("https://example.com/recipe")
        assert docs[0].page_content == "mocked"
