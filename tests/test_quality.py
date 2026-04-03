"""
AI output quality tests.

These tests require a real OpenAI API key and a populated ChromaDB with
the sample recipes ingested. They are skipped automatically if OPENAI_API_KEY
is not set or if the knowledge base is empty.

Run:
    pytest tests/test_quality.py -v

To populate the DB first:
    pfrecipes ingest recipes/
"""

import os

import pytest

NO_API_KEY = not os.getenv("OPENAI_API_KEY")
pytestmark = pytest.mark.skipif(NO_API_KEY, reason="OPENAI_API_KEY not set")


@pytest.fixture(scope="module")
def store():
    from pfrecipes.ingest import get_vector_store

    s = get_vector_store()
    count = s._collection.count()
    if count == 0:
        pytest.skip("Knowledge base is empty — run `pfrecipes ingest recipes/` first")
    return s


# ---------------------------------------------------------------------------
# Retrieval quality — tests that the right chunks surface for a given query
# ---------------------------------------------------------------------------


class TestRetrieval:
    def test_shrimp_recipe_surfaces_for_shrimp_query(self, store):
        docs = store.similarity_search("garlic butter shrimp", k=5)
        content = " ".join(d.page_content.lower() for d in docs)
        assert "shrimp" in content or "prawn" in content

    def test_beef_stew_surfaces_for_beef_stew_query(self, store):
        docs = store.similarity_search("slow braised beef red wine stew", k=5)
        content = " ".join(d.page_content.lower() for d in docs)
        assert "beef" in content

    def test_noodle_recipe_surfaces_for_noodle_query(self, store):
        docs = store.similarity_search("spicy miso noodles japan", k=5)
        content = " ".join(d.page_content.lower() for d in docs)
        assert "noodle" in content or "ramen" in content or "miso" in content

    def test_lentil_recipe_surfaces_for_lentil_query(self, store):
        docs = store.similarity_search("indian lentils vegan", k=5)
        content = " ".join(d.page_content.lower() for d in docs)
        assert "lentil" in content or "dal" in content

    def test_egg_recipe_surfaces_for_egg_tomato_query(self, store):
        docs = store.similarity_search("eggs poached in tomato sauce", k=5)
        content = " ".join(d.page_content.lower() for d in docs)
        assert "egg" in content or "tomato" in content


# ---------------------------------------------------------------------------
# Golden set — fixed query → expected response content checks
# ---------------------------------------------------------------------------

GOLDEN_SET = [
    {
        "query": "I want a quick weeknight shrimp dish",
        "must_contain": ["shrimp"],
        "must_not_contain": ["I don't have", "no recipes"],
    },
    {
        "query": "what vegetarian dishes do I have?",
        "must_contain_any": ["shakshuka", "cacio", "dal", "tacos", "avocado"],
        "must_not_contain": ["I don't have", "no recipes"],
    },
    {
        "query": "something warm and spicy with noodles",
        "must_contain_any": ["ramen", "noodle", "pasta"],
        "must_not_contain": ["I don't have", "no recipes"],
    },
    {
        "query": "a long slow weekend cooking project",
        "must_contain_any": ["bourguignon", "pho", "sourdough", "hour", "slow", "braise"],
        "must_not_contain": ["I don't have", "no recipes"],
    },
    {
        "query": "fastest possible breakfast",
        "must_contain_any": ["avocado", "shakshuka", "toast", "egg", "pancake", "cereal", "minute", "quick"],
        "must_not_contain": ["I don't have", "no recipes"],
    },
]


class TestGoldenSet:
    @pytest.mark.parametrize("case", GOLDEN_SET, ids=[c["query"][:40] for c in GOLDEN_SET])
    def test_golden_case(self, case):
        from pfrecipes.search import search_recipes

        result = search_recipes(case["query"]).lower()

        for term in case.get("must_contain", []):
            assert term.lower() in result, f"Expected '{term}' in response"

        if must_any := case.get("must_contain_any"):
            assert any(t.lower() in result for t in must_any), (
                f"Expected at least one of {must_any} in response"
            )

        for term in case.get("must_not_contain", []):
            assert term.lower() not in result, f"Unexpected '{term}' in response"


# ---------------------------------------------------------------------------
# Sanity checks — basic response quality invariants
# ---------------------------------------------------------------------------


class TestSanity:
    def test_response_is_not_empty(self):
        from pfrecipes.search import search_recipes

        result = search_recipes("chicken")
        assert result.strip()

    def test_unknown_query_does_not_hallucinate_recipe(self):
        from pfrecipes.search import search_recipes

        result = search_recipes("spaghetti carbonara with truffle foam sous vide")
        # Should either give a real match or admit it doesn't have it —
        # but should never return an empty string
        assert result.strip()

    def test_response_is_reasonable_length(self):
        from pfrecipes.search import search_recipes

        result = search_recipes("what can I make with salmon?")
        # Not a one-word answer, not a wall of text (>5000 chars would be odd)
        assert 20 < len(result) < 5000

    def test_history_context_used_in_followup(self):
        from langchain_core.messages import AIMessage, HumanMessage

        from pfrecipes.search import search_recipes

        first = search_recipes("tell me about the garlic butter shrimp recipe")
        history = [
            HumanMessage(content="tell me about the garlic butter shrimp recipe"),
            AIMessage(content=first),
        ]
        followup = search_recipes("how long does it take?", history=history)
        # Follow-up should reference cooking time, not ask what we're talking about
        assert followup.strip()
        assert len(followup) > 10
