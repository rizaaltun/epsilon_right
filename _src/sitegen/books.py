"""Book detail pages: /books/<slug>/."""

import re
from urllib.parse import quote

from . import samples, seo, shell
from .components import FILL, HERO_SIZES, aspect, book_card, breadcrumb, cover_img, section_heading
from .html import esc, prefix_for

DETAIL_ROWS = [
    ("original_title", "Original title"),
    ("original_language", "Original language"),
    ("english_title", "English title"),
    ("imprint", "Imprint"),
    ("pages", "Pages"),
    ("publication_year", "Publication year"),
    ("illustrator", "Illustrator"),
    ("age_group", "Age group"),
    ("isbn", "ISBN"),
]
RAIL_SIZE = 8


def category_label(ctx, slug: str) -> str:
    for category in ctx.settings["categories"]:
        if category["slug"] == slug:
            return category["label"]
    raise KeyError(f"unknown category {slug!r}")


def paragraphs(text: str) -> str:
    return "".join(f"<p>{esc(p)}</p>" for p in text.split("\n\n") if p.strip())


def related(ctx, slug: str) -> list:
    """The next books after this one in its category, wrapping round the list."""
    same = ctx.books_in("category", ctx.books[slug]["category"])
    index = [s for s, _ in same].index(slug)
    rotated = same[index + 1:] + same[:index]
    return rotated[:RAIL_SIZE]


def _hero(ctx, r: str, book: dict) -> str:
    ratio = aspect(book)
    if book["cover"]:
        art = (
            f'<div class="relative overflow-hidden bg-paper-3 h-full w-full" style="aspect-ratio:{ratio}">'
            + cover_img(ctx, r, book, hero=True)
            + "</div>"
        )
    else:
        art = (
            '<div class="flex items-center justify-center bg-paper-3 text-ink-3 h-full w-full"><span class="px-4 '
            f'text-center font-display text-base leading-tight text-ink-3">{esc(book["title"])}</span></div>'
        )
    return f'<div class="cover" style="aspect-ratio:{ratio}">{art}</div>'


def _author(ctx, r: str, book: dict) -> str:
    if book["author_slug"] in ctx.authors:
        return f'<span><a class="link" href="{r}authors/{book["author_slug"]}/">{esc(book["author"])}</a></span>'
    return f'<span>{esc(book["author"])}</span>'


def render(ctx, slug: str) -> tuple:
    book = ctx.books[slug]
    path = f"books/{slug}/"
    r = prefix_for(path)
    email = ctx.settings["email"]
    subject = quote("Rights enquiry: " + book["title"])
    rows = "".join(
        f'<div class="grid grid-cols-[minmax(7rem,9rem)_1fr] gap-4 py-3"><dt class="text-ink-3">{label}</dt>'
        f'<dd class="text-ink">{esc(book[key])}</dd></div>'
        for key, label in DETAIL_ROWS
        if book.get(key)
    )
    # The original pages give hero loading hints to the first cover image on a
    # book page; with no cover of its own, that image sits in the rail.
    hero_pending = not book["cover"]
    rail = ""
    for s, b in related(ctx, slug):
        hero = hero_pending and bool(b["cover"])
        hero_pending = hero_pending and not hero
        rail += f'<div class="w-36 sm:w-40 lg:w-44">{book_card(ctx, r, s, b, hero_image=hero)}</div>'
    enquire = f"mailto:{email}?subject={subject}"
    english = samples.for_book(ctx, slug)
    main = (
        '<main id="main" class="flex-1">'
        + breadcrumb(r, [("", "Home"), ("books/", "Books")], book["title"])
        + '<section class="py-14 md:py-20 pt-8 md:pt-10"><div><div class="shell"><div class="grid gap-10 '
        'lg:grid-cols-[minmax(0,19rem)_minmax(0,1fr)] lg:gap-16"><div class="lg:sticky lg:top-24 lg:self-start">'
        '<div class="mx-auto max-w-[19rem]">'
        + _hero(ctx, r, book)
        + '<section aria-label="Rights" class="mt-6"><p class="eyebrow">Rights</p><p class="mt-3 text-sm '
        f'leading-relaxed text-ink-2">{esc(book["rights"])}</p><div class="mt-4 flex flex-col gap-2"><a '
        f'href="{enquire}" class="btn btn-accent w-full">Enquire about rights</a>'
        + (samples.buttons(english) if english else "")
        + f'<a href="{r}catalogues/{book["catalogue"]}/#catalogue-reader" class="btn btn-outline w-full">Read '
        'catalogue</a></div></section></div></div><div class="min-w-0"><ul class="mb-5 flex flex-wrap gap-2"><li>'
        f'<a href="{r}books/?category={book["category"]}"><span class="chip">{esc(category_label(ctx, book["category"]))}'
        f'</span></a></li></ul><h1 class="text-display-lg">{esc(book["title"])}</h1><p class="mt-5 '
        f'text-[0.9375rem] text-ink-2">{_author(ctx, r, book)}</p><div class="measure mt-8"><div '
        f'class="prose-editorial">{paragraphs(book["description"])}</div></div><dl class="divide-y divide-rule '
        f'border-y border-rule text-sm mt-10">{rows}</dl></div></div></div></div></section>'
        + (samples.readers(r, book["title"], enquire, english) if english else "")
        + '<section class="py-14 md:py-20 ground-paper"><div><div class="shell">'
        + section_heading("More in this category")
        + '<div class="relative"><div class="rail" role="group" aria-label="More in this category" tabindex="0">'
        f"{rail}</div></div></div></div></section><!--$--><!--/$--></main>"
    )
    extra = {"head_extra": samples.head_extra(ctx), "tail_extra": samples.tail_extra(ctx)} if english else {}
    return path, shell.page(r, path, ctx.settings, seo.title_html(ctx, book, book["title"]), main,
                            seo_html=seo.head_tags(ctx, book_seo(ctx, slug, path)), **extra)


def book_seo(ctx, slug: str, path: str):
    from .covers import resolve
    book = ctx.books[slug]
    category = category_label(ctx, book["category"])
    fallback = f'{book["title"]} by {book["author"]} — {category}. {book.get("rights") or "Translation rights available"}.'
    description = seo.describe(book, book.get("description"), fallback)
    image = "/" + resolve(ctx, book["cover"])[0] if book["cover"] else ""
    data = {
        "@type": "Book",
        "@id": seo.url(ctx, path) + "#book",
        "name": book["title"],
        "url": seo.url(ctx, path),
        "author": {"@type": "Person", "name": book["author"]},
        "genre": category,
        "publisher": {"@type": "Organization", "name": book.get("imprint") or ctx.settings["site_name"]},
    }
    for pub_slug, pub in ctx.publishers.items():
        if book.get("imprint") and pub.get("imprint") == book["imprint"]:
            data["publisher"] = {"@type": "Organization", "name": pub["name"], "url": seo.url(ctx, f"publishers/{pub_slug}/")}
    if book["author_slug"] in ctx.authors:
        data["author"]["url"] = seo.url(ctx, f'authors/{book["author_slug"]}/')
    if book.get("description"):
        data["description"] = seo.clip(book["description"], 500)
    if image:
        data["image"] = seo.url(ctx, image)
    if book.get("english_title") and book["english_title"] != book["title"]:
        data["alternateName"] = book["english_title"]
    language = seo.LANGUAGES.get((book.get("original_language") or "").strip().lower())
    if language:
        data["inLanguage"] = language
    if str(book.get("pages", "")).strip().isdigit():
        data["numberOfPages"] = int(book["pages"])
    year = re.match(r"\s*(\d{4})", book.get("publication_year") or "")
    if year:
        data["datePublished"] = year.group(1)
    if book.get("illustrator"):
        data["illustrator"] = {"@type": "Person", "name": book["illustrator"]}
    if book.get("isbn"):
        data["isbn"] = re.sub(r"[^0-9Xx]", "", book["isbn"])
    ages = seo.age_range(book.get("age_group"))
    if ages:
        data["typicalAgeRange"] = ages
    crumbs = seo.breadcrumbs(ctx, [("Home", ""), ("Books", "books/"), (book["title"], path)])
    return seo.Seo(path=path, title=book["title"], description=description, image=image, type="book",
                   jsonld=[data, crumbs])
