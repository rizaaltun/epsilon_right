"""Book subcategories ("genres"): the chips on a book page and the nested
Category filter on /books/.

A book's "genres" is a list of labels from ORDER; a book can have several. On
/books/ each main category lists the subcategories its books use, with counts,
and a chip on a book page links to /books/?category=<main>&genre=<slug>.
"""

from .content import slugify
from .html import esc

ORDER = [
    "Literary Fiction", "Historical Fiction", "Fantasy", "Crime & Mystery",
    "Psychology", "Self-Help", "Health & Wellness", "Parenting & Education", "Popular Science",
    "Philosophy", "Essays", "Art", "History & Archaeology", "Cultural History", "Food & Drink",
    "Picture Book", "Early Readers", "Middle Grade",
]


def of(book: dict) -> list:
    """The book's subcategories, in ORDER (unknown labels last)."""
    labels = [g for g in book.get("genres") or [] if g]
    return sorted(labels, key=lambda g: (ORDER.index(g) if g in ORDER else len(ORDER), g))


def chips(r: str, book: dict) -> str:
    return "".join(
        f'<li><a href="{r}books/?category={book["category"]}&amp;genre={slugify(g)}"><span class="chip chip-quiet">'
        f"{esc(g)}</span></a></li>"
        for g in of(book)
    )


def _option(label: str, count: int, data: str) -> str:
    return (
        f'<li><label class="flex cursor-pointer items-center gap-2.5 text-sm"><input type="checkbox" {data} '
        f'class="size-4 shrink-0 accent-[var(--color-brand)]"/><span class="min-w-0 flex-1 truncate" '
        f'title="{esc(label)}">{esc(label)}</span><span class="text-xs text-ink-3 tabular-nums">{count}</span></label></li>'
    )


def category_filter(ctx) -> str:
    """The Category list on /books/: each main category, then its subcategories."""
    items = ""
    # The order the list had before subcategories, then any other category.
    first = ["adult-fiction", "non-fiction", "childrens-books", "young-adult"]
    for category in sorted(ctx.settings["categories"], key=lambda c: first.index(c["slug"]) if c["slug"] in first else len(first)):
        slug = category["slug"]
        books = ctx.books_in("category", slug)
        items += _option(category["label"], len(books), f'data-cat="{slug}"')
        counts = {}
        for _, book in books:
            for g in of(book):
                counts[g] = counts.get(g, 0) + 1
        subs = "".join(_option(g, counts[g], f'data-cat="{slug}" data-genre="{esc(g)}" data-slug="{slugify(g)}"')
                       for g in sorted(counts, key=lambda g: (ORDER.index(g) if g in ORDER else len(ORDER), g)))
        if subs:
            items = items[:-len("</li>")] + f'<ul class="mt-1.5 ml-1.5 space-y-1.5 border-l border-rule pl-3">{subs}</ul></li>'
    return f'<ul class="space-y-1.5 pr-1">{items}</ul>'
