"""Book subcategories ("genres"): the chips on a book page and the nested
Category filter on /books/.

A book's "genres" is a list of labels from ORDER; a book can have several. On
/books/ each main category lists the subcategories its books use, with counts,
and a chip on a book page links to /books/?category=<main>&genre=<slug>.

Books marked "backlist" also get the Backlist filter on /books/ (all of them, or
those of one main category), opened by /books/?backlist=all|<category>.
"""

from .content import slugify
from .html import esc

ORDER = [
    "Literary Fiction", "Historical Fiction", "Fantasy", "Crime & Mystery", "Short Stories",
    "Psychology", "Self-Help", "Health & Wellness", "Parenting & Education", "Popular Science",
    "Philosophy", "Essays", "Art", "History & Archaeology", "Cultural History", "Food & Drink",
    "Picture Book", "Board Book", "Early Readers", "Middle Grade",
]


def of(book: dict) -> list:
    """The book's subcategories, in ORDER (unknown labels last)."""
    return sorted({g for g in book.get("genres") or [] if g}, key=_rank)


def _rank(label: str):
    return (ORDER.index(label) if label in ORDER else len(ORDER), label)


def chips(r: str, book: dict) -> str:
    out = "".join(
        f'<li><a href="{r}books/?category={book["category"]}&amp;genre={slugify(g)}"><span class="chip chip-quiet">'
        f"{esc(g)}</span></a></li>"
        for g in of(book)
    )
    if book.get("backlist"):
        out += (f'<li><a href="{r}books/?backlist={book["category"]}"><span class="chip chip-quiet">Backlist</span>'
                "</a></li>")
    return out


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
        items = _nest(items, "".join(_option(g, counts[g], f'data-cat="{slug}" data-genre="{esc(g)}" data-slug="{slugify(g)}"')
                                     for g in sorted(counts, key=_rank)))
    return f'<ul class="space-y-1.5 pr-1">{items}</ul>'


def _nest(item: str, children: str) -> str:
    """Put ``children`` (<li>s) in a sub-list inside the last <li> of ``item``."""
    if not children:
        return item
    return item[:-len("</li>")] + f'<ul class="mt-1.5 ml-1.5 space-y-1.5 border-l border-rule pl-3">{children}</ul></li>'


def backlist_filter(ctx) -> str:
    """The Backlist list on /books/: all backlist titles, then by main category; "" if none."""
    books = [b for _, b in ctx.books.items() if b.get("backlist")]
    if not books:
        return ""
    first = ["adult-fiction", "non-fiction", "childrens-books", "young-adult"]
    subs = ""
    for category in sorted(ctx.settings["categories"], key=lambda c: first.index(c["slug"]) if c["slug"] in first else len(first)):
        n = sum(1 for b in books if b["category"] == category["slug"])
        if n:
            subs += _option(category["label"], n, f'data-backlist="{category["slug"]}"')
    items = _nest(_option("All backlist titles", len(books), 'data-backlist="all"'), subs)
    return (f'<fieldset class="py-4"><legend class="field-label">Backlist</legend><ul class="space-y-1.5 pr-1">{items}'
            '</ul></fieldset>')
