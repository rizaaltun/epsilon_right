"""Markup pieces reused across page types: breadcrumbs, covers, book cards."""

from . import covers
from .html import esc

FILL = "position:absolute;height:100%;width:100%;left:0;top:0;right:0;bottom:0;color:transparent"
HERO_SIZES = "(min-width: 1024px) 420px, 90vw"
CARD_SIZES = "(min-width: 1280px) 220px, (min-width: 640px) 30vw, 45vw"


def breadcrumb(r: str, trail: list, current: str) -> str:
    """``trail`` is a list of (href, label); href "" is the home page."""
    items = "".join(
        f'<li class="flex items-center gap-2"><a class="hover:text-ink" href="{r + href if href or r else "."}">'
        f'{esc(label)}</a><span aria-hidden="true">/</span></li>'
        for href, label in trail
    )
    return (
        '<div class="shell pt-8"><nav aria-label="Breadcrumb" class="text-xs text-ink-3"><ol class="flex '
        f'flex-wrap items-center gap-x-2 gap-y-1">{items}<li class="flex items-center gap-2"><span '
        f'aria-current="page" class="text-ink-2">{esc(current)}</span></li></ol></nav></div>'
    )


def aspect(book: dict) -> str:
    return "1 / 1" if book.get("square_cover") else "2 / 3"


def cover_img(ctx, r: str, book: dict, hero: bool) -> str:
    sizes, loading = (HERO_SIZES, 'loading="eager" fetchpriority="high"') if hero else (CARD_SIZES, 'loading="lazy"')
    src, variants = covers.resolve(ctx, book["cover"])
    srcset = ""
    if variants:
        widths = ", ".join(f"{r}{path} {w}w" for path, w in variants)
        srcset = f' srcset="{widths}" sizes="{sizes}"'
    return (
        f'<img alt="{esc(book["title"])} — cover" decoding="async" class="object-cover" style="{FILL}" '
        f'src="{r}{src}"{srcset} {loading}/>'
    )


def book_card(ctx, r: str, slug: str, book: dict, article_class: str = "group", hero_image: bool = False) -> str:
    """A cover + title + author card linking to the book page.

    ``hero_image`` reproduces the original pages, where the first cover image on
    a book page always got hero loading hints, even when it sat in a card.
    """
    if book["cover"]:
        art = (
            '<div class="relative overflow-hidden bg-paper-3 h-full w-full">'
            + cover_img(ctx, r, book, hero_image)
            + "</div>"
        )
    else:
        art = (
            '<div class="flex items-center justify-center bg-paper-3 text-ink-3 h-full w-full" aria-hidden="false">'
            f'<span class="px-3 text-center font-display text-sm leading-tight text-ink-3">{esc(book["title"])}</span></div>'
        )
    title = esc(book["title"])
    return (
        f'<article class="{article_class}"><a class="lift block" href="{r}books/{slug}/"><div class="cover lift-object" '
        f'style="aspect-ratio:{aspect(book)}">{art}</div><div class="mt-3.5"><h3 class="clamp-2 font-display '
        'text-[1.0625rem] leading-snug text-balance transition-colors group-hover:text-accent" '
        f'title="{title}">{title}</h3><p class="mt-1 text-[0.8125rem] text-ink-3">{esc(book["author"])}</p></div>'
        "</a></article>"
    )


def section_heading(title_html: str) -> str:
    return (
        '<div class="mb-8 flex flex-col gap-4 md:mb-11 md:flex-row md:items-end md:justify-between">'
        f'<div class="max-w-2xl"><h2 class="text-display-md">{title_html}</h2></div></div>'
    )
