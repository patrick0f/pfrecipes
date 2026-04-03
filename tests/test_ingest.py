from langchain_core.documents import Document

from pfrecipes.ingest import _split_documents


class TestChunking:
    def test_short_document_stays_whole(self):
        doc = Document(page_content="A short recipe.", metadata={"source": "test"})
        chunks = _split_documents([doc])
        assert len(chunks) == 1
        assert chunks[0].page_content == "A short recipe."

    def test_long_document_gets_split(self):
        long_text = "Step one. " * 300  # ~3000 chars, well over chunk_size
        doc = Document(page_content=long_text, metadata={"source": "test"})
        chunks = _split_documents([doc])
        assert len(chunks) > 1

    def test_metadata_preserved_after_split(self):
        long_text = "Ingredient list. " * 200
        doc = Document(
            page_content=long_text,
            metadata={"source": "recipe.md"},
        )
        chunks = _split_documents([doc])
        for chunk in chunks:
            assert chunk.metadata["source"] == "recipe.md"


class TestGetEmbeddings:
    def test_openai_provider(self, monkeypatch):
        from pfrecipes import config
        from pfrecipes.ingest import get_embeddings

        monkeypatch.setattr(config, "EMBED_PROVIDER", "openai")
        monkeypatch.setattr(config, "EMBED_MODEL", "text-embedding-3-small")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        embeddings = get_embeddings()
        assert type(embeddings).__name__ == "OpenAIEmbeddings"

    def test_unsupported_provider(self, monkeypatch):
        import pytest

        from pfrecipes import config
        from pfrecipes.ingest import get_embeddings

        monkeypatch.setattr(config, "EMBED_PROVIDER", "unsupported")
        with pytest.raises(ValueError, match="Unsupported embedding provider"):
            get_embeddings()
