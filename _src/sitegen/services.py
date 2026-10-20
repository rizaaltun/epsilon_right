"""Services: /services/<slug>/ and the service cards (on /services/ and under
"Other services" on each service page)."""

from . import markdown, seo, shell
from .components import FILL
from .html import esc, prefix_for
from .news import ZOOM

CHECK = (
    '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" class="mt-0.5 shrink-0 text-accent" fill="none" '
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10.5 8 14.5 '
    '16 5.5"></path></svg>'
)
ARROW = (
    '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 8h11M9.5 4l4 4-4 4"></path></svg>'
)


def ordered(ctx) -> list:
    return sorted(ctx.services.items(), key=lambda kv: (kv[1].get("order") is None, kv[1].get("order") or 0, kv[0]))


def card(r: str, slug: str, item: dict) -> str:
    image = (
        f'<img alt="{esc(item.get("image_alt") or item["title"])}" loading="lazy" decoding="async" data-nimg="fill" '
        f'class="{ZOOM}" style="{FILL}" src="{r}{esc(item["image"].lstrip("/"))}"/>' if item.get("image") else ""
    )
    return (
        '<li class="flex"><article class="card card-hover group overflow-hidden w-full"><a class="flex h-full flex-col" '
        f'href="{r}services/{slug}/"><div class="relative overflow-hidden bg-paper-3" style="aspect-ratio:16/9">{image}'
        '</div><div class="flex flex-1 flex-col p-6"><h3 class="font-display text-xl leading-snug transition-colors '
        f'group-hover:text-accent">{esc(item["title"])}</h3><p class="clamp-3 mt-2.5 text-sm leading-relaxed text-ink-2">'
        f'{esc(item.get("summary", ""))}</p><span class="link-arrow mt-5 text-sm">Learn more{ARROW}</span></div></a>'
        "</article></li>"
    )


def cards(ctx, r: str, exclude: str = "") -> str:
    return "".join(card(r, s, item) for s, item in ordered(ctx) if s != exclude)


def render(ctx, slug: str) -> tuple:
    item = ctx.services[slug]
    path = f"services/{slug}/"
    r = prefix_for(path)
    title = esc(item["title"])
    hero = item.get("hero_image") or item.get("image")
    hero_html = (
        '<div class="shell pt-10 md:pt-14"><div class="relative overflow-hidden bg-paper-3 rounded-lg" '
        f'style="aspect-ratio:21/9"><img alt="{esc(item.get("image_alt") or item["title"])}" decoding="async" '
        f'data-nimg="fill" class="object-cover" style="{FILL}" src="{r}{esc(hero.lstrip("/"))}"/></div></div>'
        if hero else ""
    )
    covers = "".join(
        f'<li class="flex gap-3 text-[0.9375rem] leading-relaxed text-ink-2">{CHECK}<span>{esc(c)}</span></li>'
        for c in item.get("covers", []) if c
    )
    aside = (
        '<aside class="card h-fit p-7"><h2 class="font-display text-xl">What this covers</h2><ul class="mt-5 '
        f'space-y-3.5">{covers}</ul></aside>' if covers else ""
    )
    others = cards(ctx, r, exclude=slug)
    others_html = (
        '<section class="py-14 md:py-20 ground-paper"><div><div class="shell"><div class="mb-8 flex flex-col gap-4 '
        'md:mb-11 md:flex-row md:items-end md:justify-between"><div class="max-w-2xl"><h2 class="text-display-md">'
        f'Other services</h2></div></div><ul class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">{others}</ul></div></div>'
        "</section>" if others else ""
    )
    main = (
        '<main id="main" class="flex-1"><div class="border-b border-rule bg-surface pt-6"><div class="shell"><nav '
        'aria-label="Breadcrumb" class="text-xs text-ink-3"><ol class="flex flex-wrap items-center gap-x-2 gap-y-1"><li '
        f'class="flex items-center gap-2"><a class="hover:text-ink" href="{r}">Home</a><span aria-hidden="true">/</span>'
        f'</li><li class="flex items-center gap-2"><a class="hover:text-ink" href="{r}services/">Services</a><span '
        'aria-hidden="true">/</span></li><li class="flex items-center gap-2"><span aria-current="page" class="text-ink-2">'
        f'{title}</span></li></ol></nav></div></div><header class="border-b border-rule bg-surface py-12 md:py-18"><div '
        f'class="shell"><div class="max-w-3xl"><h1 class="text-display-lg">{title}</h1><p class="mt-5 max-w-2xl text-lg '
        f'leading-relaxed text-ink-2">{esc(item.get("summary", ""))}</p></div></div></header>{hero_html}<section '
        'class="py-14 md:py-20"><div><div class="shell"><div class="grid gap-12 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,'
        f'0.85fr)] lg:gap-20"><div><div class="prose-editorial">{markdown.to_html(item.get("body", ""))}</div><div '
        f'class="mt-10"><a class="btn btn-primary" href="{r}contact/">Talk to the team</a></div></div>{aside}</div></div>'
        f"</div></section>{others_html}<!--$--><!--/$--></main>"
    )
    service = {"@type": "Service", "name": item["title"], "serviceType": item["title"], "url": seo.url(ctx, path),
               "description": item.get("summary", ""),
               "provider": {"@type": "Organization", "name": ctx.settings["site_name"], "url": seo.url(ctx, "")}}
    meta = seo.Seo(path=path, title=item["title"], description=seo.describe(item, item.get("summary"), item.get("body")),
                   image=hero or "",
                   jsonld=[service, seo.breadcrumbs(ctx, [("Home", ""), ("Services", "services/"), (item["title"], path)])])
    return path, shell.page(r, path, ctx.settings, seo.title_html(ctx, item, item["title"]), main,
                            seo_html=seo.head_tags(ctx, meta))
