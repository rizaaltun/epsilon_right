"""Fairs & events: /fairs-events/<slug>/, the lists on /fairs-events/ and the
home page's "Upcoming fair" card.

An event is upcoming until its end date has passed, so the site needs a
rebuild each day (the Build site workflow runs daily) to move events to "Past".
"""

from . import dates, markdown, shell
from .components import FILL
from .html import esc, esc_title, prefix_for

ARROW = (
    '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 8h11M9.5 4l4 4-4 4"></path></svg>'
)


def _span(item):
    start = dates.parse(item["start_date"])
    end = dates.parse(item.get("end_date") or item["start_date"])
    return start, end


def is_upcoming(item) -> bool:
    return _span(item)[1] >= dates.today()


def upcoming(ctx) -> list:
    """Soonest first."""
    return sorted(((s, e) for s, e in ctx.events.items() if is_upcoming(e)), key=lambda kv: (str(kv[1]["start_date"]), kv[0]))


def past(ctx) -> list:
    """Most recent first."""
    return sorted(((s, e) for s, e in ctx.events.items() if not is_upcoming(e)),
                  key=lambda kv: (str(kv[1]["start_date"]), kv[0]), reverse=True)


def _chips(item) -> str:
    status = '<span class="chip chip-accent">Upcoming</span>' if is_upcoming(item) else '<span class="chip chip-quiet">Past</span>'
    stand = f'<span class="chip chip-quiet">Stand <!-- -->{esc(item["stand"])}</span>' if item.get("stand") else ""
    return status + stand


def _place(item, sep) -> str:
    return sep.join(esc(item[k]) for k in ("venue", "city", "country") if item.get(k))


def _calendar(item) -> tuple:
    start, end = _span(item)
    month = dates.MONTHS[start.month - 1][:3].upper()
    if end.month != start.month:
        month += "–" + dates.MONTHS[end.month - 1][:3].upper()
    days = str(start.day) if end == start else f"{start.day}–{end.day}"
    return month, days


def row(r: str, slug: str, item: dict) -> str:
    month, days = _calendar(item)
    title = esc(item["title"])
    href = f"{r}fairs-events/{slug}/"
    return (
        '<article class="group grid grid-cols-[4.5rem_1fr] items-start gap-4 border-b border-rule py-6 '
        'md:grid-cols-[6rem_1fr_auto] md:gap-8"><div class="text-center">'
        f'<div class="eyebrow text-accent">{month}</div><div class="font-display text-2xl leading-none">{days}</div></div>'
        '<div class="min-w-0"><h3 class="font-display text-xl leading-snug text-balance"><a class="transition-colors '
        f'group-hover:text-accent" href="{href}">{title}</a></h3><p class="mt-1.5 text-sm text-ink-3">{_place(item, " · ")}</p>'
        f'<p class="clamp-2 mt-2 max-w-2xl text-sm leading-relaxed text-ink-2">{esc(item.get("summary", ""))}</p>'
        f'<div class="mt-3 flex flex-wrap items-center gap-2">{_chips(item)}</div></div><div class="col-span-2 '
        f'md:col-span-1 md:self-center"><a class="link-arrow text-sm" aria-label="Read about {title}" href="{href}">'
        f"Details{ARROW}</a></div></article>"
    )


def _section(r, anchor, heading, items, empty_text):
    count = f'{len(items)} event' + ("" if len(items) == 1 else "s")
    body = "".join(row(r, s, e) for s, e in items) if items else (
        f'<p class="py-6 text-sm text-ink-2">{esc(empty_text)}</p>'
    )
    return (
        f'<section id="{anchor}" class="py-14 md:py-20 scroll-mt-24"><div><div class="shell"><div class="mb-8 flex '
        'flex-col gap-4 md:mb-11 md:flex-row md:items-end md:justify-between"><div class="max-w-2xl"><h2 '
        f'class="text-display-md">{heading}</h2><p class="mt-3 text-[0.9375rem] leading-relaxed text-ink-2">{count}</p>'
        f'</div></div><div class="border-t border-rule">{body}</div></div></div></section>'
    )


def sections(ctx, r: str) -> str:
    """The Upcoming and Past lists on /fairs-events/ (Past only once there is one)."""
    out = _section(r, "upcoming", "Upcoming", upcoming(ctx), "New dates will be announced soon.")
    if past(ctx):
        out += _section(r, "past", "Past", past(ctx), "")
    return out


def aside(ctx, r: str) -> str:
    """Contents of the home page's fair card: a pinned event if there is one
    (the soonest upcoming pinned one, else the latest pinned one), otherwise
    the next fair, otherwise the latest one."""
    pinned = [kv for kv in upcoming(ctx) + past(ctx) if kv[1].get("pinned")]
    items = pinned or upcoming(ctx) or past(ctx)
    label = "Upcoming fair" if items and is_upcoming(items[0][1]) else "Latest fair"
    if not items:
        return (
            '<p class="eyebrow mb-3">Fairs</p><p class="font-display text-display-sm leading-tight text-balance">'
            f'Where to meet us</p><a class="link-arrow mt-4 text-sm" href="{r}fairs-events/">View all fairs{ARROW}</a>'
        )
    item = items[0][1]
    return (
        f'<p class="eyebrow mb-3">{label}</p><p class="font-display text-display-sm leading-tight text-balance">'
        f'{esc(item["title"])}</p><p class="mt-2 text-sm text-ink-2">{dates.span(*_span(item))}</p>'
        f'<a class="link-arrow mt-4 text-sm" href="{r}fairs-events/">View all fairs{ARROW}</a>'
    )


def render(ctx, slug: str) -> tuple:
    item = ctx.events[slug]
    path = f"fairs-events/{slug}/"
    r = prefix_for(path)
    start, end = _span(item)
    title = esc(item["title"])
    anchor = "upcoming" if is_upcoming(item) else "past"
    website = (
        f'<p class="mt-8"><a href="{esc(item["website"])}" class="link-arrow text-sm" target="_blank" '
        f'rel="noopener noreferrer">Visit the official event site{ARROW}</a></p>' if item.get("website") else ""
    )
    image = (
        '<div class="relative overflow-hidden bg-paper-3 rounded-md lg:sticky lg:top-28" style="aspect-ratio:4/5">'
        f'<img alt="{esc(item.get("image_alt") or item["title"])}" decoding="async" class="object-cover" style="{FILL}" '
        f'src="{r}{esc(item["image"].lstrip("/"))}"/></div>' if item.get("image") else "<div></div>"
    )
    tiles = "".join(
        f'<li><div class="relative overflow-hidden bg-paper-3 rounded-md" style="aspect-ratio:4/5"><img '
        f'alt="{esc(g.get("alt", ""))}" loading="lazy" decoding="async" class="object-cover" style="{FILL}" '
        f'src="{r}{esc(g["image"].lstrip("/"))}"/></div></li>'
        for g in item.get("gallery", []) if g.get("image")
    )
    gallery = (
        '<div class="mt-16"><h2 class="mb-4 font-display text-xl">Gallery</h2><ul class="mt-3 grid grid-cols-2 gap-3 '
        f'sm:grid-cols-4" aria-label="{title} gallery">{tiles}</ul></div>' if tiles else ""
    )
    main = (
        '<main id="main" class="flex-1"><section class="py-14 md:py-20"><div><div class="shell"><nav '
        'aria-label="Breadcrumb" class="text-xs text-ink-3 mb-10"><ol class="flex flex-wrap items-center gap-x-2 gap-y-1">'
        f'<li class="flex items-center gap-2"><a class="hover:text-ink" href="{r}">Home</a><span aria-hidden="true">/'
        f'</span></li><li class="flex items-center gap-2"><a class="hover:text-ink" href="{r}fairs-events/">Fairs &amp; '
        f'Events</a><span aria-hidden="true">/</span></li><li class="flex items-center gap-2"><a class="hover:text-ink" '
        f'href="{r}fairs-events/#{anchor}">{start.year}</a><span aria-hidden="true">/</span></li><li class="flex '
        f'items-center gap-2"><span aria-current="page" class="text-ink-2">{title}</span></li></ol></nav><div '
        'class="grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,24rem)] lg:gap-16"><div><p class="eyebrow '
        f'text-accent">{dates.span(start, end)}</p><h1 class="mt-3 text-display-lg">{title}</h1><p class="mt-4 text-lg '
        f'text-ink-2">{_place(item, ", ")}</p><div class="mt-6 flex flex-wrap gap-2">{_chips(item)}</div><div '
        f'class="prose-editorial mt-8 measure">{markdown.to_html(item.get("body", ""))}</div>{website}</div>{image}'
        f"</div>{gallery}</div></div></section><!--$--><!--/$--></main>"
    )
    page_title = esc_title(f'{item["title"]} — {ctx.settings["site_name"]}')
    return path, shell.page(r, path, ctx.settings, page_title, main)
