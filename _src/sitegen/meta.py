"""assets/meta.json: compact per-book data for the /books search and filters."""

import json
import re

from . import covers


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
            "sq": bool(book.get("square_cover")),
        }
        for slug, book in ctx.books.items()
    }
    return json.dumps(meta, ensure_ascii=False, separators=(",", ":")) + "\n"
