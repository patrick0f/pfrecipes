import json
import urllib.request
from html.parser import HTMLParser

from langchain_core.documents import Document


class _JsonLdExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._in_jsonld = False
        self._data_parts: list[str] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            attr_dict = dict(attrs)
            if attr_dict.get("type") == "application/ld+json":
                self._in_jsonld = True
                self._data_parts = []

    def handle_data(self, data):
        if self._in_jsonld:
            self._data_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._in_jsonld:
            self.scripts.append("".join(self._data_parts))
            self._in_jsonld = False


def _extract_recipe_from_jsonld(html: str) -> Document | None:
    parser = _JsonLdExtractor()
    parser.feed(html)

    for script in parser.scripts:
        try:
            data = json.loads(script)
        except json.JSONDecodeError:
            continue

        recipes = []
        if isinstance(data, list):
            recipes = data
        elif isinstance(data, dict):
            if data.get("@graph"):
                recipes = data["@graph"]
            else:
                recipes = [data]

        for item in recipes:
            if not isinstance(item, dict):
                continue
            item_type = item.get("@type", "")
            if isinstance(item_type, list):
                item_type = " ".join(item_type)
            if "Recipe" not in item_type:
                continue

            name = item.get("name", "Untitled Recipe")
            ingredients = item.get("recipeIngredient", [])
            instructions = item.get("recipeInstructions", [])

            parts = [f"# {name}", "", "## Ingredients"]
            for ing in ingredients:
                parts.append(f"- {ing}")

            parts.extend(["", "## Instructions"])
            for i, step in enumerate(instructions, 1):
                if isinstance(step, dict):
                    text = step.get("text", "")
                else:
                    text = str(step)
                parts.append(f"{i}. {text}")

            return Document(
                page_content="\n".join(parts),
                metadata={"recipe_name": name},
            )

    return None


def load_url(url: str) -> list[Document]:
    req = urllib.request.Request(url, headers={"User-Agent": "pfrecipes/0.1"})
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    doc = _extract_recipe_from_jsonld(html)
    if doc is not None:
        doc.metadata["source"] = url
        return [doc]

    from langchain_community.document_loaders import WebBaseLoader

    return WebBaseLoader(url).load()
