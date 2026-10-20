"""Load the JSON content files under _src/content/ into one context object."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

_TR = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "İ": "i", "ö": "o", "ş": "s", "ü": "u",
                     "Ç": "c", "Ğ": "g", "Ö": "o", "Ş": "s", "Ü": "u", "â": "a", "î": "i", "û": "u"})


def slugify(value: str) -> str:
    """Turkish-aware URL slug, matching the slugs the original site used."""
    s = value.translate(_TR).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _load_folder(folder: Path) -> dict:
    items = {}
    for path in sorted(folder.glob("*.json")):
        items[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    return items


@dataclass
class Context:
    root: str
    settings: dict
    write: bool = False                            # may the build create files (cover variants)?
    books: dict = field(default_factory=dict)      # slug -> book, in display order
    authors: dict = field(default_factory=dict)    # slug -> author
    news: dict = field(default_factory=dict)       # slug -> article
    events: dict = field(default_factory=dict)     # slug -> fair / event
    publishers: dict = field(default_factory=dict) # slug -> publisher (imprint)
    services: dict = field(default_factory=dict)   # slug -> service
    shared: dict = field(default_factory=dict)     # settings files usable in page templates

    def books_by_author(self, author_slug: str) -> list:
        return [(s, b) for s, b in self.books.items() if b["author_slug"] == author_slug]

    def books_in(self, key: str, value: str) -> list:
        return [(s, b) for s, b in self.books.items() if b.get(key) == value]


def load(root: Path, write: bool = False) -> Context:
    content = root / "_src/content"
    settings = json.loads((content / "settings/site.json").read_text(encoding="utf-8"))
    settings.update(json.loads((content / "settings/categories.json").read_text(encoding="utf-8")))
    authors = _load_folder(content / "authors") if (content / "authors").exists() else {}
    # Books name their author in free text; match it to an author file by the
    # name's slug, so spelling variants such as Sağbaş/Şağbaş share one page.
    by_name = {slugify(a["name"]): slug for slug, a in authors.items()}
    books = _load_folder(content / "books")
    for book in books.values():
        name_slug = slugify(book["author"])
        book["author_slug"] = by_name.get(name_slug, name_slug)
    # New books without an order go last; the admin panel numbers from 1.
    books = dict(sorted(books.items(), key=lambda kv: (kv[1].get("order") is None, kv[1].get("order") or 0, kv[0])))
    news = _load_folder(content / "news") if (content / "news").exists() else {}
    events = _load_folder(content / "events") if (content / "events").exists() else {}
    publishers = _load_folder(content / "publishers") if (content / "publishers").exists() else {}
    services = _load_folder(content / "services") if (content / "services").exists() else {}
    shared = {"site": settings}
    for name in ("stats", "contact"):
        path = content / "settings" / f"{name}.json"
        if path.exists():
            shared[name] = json.loads(path.read_text(encoding="utf-8"))
    return Context(root=str(root), settings=settings, write=write, books=books, authors=authors,
                   news=news, events=events, publishers=publishers, services=services, shared=shared)
