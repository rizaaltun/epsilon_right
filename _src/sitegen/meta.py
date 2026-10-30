"""assets/meta.json: compact per-book data for the /books search and filters."""

import json
import re

from . import covers
from .components import cover_size


def _is_square(ctx, book) -> bool:
    dimensions = cover_size(ctx, book)
    return bool(dimensions) and dimensions[1] / dimensions[0] < 1.1


def year(publication_year: str):
    """The first year in a free-text publication year such as "2024-2025"."""
    match = re.match(r"\s*(\d{4})", publication_year or "")
    return int(match.group(1)) if match else None


def render(ctx) -> str:
    meta = {
        slug: {
            "t": book["title"],
            "a": book["author"],
            "c": book["category"],
            "y": year(book.get("publication_year")),
            "l": book.get("rights_sold", []),
            "f": bool(book.get("featured")),
            "n": bool(book.get("new")),
            "p": "/" + covers.resolve(ctx, book["cover"])[0] if book["cover"] else None,
            "sq": _is_square(ctx, book),
        }
        for slug, book in ctx.books.items()
    }
    return json.dumps(meta, ensure_ascii=False, separators=(",", ":")) + "\n"
