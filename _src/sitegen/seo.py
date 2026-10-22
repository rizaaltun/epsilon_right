"""Search and sharing metadata: meta description, canonical URL, Open Graph /
Twitter cards and schema.org JSON-LD, plus sitemap.xml, robots.txt and llms.txt.

Every page passes an ``Seo`` to shell.page(). Editors can override the title
and description of any item with its ``seo_title`` / ``seo_description`` fields;
otherwise they are derived from the content.
"""

import html
import json
import re
from dataclasses import dataclass, field

from .html import esc

DESCRIPTION_LIMIT = 158


def clip(text: str, limit: int = DESCRIPTION_LIMIT) -> str:
    """Plain text of at most ``limit`` characters, cut at a word boundary."""
    plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(text or ""))).strip()
    plain = re.sub(r"\*\*|__|(?<!\w)[*_]|[*_](?!\w)|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", plain)
    if len(plain) <= limit:
        return plain
    cut = plain[:limit - 1].rsplit(" ", 1)[0].rstrip(",;:—–- ")
    return cut + "…"


def site_url(ctx) -> str:
    return ctx.settings.get("site_url", "https://epsilonpublishinggroup.com").rstrip("/")


def url(ctx, path: str) -> str:
    """Absolute URL of a site path such as "books/x/" or "/assets/a.jpg"."""
    return f"{site_url(ctx)}/{path.lstrip('/')}"


@dataclass
class Seo:
    path: str                     # page path, e.g. "books/eflatun-koza/" ("" for home)
    title: str                    # plain-text title for sharing (the <title> is set separately)
    description: str = ""
    image: str = ""               # site path of the share image
    type: str = "website"         # og:type
    jsonld: list = field(default_factory=list)
    noindex: bool = False


def organization(ctx) -> dict:
    s = ctx.settings
    org = {
        "@type": "Organization",
        "@id": url(ctx, "#organization"),
        "name": s["site_name"],
        "url": url(ctx, ""),
        "logo": url(ctx, s.get("logo", "/assets/images/demo/brand-epg.png")),
        "email": s["email"],
        "slogan": s.get("tagline", ""),
        "sameAs": [v for v in (s.get("instagram"), s.get("linkedin")) if v],
    }
    if s.get("founding_year"):
        org["foundingDate"] = str(s["founding_year"])
    contact = ctx.shared.get("contact", {})
    office = (contact.get("offices") or [{}])[0]
    if office.get("address"):
        org["address"] = {"@type": "PostalAddress", "streetAddress": office["address"].split("\n")[0],
                          "addressLocality": "Istanbul", "addressCountry": "TR"}
    if contact.get("phone"):
        org["telephone"] = contact["phone"]
    return org


def breadcrumbs(ctx, trail: list) -> dict:
    """``trail``: [(name, path)] from Home to the current page."""
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": name, "item": url(ctx, path)}
            for i, (name, path) in enumerate(trail, start=1)
        ],
    }


def _jsonld(items: list) -> str:
    if not items:
        return ""
    data = {"@context": "https://schema.org", "@graph": items} if len(items) > 1 else {"@context": "https://schema.org", **items[0]}
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'\n<script type="application/ld+json">{text}</script>'


def head_tags(ctx, seo: Seo) -> str:
    """The tags that go right after <title>."""
    description = seo.description or ctx.settings.get("default_description", "")
    image = seo.image or ctx.settings.get("share_image", "")
    canonical = url(ctx, seo.path)
    tags = [
        f'<meta name="description" content="{esc(description)}">' if description else "",
        '<meta name="robots" content="noindex">' if seo.noindex else "",
        f'<link rel="canonical" href="{esc(canonical)}">',
        f'<meta property="og:site_name" content="{esc(ctx.settings["site_name"])}">',
        '<meta property="og:locale" content="en_US">',
        f'<meta property="og:type" content="{seo.type}">',
        f'<meta property="og:title" content="{esc(seo.title)}">',
        f'<meta property="og:description" content="{esc(description)}">' if description else "",
        f'<meta property="og:url" content="{esc(canonical)}">',
        f'<meta property="og:image" content="{esc(url(ctx, image))}">' if image else "",
        f'<meta name="twitter:card" content="{"summary_large_image" if image else "summary"}">',
    ]
    return "\n" + "\n".join(t for t in tags if t) + _jsonld(seo.jsonld)


def title_html(ctx, item: dict, name: str) -> str:
    """<title>: the item's SEO title if set, else "<name> — <site name>"."""
    from .html import esc_title
    return esc_title(item.get("seo_title") or f"{name} — {ctx.settings['site_name']}")


def describe(item: dict, *fallbacks) -> str:
    """The item's SEO description, else the first non-empty fallback, clipped."""
    for text in (item.get("seo_description"), *fallbacks):
        if text and str(text).strip():
            return clip(str(text))
    return ""


LANGUAGES = {"turkish": "tr", "english": "en", "arabic": "ar", "russian": "ru", "german": "de", "french": "fr"}


def age_range(age_group: str):
    """'6+' -> '6-', '3-6' -> '3-6' (schema.org typicalAgeRange)."""
    m = re.fullmatch(r"\s*(\d+)\s*\+\s*", age_group or "")
    if m:
        return f"{m.group(1)}-"
    m = re.fullmatch(r"\s*(\d+)\s*[-–]\s*(\d+)\s*", age_group or "")
    return f"{m.group(1)}-{m.group(2)}" if m else None


# ---- site-wide files -------------------------------------------------------

def sitemap(ctx, paths: list) -> str:
    entries = "".join(f"<url><loc>{esc(url(ctx, p))}</loc></url>\n" for p in sorted(paths, key=lambda p: (p.count("/"), p)))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}</urlset>\n')


AI_CRAWLERS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User",
               "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended", "Bingbot", "CCBot"]


def robots(ctx) -> str:
    """Everyone may crawl everything but the admin panel; AI search crawlers are named
    explicitly so a future blanket rule elsewhere doesn't shut them out by accident."""
    groups = "".join(f"User-agent: {bot}\n" for bot in AI_CRAWLERS)
    return (
        "# Epsilon Publishing Group — the whole site is open to search engines and AI assistants.\n"
        f"User-agent: *\n{groups}Allow: /\nDisallow: /admin/\n\n"
        f"Sitemap: {url(ctx, 'sitemap.xml')}\n"
    )


def llms(ctx, sections: list) -> str:
    """llms.txt (https://llmstxt.org): what the site is and where its content lives,
    in Markdown, for AI assistants. ``sections``: [(heading, [(title, path, note)])]."""
    s = ctx.settings
    out = [f"# {s['site_name']}", "", f"> {s.get('default_description', s.get('tagline', ''))}", ""]
    if s.get("llms_intro"):
        out += [s["llms_intro"], ""]
    out += [f"Rights enquiries: {s['email']}", ""]
    for heading, items in sections:
        if not items:
            continue
        out.append(f"## {heading}")
        out.append("")
        for title, path, note in items:
            out.append(f"- [{title}]({url(ctx, path)})" + (f": {note}" if note else ""))
        out.append("")
    return "\n".join(out)
