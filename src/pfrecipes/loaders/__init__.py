from pathlib import Path

from langchain_core.documents import Document

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}


def load(source: str) -> list[Document]:
    if source.startswith("http://") or source.startswith("https://"):
        from pfrecipes.loaders.url import load_url

        return load_url(source)

    path = Path(source)
    suffix = path.suffix.lower()

    if suffix == ".md":
        from pfrecipes.loaders.markdown import load_markdown

        return load_markdown(path)
    elif suffix == ".txt":
        from pfrecipes.loaders.text import load_text

        return load_text(path)
    elif suffix == ".pdf":
        from pfrecipes.loaders.pdf import load_pdf

        return load_pdf(path)
    else:
        raise ValueError(
            f"Unsupported file type: '{suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))} and URLs."
        )
