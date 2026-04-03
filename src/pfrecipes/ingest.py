from datetime import datetime
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pfrecipes import config
from pfrecipes.loaders import SUPPORTED_EXTENSIONS, load

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " "],
)


def get_embeddings() -> Embeddings:
    provider = config.EMBED_PROVIDER.lower()
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=config.EMBED_MODEL)
    elif provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(model=config.EMBED_MODEL)
    else:
        raise ValueError(
            f"Unsupported embedding provider: '{config.EMBED_PROVIDER}'. "
            f"Supported: openai, ollama"
        )


def get_vector_store():
    from langchain_chroma import Chroma

    return Chroma(
        collection_name="recipes",
        persist_directory=str(config.CHROMA_DIR),
        embedding_function=get_embeddings(),
    )


def _split_documents(docs: list[Document]) -> list[Document]:
    return _splitter.split_documents(docs)


def ingest_source(source: str) -> int:
    docs = load(source)
    chunks = _split_documents(docs)
    now = datetime.now().isoformat()
    for chunk in chunks:
        chunk.metadata["import_date"] = now
    store = get_vector_store()
    store.add_documents(chunks)
    return len(chunks)


def ingest_directory(directory: Path) -> int:
    total = 0
    for filepath in sorted(directory.rglob("*")):
        if not filepath.is_file():
            continue
        if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if any(part.startswith(".") for part in filepath.parts):
            continue
        total += ingest_source(str(filepath))
    return total
