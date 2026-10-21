"""Blog: /blog/<slug>/ posts, the cards on /blog/, and the RSS feed /blog/feed.xml.

A post can name related books; they are shown under the post as book cards,
which links the article to the title pages (and the titles back to search).
The blog only appears in the menus once at least one post exists.
"""

import re
from email.utils import format_datetime
from datetime import datetime, timezone

from . import dates, markdown, seo, shell
from .components import FILL, book_card, section_heading
from .html import esc, prefix_for
from .news import ZOOM, _figure, gallery

WORDS_PER_MINUTE = 200


def ordered(ctx) -> list:
    """Pinned posts first, then newest first."""
    return sorted(ctx.blog.items(), key=lambda kv: (bool(kv[1].get("pinned")), str(kv[1]["date"]), kv[0]), reverse=True)


def reading_time(item) -> str:
    words = len(re.findall(r"\w+", item.get("body", "")))
    return f"{max(1, round(words / WORDS_PER_MINUTE))} min read"


def card(r: str, slug: str, item: dict) -> str:
    d = dates.parse(item["date"])
    image = (
        f'<img alt="{esc(item.get("image_alt") or item["title"])}" loading="lazy" decoding="async" class="{ZOOM}" '
        f'style="{FILL}" src="{r}{esc(item["image"].lstrip("/"))}"/>' if item.get("image") else ""
    )
    tag = esc(item["tags"][0]) if item.get("tags") else ""
    meta = f'<time dateTime="{d.isoformat()}">{dates.long(d)}</time>'
    if tag:
        meta += f'<span aria-hidden="true">·</span><span>{tag}</span>'
    return (
        f'<li><article class="group"><a class="block" href="{r}blog/{slug}/"><div class="relative overflow-hidden '
        f'bg-paper-3 rounded-md" style="aspect-ratio:16/9">{image}</div><div class="mt-4"><div class="flex flex-wrap '
        f'items-center gap-3 text-xs text-ink-3">{meta}</div><h3 class="mt-2 font-display text-xl leading-snug '
        f'text-balance transition-colors group-hover:text-accent">{esc(item["title"])}</h3><p class="clamp-3 mt-2 '
        f'text-sm leading-relaxed text-ink-2">{esc(item.get("excerpt", ""))}</p></div></a></article></li>'
    )


def cards(ctx, r: str, limit=None, exclude: str = "") -> str:
    items = [(s, p) for s, p in ordered(ctx) if s != exclude]
    return "".join(card(r, s, p) for s, p in (items[:int(limit)] if limit else items))


def render(ctx, slug: str) -> tuple:
    item = ctx.blog[slug]
    path = f"blog/{slug}/"
    r = prefix_for(path)
    d = dates.parse(item["date"])
    title = esc(item["title"])
    hero = ""
    if item.get("image"):
        hero = _figure(r, item["image"], item.get("image_alt") or item["title"], item.get("image_ratio", "3/2"),
                       " mx-auto mt-12 max-w-3xl")
    tags = "".join(f'<span class="chip chip-quiet">{esc(t)}</span>' for t in item.get("tags", []))
    byline = esc(item.get("author") or ctx.settings["site_name"])
    books = [(s, ctx.books[s]) for s in item.get("books", []) if s in ctx.books]
    related = ""
    if books:
        related = (
            '<section class="py-14 md:py-20 ground-paper"><div><div class="shell">'
            + section_heading("Titles in this article")
            + '<ul class="grid grid-cols-2 gap-x-5 gap-y-9 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">'
            + "".join(f"<li>{book_card(ctx, r, s, b)}</li>" for s, b in books)
            + "</ul></div></div></section>"
        )
    more_cards = cards(ctx, r, limit=3, exclude=slug)
    more = (
        '<section class="py-14 md:py-20"><div><div class="shell"><div class="mb-8 flex flex-col gap-4 md:mb-11 '
        'md:flex-row md:items-end md:justify-between"><div class="max-w-2xl"><h2 class="text-display-md">More from the '
        f'blog</h2></div><div class="shrink-0"><a class="link-arrow text-sm" href="{r}blog/">All posts</a></div></div>'
        f'<ul class="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">{more_cards}</ul></div></div></section>' if more_cards else ""
    )
    main = (
        '<main id="main" class="flex-1"><section class="py-14 md:py-20"><div><div class="shell"><nav '
        'aria-label="Breadcrumb" class="text-xs text-ink-3 mb-10"><ol class="flex flex-wrap items-center gap-x-2 gap-y-1">'
        f'<li class="flex items-center gap-2"><a class="hover:text-ink" href="{r}">Home</a><span aria-hidden="true">/'
        f'</span></li><li class="flex items-center gap-2"><a class="hover:text-ink" href="{r}blog/">Blog</a><span '
        f'aria-hidden="true">/</span></li><li class="flex items-center gap-2"><span aria-current="page" class="text-ink-2">'
        f'{title}</span></li></ol></nav><article><header class="measure mx-auto text-center">'
        + (f'<div class="flex flex-wrap justify-center gap-2">{tags}</div>' if tags else "")
        + f'<h1 class="mt-5 text-display-lg">{title}</h1><p class="mt-6 flex flex-wrap items-center justify-center '
        f'gap-x-3 gap-y-1 text-sm text-ink-3"><span>{byline}</span><span aria-hidden="true">·</span><time '
        f'dateTime="{d.isoformat()}">{dates.long(d)}</time><span aria-hidden="true">·</span><span>{reading_time(item)}'
        f'</span></p></header>{hero}<div class="measure mx-auto mt-12"><div class="prose-editorial">'
        f'{markdown.to_html(item.get("body", ""))}</div>'
        + gallery(r, item.get("gallery", []))
        + "</div></article></div></div></section>"
        + related + more + "</main>"
    )
    image = item.get("image") or ""
    post = {
        "@type": "BlogPosting",
        "headline": item["title"],
        "url": seo.url(ctx, path),
        "mainEntityOfPage": seo.url(ctx, path),
        "datePublished": d.isoformat(),
        "author": ({"@type": "Person", "name": item["author"]} if item.get("author")
                   else {"@type": "Organization", "name": ctx.settings["site_name"], "url": seo.url(ctx, "")}),
        "publisher": seo.organization(ctx),
        "wordCount": len(re.findall(r"\w+", item.get("body", ""))),
    }
    if image:
        post["image"] = [seo.url(ctx, image)]
    if item.get("excerpt"):
        post["description"] = item["excerpt"]
    if item.get("tags"):
        post["keywords"] = ", ".join(item["tags"])
    if books:
        post["mentions"] = [{"@type": "Book", "name": b["title"], "url": seo.url(ctx, f"books/{s}/")} for s, b in books]
    meta = seo.Seo(path=path, title=item["title"], description=seo.describe(item, item.get("excerpt"), item.get("body")),
                   image=image, type="article",
                   jsonld=[post, seo.breadcrumbs(ctx, [("Home", ""), ("Blog", "blog/"), (item["title"], path)])])
    head_extra = f'<link rel="alternate" type="application/rss+xml" title="{esc(ctx.settings["site_name"])} blog" href="~/blog/feed.xml">'
    return path, shell.page(r, path, ctx.settings, seo.title_html(ctx, item, item["title"]), main,
                            head_extra=head_extra, seo_html=seo.head_tags(ctx, meta))


def feed(ctx) -> str:
    """RSS 2.0 feed of the 20 newest posts."""
    site = seo.site_url(ctx)
    items = []
    for slug, item in sorted(ctx.blog.items(), key=lambda kv: (str(kv[1]["date"]), kv[0]), reverse=True)[:20]:
        d = dates.parse(item["date"])
        when = format_datetime(datetime(d.year, d.month, d.day, 9, tzinfo=timezone.utc))
        link = seo.url(ctx, f"blog/{slug}/")
        items.append(
            f"<item><title>{esc(item['title'])}</title><link>{link}</link><guid>{link}</guid>"
            f"<pubDate>{when}</pubDate><description>{esc(item.get('excerpt', ''))}</description></item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
        f"<title>{esc(ctx.settings['site_name'])} — Blog</title><link>{site}/blog/</link>"
        f"<description>{esc(ctx.settings.get('default_description', ''))}</description><language>en</language>"
        + "".join(items) + "</channel></rss>\n"
    )
