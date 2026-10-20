"""News articles: /news/<slug>/, plus the news cards used on /news/ and the home page."""

from . import dates, markdown, shell
from .components import FILL
from .html import esc, esc_title, prefix_for

ZOOM = "object-cover transition-transform duration-500 ease-[cubic-bezier(0.22,0.8,0.28,1)] group-hover:scale-[1.03]"


def ordered(ctx) -> list:
    """Newest first."""
    return sorted(ctx.news.items(), key=lambda kv: (str(kv[1]["date"]), kv[0]), reverse=True)


def card(ctx, r: str, slug: str, item: dict) -> str:
    d = dates.parse(item["date"])
    alt = item.get("image_alt") or item["title"]
    image = (
        f'<div class="relative overflow-hidden bg-paper-3 rounded-md" style="aspect-ratio:16/9"><img alt="{esc(alt)}" '
        f'loading="lazy" decoding="async" class="{ZOOM}" style="{FILL}" src="{r}{esc(item["image"].lstrip("/"))}"/></div>'
        if item.get("image") else
        '<div class="relative overflow-hidden bg-paper-3 rounded-md" style="aspect-ratio:16/9"></div>'
    )
    return (
        f'<article class="group news-card"><a class="block" href="{r}news/{slug}/">{image}<div class="mt-4"><div '
        f'class="flex flex-wrap items-center gap-3 text-xs text-ink-3"><time dateTime="{d.isoformat()}">{dates.long(d)}'
        f'</time><span aria-hidden="true">·</span><span>{esc(item["category"])}</span></div><h3 class="mt-2 font-display '
        'leading-snug text-balance transition-colors group-hover:text-accent text-display-sm">'
        f'{esc(item["title"])}</h3><p class="clamp-3 mt-2 text-sm leading-relaxed text-ink-2">{esc(item.get("excerpt", ""))}'
        "</p></div></a></article>"
    )


def cards(ctx, r: str, limit=None) -> str:
    items = ordered(ctx)
    return "".join(card(ctx, r, s, n) for s, n in (items[:int(limit)] if limit else items))


def _figure(r, src, alt, ratio, extra_class=""):
    return (
        f'<div class="relative overflow-hidden bg-paper-3{extra_class} rounded-md" style="aspect-ratio:{ratio}"><img '
        f'alt="{esc(alt)}" decoding="async" class="object-cover" style="{FILL}" src="{r}{esc(src.lstrip("/"))}"/></div>'
    )


def gallery(r: str, images: list) -> str:
    if not images:
        return ""
    tiles = "".join(f"<li>{_figure(r, g['image'], g.get('alt', ''), '4/5')}</li>" for g in images if g.get("image"))
    return (
        '<div class="mt-14"><h2 class="mb-4 font-display text-xl">Gallery</h2><ul class="mt-3 grid grid-cols-2 gap-3 '
        f'sm:grid-cols-4" aria-label="Gallery">{tiles}</ul></div>'
    )


def render(ctx, slug: str) -> tuple:
    item = ctx.news[slug]
    path = f"news/{slug}/"
    r = prefix_for(path)
    d = dates.parse(item["date"])
    hero = ""
    if item.get("image") and item.get("show_image", True):
        hero = _figure(r, item["image"], item.get("image_alt") or item["title"], item.get("image_ratio", "3/2"),
                       " mx-auto mt-12 max-w-3xl")
    source = (
        f'<div class="mt-10 border-t border-rule pt-6"><p class="text-xs text-ink-3">{esc(item["source"])}</p></div>'
        if item.get("source") else ""
    )
    title = esc(item["title"])
    main = (
        '<main id="main" class="flex-1"><section class="py-14 md:py-20"><div><div class="shell"><nav '
        'aria-label="Breadcrumb" class="text-xs text-ink-3 mb-10"><ol class="flex flex-wrap items-center gap-x-2 gap-y-1">'
        f'<li class="flex items-center gap-2"><a class="hover:text-ink" href="{r}">Home</a><span aria-hidden="true">/'
        f'</span></li><li class="flex items-center gap-2"><a class="hover:text-ink" href="{r}news/">News</a><span '
        f'aria-hidden="true">/</span></li><li class="flex items-center gap-2"><span aria-current="page" class="text-ink-2">'
        f'{title}</span></li></ol></nav><article><header class="measure mx-auto text-center"><span class="chip '
        f'chip-accent">{esc(item["category"])}</span><h1 class="mt-5 text-display-lg">{title}</h1><p class="mt-6 flex '
        'flex-wrap items-center justify-center gap-x-3 gap-y-1 text-sm text-ink-3">'
        f'<span>{esc(item.get("byline") or "Editorial desk")}</span><span aria-hidden="true">·</span>'
        f'<time dateTime="{d.isoformat()}">{dates.long(d)}</time></p></header>{hero}<div class="measure mx-auto mt-12">'
        f'<div class="prose-editorial">{markdown.to_html(item.get("body", ""))}</div>'
        + gallery(r, item.get("gallery", []))
        + source
        + "</div></article></div></div></section></main>"
    )
    page_title = esc_title(f'{item["title"]} — {ctx.settings["site_name"]}')
    return path, shell.page(r, path, ctx.settings, page_title, main, lazy_logos=False)
