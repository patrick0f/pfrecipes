from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from pfrecipes import config
from pfrecipes.ingest import get_vector_store

SYSTEM_PROMPT = """You are a helpful recipe assistant. You have access to the user's personal recipe collection below. \
Answer their questions based on these recipes. Mention recipe names when relevant. \
If the recipes below don't contain what the user is asking about, say so honestly.

Recipes:
{context}"""

TOP_K = 5


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(model=config.LLM_MODEL)


def search_recipes(query: str, history: list | None = None) -> str:
    store = get_vector_store()
    docs = store.similarity_search(query, k=TOP_K)

    if not docs:
        return "No recipes found in the knowledge base. Try ingesting some recipes first."

    context = "\n\n---\n\n".join(
        f"[Source: {d.metadata.get('source', 'unknown')}]\n{d.page_content}"
        for d in docs
    )

    llm = get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT.format(context=context)),
        *(history or []),
        HumanMessage(content=query),
    ]
    response = llm.invoke(messages)
    return response.content


def list_recipes() -> list[dict]:
    store = get_vector_store()
    collection = store._collection
    result = collection.get(include=["metadatas", "documents"])

    seen = {}
    for meta, doc in zip(result["metadatas"], result["documents"]):
        source = meta.get("source", "unknown")
        if source not in seen:
            clean = " ".join(doc.split())
            preview = (clean[:25] + "...") if len(clean) > 25 else clean
            seen[source] = {"source": source, "preview": preview}

    return sorted(seen.values(), key=lambda x: x["source"])


def remove_recipe(source: str) -> int:
    store = get_vector_store()
    collection = store._collection
    result = collection.get(where={"source": source}, include=[])

    ids = result["ids"]
    if ids:
        collection.delete(ids=ids)
    return len(ids)
