"""The page shell every page shares: <head>, site header, footer, scripts."""

from .html import esc, home_href

FONTS = (
    "https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,100..900;"
    "1,9..144,100..900&family=Inter+Tight:ital,wght@0,100..900;1,100..900&family=Newsreader:"
    "ital,opsz,wght@0,6..72,200..800;1,6..72,200..800&display=swap"
)

CF_ANALYTICS = (
    "<!-- Cloudflare Web Analytics -->\n"
    '<script type="module" src="https://static.cloudflareinsights.com/beacon.min.js" '
    "data-cf-beacon='{\"token\": \"a1ab63230f104f8b891b5b32de5208b0\"}'></script>\n"
    "<!-- End Cloudflare Web Analytics -->\n"
)

CHEVRON = (
    '<svg viewBox="0 0 12 12" width="10" height="10" aria-hidden="true" '
    'class="transition-transform duration-200"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path></svg>'
)

BOOK_CATEGORY_LINKS = [
    ("books/", "All Titles"),
    ("books/?category=childrens-books", "Children's Books"),
    ("books/?category=adult-fiction", "Adult Fiction"),
    ("books/?category=non-fiction", "Non-Fiction"),
    ("books/?category=young-adult", "Young Adult"),
]
NEWS_LINKS = [("fairs-events/", "Where to Meet Us"), ("news/", "Latest News")]


def head(r: str, title_html: str, extra: str = "") -> str:
    """``title_html`` is already escaped (see ``html.esc_title``)."""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{title_html}</title>\n"
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="preconnect" href="https://www.epsilonyayingrubu.com">\n'
        '<link rel="dns-prefetch" href="https://www.epsilonyayingrubu.com">\n'
        f'<link rel="stylesheet" href="{FONTS}">\n'
        "<style>:root{color-scheme:light}body{margin:0;padding:0;font:14px -apple-system,"
        "BlinkMacSystemFont,sans-serif;background:#faf9f5;color:#141413}img{max-width:100%}</style>\n"
        f'<link rel="stylesheet" href="{r}assets/styles.css">{extra.replace("~/", r)}</head>'
        '<body><div hidden=""><!--$--><!--/$--></div><div class="flex min-h-dvh flex-col">'
    )


def _desktop_link(r, path, href, label, exact=False):
    active = path == href if exact else path.startswith(href)
    url = home_href(r) if href == "" else r + href
    if active:
        return (
            '<li><a aria-current="page" class="relative block rounded-sm px-3 py-2 text-[0.9375rem] '
            f'transition-colors text-ink" href="{url}">{esc(label)}<span aria-hidden="true" '
            'class="absolute inset-x-3 -bottom-0.5 h-[2px] bg-ink"></span></a></li>'
        )
    return (
        '<li><a class="relative block rounded-sm px-3 py-2 text-[0.9375rem] transition-colors '
        f'text-ink-2 hover:text-ink" href="{url}">{esc(label)}</a></li>'
    )


def _desktop_menu(path, label, sections):
    active = any(path.startswith(s) for s in sections)
    tone = "text-accent" if active else "text-ink-2 hover:text-ink"
    return (
        '<li class="relative"><button type="button" aria-expanded="false" class="flex items-center '
        f'gap-1.5 rounded-sm px-3 py-2 text-[0.9375rem] transition-colors {tone}">{esc(label)}'
        f"{CHEVRON}</button></li>"
    )


def _mobile_item(r, path, href, label, children=None, exact=False):
    active = path == href if exact else path.startswith(href)
    url = home_href(r) if href == "" else r + href
    tone = "text-accent" if active else "text-ink"
    out = f'<li class="py-1"><a class="block py-2.5 font-display text-lg {tone}" href="{url}">{esc(label)}</a>'
    if children:
        out += '<ul class="mb-2 ml-4 space-y-1 border-l border-rule pl-4">'
        for child_href, child_label in children:
            out += f'<li><a class="block py-1.5 text-sm text-ink-2" href="{r}{child_href}">{esc(child_label)}</a></li>'
        out += "</ul>"
    return out + "</li>"


def header(r: str, path: str, lazy_logo: bool = True) -> str:
    """Site header; ``path`` (e.g. ``"books/x/"``) decides the active menu item."""
    lazy = ' loading="lazy"' if lazy_logo else ""
    desktop = (
        _desktop_link(r, path, "", "Home", exact=True)
        + _desktop_link(r, path, "about-us/", "About")
        + _desktop_menu(path, "Books & Rights", ["books/"])
        + _desktop_link(r, path, "catalogues/", "Catalogues")
        + _desktop_menu(path, "News & Events", ["fairs-events/", "news/"])
        + _desktop_link(r, path, "contact/", "Contact")
    )
    mobile = (
        _mobile_item(r, path, "", "Home", exact=True)
        + _mobile_item(r, path, "about-us/", "About")
        + _mobile_item(r, path, "books/", "Books & Rights", BOOK_CATEGORY_LINKS)
        + _mobile_item(r, path, "catalogues/", "Catalogues")
        + _mobile_item(r, path, "fairs-events/", "News & Events", NEWS_LINKS)
        + _mobile_item(r, path, "contact/", "Contact")
    )
    return (
        '<header class="sticky top-0 z-50 border-b transition-[background-color,border-color,backdrop-filter] '
        'duration-500 border-transparent bg-transparent"><a href="#main" class="sr-only-focusable btn '
        'btn-primary btn-sm absolute top-2 left-2 z-50">Skip to content</a><div class="shell flex h-16 '
        'items-center justify-between gap-6 md:h-20"><a class="flex items-center gap-3" '
        f'aria-label="Epsilon Publishing Group — home" href="{home_href(r)}"><img alt="Epsilon Publishing Group"'
        f'{lazy} width="720" height="310" decoding="async" data-nimg="1" class="h-10 w-auto md:h-12" '
        f'style="color:transparent" src="{r}assets/images/demo/brand-epg.png"/></a><nav aria-label="Main" '
        f'class="hidden lg:block"><ul class="flex items-center gap-1">{desktop}</ul></nav>'
        '<div class="flex items-center gap-1"><a aria-label="Search the catalogue" class="hidden size-9 '
        'place-items-center rounded-full text-ink-2 transition-colors hover:bg-paper-2 hover:text-ink lg:grid" '
        f'href="{r}books/"><svg viewBox="0 0 20 20" width="17" height="17" fill="none" stroke="currentColor" '
        'stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><circle cx="9" cy="9" r="5.5"></circle>'
        '<path d="m13.5 13.5 3.5 3.5"></path></svg></a><button type="button" class="btn btn-ghost btn-sm '
        'lg:hidden" aria-expanded="false" aria-controls="mobile-nav"><span class="sr-only">Open menu</span>'
        '<svg viewBox="0 0 20 20" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" '
        'stroke-linecap="round" aria-hidden="true"><path d="M3 6h14M3 10h14M3 14h14"></path></svg></button>'
        '</div></div><div id="mobile-nav" hidden="" class="max-h-[calc(100dvh-4rem)] overflow-y-auto '
        'border-t border-rule bg-paper lg:hidden"><nav aria-label="Main (mobile)" class="shell py-4">'
        f'<ul class="divide-y divide-rule">{mobile}</ul></nav></div></header>'
    )


FOOTER_CATALOGUE = [
    ("books/", "All books"),
    ("books/?category=fiction", "Fiction"),
    ("books/?category=nonfiction", "Nonfiction"),
    ("books/?category=childrens", "Children's books"),
    ("catalogues/", "Catalogues"),
]
FOOTER_AGENCY = [
    ("authors/", "Authors"),
    ("publishers/", "Publishers"),
    ("fairs-events/", "Fairs & events"),
    ("news/", "News"),
    ("about-us/", "About us"),
    ("contact/", "Contact"),
]
INSTAGRAM_ICON = (
    '<svg viewBox="0 0 18 18" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M6.2 '
    "2.5h5.6a3.7 3.7 0 0 1 3.7 3.7v5.6a3.7 3.7 0 0 1-3.7 3.7H6.2a3.7 3.7 0 0 1-3.7-3.7V6.2a3.7 3.7 0 0 1 "
    "3.7-3.7Zm2.8 3.6a2.9 2.9 0 1 0 0 5.8 2.9 2.9 0 0 0 0-5.8Zm4-.9a.8.8 0 1 0 0 1.6.8.8 0 0 0 0-1.6Z\">"
    "</path></svg>"
)
LINKEDIN_ICON = (
    '<svg viewBox="0 0 18 18" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M4.3 '
    "6.4H6.6V15H4.3V6.4Zm1.2-3.6a1.3 1.3 0 1 1 0 2.7 1.3 1.3 0 0 1 0-2.7ZM8.2 6.4h2.2v1.2c.4-.7 1.2-1.4 "
    "2.5-1.4 1.9 0 2.8 1.2 2.8 3.4V15h-2.3v-4.9c0-1.2-.4-1.8-1.3-1.8-1 0-1.6.7-1.6 1.8V15H8.2V6.4Z\">"
    "</path></svg>"
)


def _footer_nav(r, label, links):
    items = "".join(
        f'<li><a class="text-sm text-ink-inverse/80 transition-colors hover:text-ink-inverse" '
        f'href="{r}{href}">{esc(text)}</a></li>'
        for href, text in links
    )
    return (
        f'<nav class="md:col-span-3" aria-label="{label}"><h2 class="eyebrow mb-4 text-ink-inverse/60">'
        f'{label}</h2><ul class="space-y-2.5">{items}</ul></nav>'
    )


def _social(href, label, icon):
    return (
        f'<li><a href="{href}" target="_blank" rel="noopener noreferrer" aria-label="{label}" class="grid '
        'size-9 place-items-center rounded-full transition-colors text-ink-inverse/70 hover:bg-white/10 '
        f'hover:text-ink-inverse">{icon}</a></li>'
    )


def footer(r: str, settings: dict, lazy_logo: bool = True) -> str:
    email = esc(settings["email"])
    lazy = ' loading="lazy"' if lazy_logo else ""
    return (
        '<footer class="mt-auto ground-brand"><div class="py-8 md:py-10"></div><div class="shell grid gap-10 '
        'py-14 md:grid-cols-12 md:gap-8"><div class="md:col-span-4"><a class="inline-flex" '
        f'aria-label="Epsilon Publishing Group — home" href="{home_href(r)}"><img alt="Epsilon Publishing Group"'
        f'{lazy} width="180" height="44" decoding="async" data-nimg="1" class="h-9 w-auto" '
        f'style="color:transparent" src="{r}assets/images/demo/brand-epg-light.png"/></a>'
        f'<p class="mt-5 max-w-xs text-sm leading-relaxed text-ink-inverse/72">{esc(settings["tagline"])}</p>'
        '<address class="mt-6 space-y-1.5 text-sm not-italic text-ink-inverse/72"><p class="max-w-xs '
        f'whitespace-pre-line">{esc(settings["location"])}</p><p><a href="mailto:{email}" '
        f'class="hover:text-ink-inverse">{email}</a></p></address><ul class="flex flex-wrap items-center '
        'gap-1 mt-6 -ml-2">'
        + _social(esc(settings["instagram"]), "Instagram", INSTAGRAM_ICON)
        + _social(esc(settings["linkedin"]), "LinkedIn", LINKEDIN_ICON)
        + "</ul></div>"
        + _footer_nav(r, "Catalogue", FOOTER_CATALOGUE)
        + _footer_nav(r, "Agency", FOOTER_AGENCY)
        + '<div class="md:col-span-2"><h2 class="eyebrow mb-4 text-ink-inverse/60">Rights enquiries</h2>'
        f'<a href="mailto:{email}" class="text-sm break-words text-ink-inverse/80 hover:text-ink-inverse">'
        f'{email}</a></div></div><div class="border-t border-white/12 py-6"><div class="shell flex flex-col '
        'gap-3 text-xs text-ink-inverse/60 sm:flex-row sm:items-center sm:justify-between">'
        f'<p>{esc(settings["copyright"])}</p><p>Site by<!-- --> <a href="https://www.rizaaltun.com" '
        'target="_blank" rel="noopener noreferrer" class="underline decoration-ink-inverse/30 '
        'underline-offset-2 hover:text-ink-inverse">rizaaltun.com</a></p><ul class="flex flex-wrap gap-x-5 '
        f'gap-y-1"><li><a class="hover:text-ink-inverse" href="{r}privacy-policy/">Privacy policy</a></li>'
        f'<li><a class="hover:text-ink-inverse" href="{r}terms/">Terms of use</a></li></ul></div></div>'
        "</footer>"
    )


def tail(r: str, extra: str = "") -> str:
    return (
        f'</div>\n<script>window.__PREFIX="{r}";</script><script src="{r}assets/site.js" defer></script>'
        f'{extra.replace("~/", r)}{CF_ANALYTICS}</body></html>'
    )


def page(r: str, path: str, settings: dict, title_html: str, main: str, *, head_extra: str = "",
         tail_extra: str = "", lazy_logos: bool = True) -> str:
    """Assemble a full HTML document around ``main`` (the <main> element)."""
    return (
        head(r, title_html, head_extra)
        + header(r, path, lazy_logos)
        + main
        + footer(r, settings, lazy_logos)
        + tail(r, tail_extra)
    )
