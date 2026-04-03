from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from pfrecipes import config
from pfrecipes.ingest import get_vector_store

SYSTEM_PROMPT = """You are a recipe assistant. Answer questions using ONLY the recipe context provided below. \
If the context contains relevant recipes, cite them by name. \
If nothing in the context matches the question, say "I don't have a recipe for that." \
Do not invent recipes or add information not present in the context.

Recipe context:
{context}"""

TOP_K = 5


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(model=config.LLM_MODEL)


def search_recipes(query: str) -> str:
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
            preview = (doc[:100] + "...") if len(doc) > 100 else doc
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
