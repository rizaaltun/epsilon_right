"""Instagram posts: the home page Spotlight (latest five) and /spotlight/ (all of them).

A post is ``content/spotlight/<slug>.json``: ``image`` (an upload), ``link`` (the
post on Instagram, which a card opens in a new tab), ``date`` (only sets the
order, newest first; it is not shown) and optional ``caption`` and ``image_alt``. Like uploaded covers,
the image gets 480px / 960px WebP variants (needs Pillow; without it the upload
is used as it is).
"""

from pathlib import Path

from . import covers, dates
from .html import esc

FOLDER = "assets/images/spotlight"
WIDTHS = (480, 960)
SIZES = {
    "home": "(min-width: 64rem) 17vw, min(15rem, 68vw)",
    "page": "(min-width: 80rem) 17vw, (min-width: 64rem) 22vw, (min-width: 40rem) 30vw, 46vw",
}


def ordered(ctx) -> list:
    return sorted(ctx.spotlight.items(), key=lambda kv: (str(kv[1]["date"]), kv[0]), reverse=True)


def _image(ctx, r: str, slug: str, item: dict, sizes: str) -> str:
    rel = str(item.get("image") or "").lstrip("/")
    if not rel or not Path(ctx.root, rel).is_file():
        raise FileNotFoundError(f"spotlight/{slug}: image not found: {item.get('image')!r}")
    variants = covers.make_variants(ctx.root, rel, ctx.write, FOLDER, WIDTHS)
    if not variants:
        return f'src="{r}{esc(rel)}"'
    srcset = ", ".join(f"{r}{esc(path)} {width}w" for path, width in variants)
    return f'src="{r}{esc(variants[0][0])}" srcset="{srcset}" sizes="{SIZES[sizes]}"'


def card(ctx, r: str, slug: str, item: dict, sizes: str) -> str:
    d = dates.parse(item["date"])
    caption = (item.get("caption") or "").strip()
    alt = (item.get("image_alt") or "").strip() or caption or f"Instagram post, {dates.long(d)}"
    link = (item.get("link") or "").strip() or ctx.settings.get("instagram", "")
    caption_html = f'<span class="spot-card-caption">{esc(caption)}</span>' if caption else ""
    return (
        f'<li><a class="spot-card" href="{esc(link)}" target="_blank" rel="noopener noreferrer">'
        f'<span class="spot-card-image"><img alt="{esc(alt)}" loading="lazy" decoding="async" '
        f'{_image(ctx, r, slug, item, sizes)}/></span>{caption_html}'
        '<span class="sr-only"> (opens on Instagram)</span></a></li>'
    )


def cards(ctx, r: str, limit=None, sizes: str = "page") -> str:
    posts = ordered(ctx)
    if limit:
        posts = posts[: int(limit)]
    return "".join(card(ctx, r, slug, item, sizes) for slug, item in posts)
