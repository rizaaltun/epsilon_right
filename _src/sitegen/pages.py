"""Hand-built pages stored as a <main> fragment plus a small JSON record.

Slots in a fragment are filled from content at build time:
  <!--@cards select="RULE" wrap=li|none [article="classes"]-->
      RULE: all | catalogue:<slug> | imprint:<name> | category:<slug> | list:<name>
      (list names refer to the page record's "lists")
  <!--@count select="RULE"-->   the number of books RULE selects
"""

import json
import re
from pathlib import Path

from . import shell
from .components import book_card
from .html import prefix_for

COUNT = re.compile(r'<!--@count select="([^"]+)"-->')
SLOT = re.compile(r'<!--@cards select="([^"]+)" wrap=(li|none)(?: article="([^"]+)")?-->')


def load_pages(root: str) -> list:
    pages = []
    base = Path(root, "_src/content/pages")
    for record_file in sorted(base.glob("**/index.json")):
        record = json.loads(record_file.read_text(encoding="utf-8"))
        record["main"] = (record_file.parent / "index.html").read_text(encoding="utf-8")
        pages.append(record)
    return pages


def select(ctx, record: dict, rule: str) -> list:
    if rule == "all":
        return list(ctx.books.items())
    kind, _, value = rule.partition(":")
    if kind == "list":
        return [(s, ctx.books[s]) for s in record["lists"][value] if s in ctx.books]
    if kind in ("catalogue", "imprint", "category"):
        return ctx.books_in(kind, value)
    raise ValueError(f"unknown card selection {rule!r} on {record['path'] or 'home'}")


def render(ctx, record: dict) -> tuple:
    path = record["path"]
    r = prefix_for(path)

    def fill(match):
        rule, wrap, article = match.group(1), match.group(2), match.group(3) or "group"
        cards = (book_card(ctx, r, s, b, article_class=article) for s, b in select(ctx, record, rule))
        return "".join(f"<li>{c}</li>" if wrap == "li" else c for c in cards)

    main = SLOT.sub(fill, record["main"])
    main = COUNT.sub(lambda m: str(len(select(ctx, record, m.group(1)))), main)
    return path, shell.page(
        r, path, ctx.settings, record["title_html"], main,
        head_extra=record["head_extra"], tail_extra=record["tail_extra"], lazy_logos=record["lazy_logos"],
    )
