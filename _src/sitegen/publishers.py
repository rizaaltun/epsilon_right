"""Publishers (/publishers/<slug>/ and the publisher cards), plus the author
cards and counts used on /authors/ and /representations/.

Title counts are always computed from the books: a publisher's titles are the
books whose imprint is the publisher's imprint; an author's are the books whose
author name matches the author.
"""

import html
import re
import unicodedata
from pathlib import Path

from . import markdown, seo, shell
from .authors import initials
from .components import book_card, breadcrumb, section_heading
from .html import esc, prefix_for
from .imagesize import size


def titles(ctx, slug: str) -> list:
    return ctx.books_in("imprint", ctx.publishers[slug]["imprint"])


def plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def ordered(ctx) -> list:
    """Display order set in the admin panel (drag and drop), then name."""
    return sorted(ctx.publishers.items(), key=lambda kv: (kv[1].get("order") is None, kv[1].get("order") or 0, kv[0]))


def by_titles(ctx) -> list:
    return sorted(ctx.publishers.items(), key=lambda kv: (-len(titles(ctx, kv[0])), kv[1]["name"]))


def _logo(ctx, r, pub, card: bool) -> str:
    if not pub.get("logo"):
        cls = "text-2xl" if card else "text-3xl"
        return f'<span class="font-display {cls} text-ink-3">{esc(initials(pub["name"]))}</span>'
    rel = pub["logo"].lstrip("/")
    w, h = pub.get("logo_width"), pub.get("logo_height")
    if not (w and h):
        w, h = size(str(Path(ctx.root, rel))) or (None, None)
    dims = f' width="{w}" height="{h}"' if w and h else ""
    lazy = ' loading="lazy"' if card else ""
    cls = "max-h-14" if card else "max-h-16"
    return (
        f'<img alt="{esc(pub["name"])} logo"{lazy}{dims} decoding="async" data-nimg="1" class="{cls} w-auto '
        f'object-contain" style="color:transparent" src="{r}{esc(rel)}"/>'
    )


def _summary(pub) -> str:
    """Card text: the short summary, else the description's first paragraph as plain text."""
    if pub.get("summary"):
        return pub["summary"]
    first = (pub.get("description") or "").strip().split("\n\n")[0]
    return html.unescape(re.sub(r"<[^>]+>", "", markdown.inline(first))) if first else ""


def card(ctx, r: str, slug: str) -> str:
    pub = ctx.publishers[slug]
    count = len(titles(ctx, slug))
    return (
        f'<article class="card card-hover group flex h-full flex-col p-5"><a class="flex h-full flex-col" '
        f'href="{r}publishers/{slug}/"><div class="mb-4 flex h-14 items-center">{_logo(ctx, r, pub, True)}</div>'
        '<h3 class="font-display text-lg leading-snug transition-colors group-hover:text-accent">'
        f'{esc(pub["name"])}</h3><p class="mt-1 text-[0.8125rem] text-ink-3">{esc(pub.get("country", ""))}</p>'
        f'<p class="clamp-3 mt-3 text-sm leading-relaxed text-ink-2">{esc(_summary(pub))}</p><p class="mt-auto pt-4 '
        f'text-xs text-ink-3">{count}<!-- --> {"title" if count == 1 else "titles"} represented</p></a></article>'
    )


def cards(ctx, r: str, order: str = "panel") -> str:
    items = by_titles(ctx) if order == "titles" else ordered(ctx)
    return "".join(f"<li>{card(ctx, r, s)}</li>" for s, _ in items)


def countries(ctx) -> list:
    counts = {}
    for _, pub in ordered(ctx):
        if pub.get("country"):
            counts[pub["country"]] = counts.get(pub["country"], 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def country_filter(ctx) -> str:
    return "".join(
        '<li><label class="flex cursor-pointer items-center gap-2.5 text-sm"><input type="checkbox" class="size-4 '
        f'shrink-0 accent-[var(--color-brand)]"/><span class="min-w-0 flex-1 truncate" title="{esc(c)}">{esc(c)}</span>'
        f'<span class="text-xs text-ink-3 tabular-nums">{n}</span></label></li>'
        for c, n in countries(ctx)
    )


def featured_filter(ctx, kind: str) -> str:
    items = ctx.publishers if kind == "publishers" else ctx.authors
    n = sum(1 for x in items.values() if x.get("featured"))
    if not n:
        return ""
    return (
        '<div class="py-4"><label class="flex cursor-pointer items-center gap-2.5 text-sm"><input type="checkbox" '
        'class="size-4 shrink-0 accent-[var(--color-brand)]"/><span class="flex-1">Featured</span><span '
        f'class="text-xs text-ink-3 tabular-nums">{n}</span></label></div>'
    )


def summary_line(ctx) -> str:
    n, c = len(ctx.publishers), len(countries(ctx))
    return f'{plural(n, "publishing house")} across {plural(c, "country").replace("countrys", "countries")}'


def render(ctx, slug: str) -> tuple:
    pub = ctx.publishers[slug]
    path = f"publishers/{slug}/"
    r = prefix_for(path)
    email = esc(pub.get("email") or ctx.settings["email"])
    links = f'<li><a href="mailto:{email}" class="link">{email}</a></li>'
    if pub.get("website"):
        links += (f'<li><a href="{esc(pub["website"])}" class="link" target="_blank" rel="noopener noreferrer">'
                  "Website</a></li>")
    books = titles(ctx, slug)
    titles_section = ""
    if books:
        titles_section = (
            '<section class="py-14 md:py-20 ground-paper"><div><div class="shell">'
            + section_heading("Titles represented")
            + '<ul class="grid grid-cols-2 gap-x-5 gap-y-9 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">'
            + "".join(f"<li>{book_card(ctx, r, s, b)}</li>" for s, b in books)
            + "</ul></div></div></section>"
        )
    main = (
        '<main id="main" class="flex-1">'
        + breadcrumb(r, [("", "Home"), ("publishers/", "Publishers")], pub["name"])
        + '<section class="py-14 md:py-20 pt-8 md:pt-10"><div><div class="shell"><div class="max-w-3xl"><div '
        f'class="mb-6 flex h-16 items-center">{_logo(ctx, r, pub, False)}</div><h1 class="text-display-lg">'
        f'{esc(pub["name"])}</h1><p class="mt-3 text-[0.9375rem] text-ink-3">{esc(pub.get("country", ""))}</p><ul '
        f'class="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-sm">{links}</ul><div class="mt-8"><div class="prose-editorial">'
        f'{markdown.to_html(pub.get("description", ""))}</div></div></div></div></div></section>'
        + titles_section
        + "<!--$--><!--/$--></main>"
    )
    org = {"@type": "Organization", "name": pub["name"], "url": seo.url(ctx, path),
           "parentOrganization": {"@type": "Organization", "name": ctx.settings["site_name"], "url": seo.url(ctx, "")}}
    if pub.get("logo"):
        org["logo"] = seo.url(ctx, pub["logo"])
    if pub.get("website"):
        org["sameAs"] = pub["website"]
    fallback = f'{pub["name"]} — {_summary(pub)} {len(books)} titles available for translation rights.'
    meta = seo.Seo(path=path, title=pub["name"], description=seo.describe(pub, pub.get("summary"), fallback),
                   jsonld=[org, seo.breadcrumbs(ctx, [("Home", ""), ("Publishers", "publishers/"), (pub["name"], path)])])
    return path, shell.page(r, path, ctx.settings, seo.title_html(ctx, pub, pub["name"]), main,
                            seo_html=seo.head_tags(ctx, meta))


# ---- authors -------------------------------------------------------------

def author_titles(ctx, slug: str) -> int:
    return len(ctx.books_by_author(slug))


def sort_key(name: str) -> tuple:
    """Alphabetical, ignoring accents (Ç sorts with C), like the original lists."""
    base = unicodedata.normalize("NFD", name.replace("ı", "i").replace("İ", "I"))
    return ("".join(c for c in base if not unicodedata.combining(c)).casefold(), name)


def author_card(ctx, r: str, slug: str) -> str:
    author = ctx.authors[slug]
    n = author_titles(ctx, slug)
    return (
        f'<article class="group"><a class="block" href="{r}authors/{slug}/"><div class="flex items-center '
        'justify-center bg-paper-3 text-ink-3 rounded-md" style="aspect-ratio:4/5" aria-hidden="false"><span '
        f'class="font-display text-3xl text-ink-3">{esc(initials(author["name"]))}</span></div><div class="mt-4"><h3 '
        'class="font-display text-lg leading-snug transition-colors group-hover:text-accent">'
        f'{esc(author["name"])}</h3><p class="mt-1 text-[0.8125rem] text-ink-3">{plural(n, "title")}</p></div></a>'
        "</article>"
    )


def authors_alphabetical(ctx) -> list:
    return sorted(ctx.authors, key=lambda s: sort_key(ctx.authors[s]["name"]))


def author_cards(ctx, r: str) -> str:
    return "".join(f"<li>{author_card(ctx, r, s)}</li>" for s in authors_alphabetical(ctx))


def top_authors(ctx, r: str, limit: int = 8) -> str:
    ranked = sorted(ctx.authors, key=lambda s: (-author_titles(ctx, s), sort_key(ctx.authors[s]["name"])))
    return "".join(f'<div class="w-40 sm:w-44 lg:w-48">{author_card(ctx, r, s)}</div>' for s in ranked[:limit])


def letter_nav(ctx) -> str:
    present = {sort_key(a["name"])[0][:1].upper() for a in ctx.authors.values()}
    out = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if letter in present:
            out.append('<li><button type="button" aria-pressed="false" class="grid size-8 place-items-center rounded-sm '
                       'border text-[0.8125rem] font-medium transition-colors border-rule text-ink-2 hover:border-ink '
                       f'hover:text-ink">{letter}</button></li>')
        else:
            out.append('<li><button type="button" disabled="" aria-pressed="false" class="grid size-8 place-items-center '
                       'rounded-sm border text-[0.8125rem] font-medium transition-colors hover:border-ink hover:text-ink '
                       f'cursor-not-allowed border-transparent text-ink-3 opacity-40">{letter}</button></li>')
    return "".join(out)


def authors_with_titles(ctx) -> int:
    return sum(1 for s in ctx.authors if author_titles(ctx, s))
