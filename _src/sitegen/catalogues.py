"""Catalogues: /catalogues/<slug>/ (PDF download plus the page-turning reader),
the cards on /catalogues/, and the reader images.

The reader needs every PDF page as an image. assets/catalogues/readers.json
records, per catalogue, which PDF revision (first 8 hex digits of its SHA-256)
the images in assets/images/catalogues/pages/<slug>-<revision>/ were made from,
with the page count and page ratio. When a catalogue's PDF changes, the build
renders new images with PyMuPDF + Pillow (installed in CI), as
scripts/build_catalogue_readers.py did; without them the page is built
without the reader until CI runs.
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path

from . import markdown, seo, shell
from .components import FILL, book_card
from .html import esc, prefix_for
from .news import ZOOM

MANIFEST = "assets/catalogues/readers.json"
PAGE_WIDTH, COVER_WIDTH = 1800, 700
ARROW = (
    '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 8h11M9.5 4l4 4-4 4"></path></svg>'
)
NEW_BADGE = (
    '<span class="catalogue-new" style="position:absolute;top:12px;right:12px;background:#153f34;color:white;'
    'padding:5px 12px;border-radius:999px;font:600 12px Arial">New</span>'
)
LAYOUT_CSS = (
    '<style id="catalogue-layout">html,body{background:#faf9f5!important;color-scheme:light}.catalogue-reader:not(.is-open)'
    '{display:none!important}.catalogue-reader.is-open{display:grid!important;position:fixed!important;inset:0!important;'
    'width:100vw;height:100vh;background:#faf9f5!important}.catalogue-reader:fullscreen{background:#faf9f5!important}'
    '.catalogue-reader::backdrop{background:#faf9f5}</style>'
)


def ordered(ctx) -> list:
    return sorted(ctx.catalogues.items(), key=lambda kv: (kv[1].get("order") is None, kv[1].get("order") or 0, kv[0]))


def _pdf(ctx, item) -> Path:
    return Path(ctx.root, item["pdf"].lstrip("/"))


def _manifest(ctx) -> dict:
    path = Path(ctx.root, MANIFEST)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def cover(ctx, slug) -> str:
    """Site path of the cover: a custom image, else the one made from page 1."""
    return cover_path_for(ctx.catalogues[slug], slug)


def _render_reader_images(ctx, slug, item, revision):
    try:
        import fitz
        from PIL import Image
    except ImportError:
        return None
    page_dir = Path(ctx.root, "assets/images/catalogues/pages", f"{slug}-{revision}")
    page_dir.mkdir(parents=True, exist_ok=True)
    with fitz.open(_pdf(ctx, item)) as document:
        first = document[0]
        for i, page in enumerate(document):
            pix = page.get_pixmap(matrix=fitz.Matrix(PAGE_WIDTH / page.rect.width, PAGE_WIDTH / page.rect.width), alpha=False)
            Image.frombytes("RGB", [pix.width, pix.height], pix.samples).save(page_dir / f"{i + 1:03d}.webp", "WEBP",
                                                                              quality=90, method=3)
        if not item.get("cover"):
            pix = first.get_pixmap(matrix=fitz.Matrix(COVER_WIDTH / first.rect.width, COVER_WIDTH / first.rect.width))
            Image.frombytes("RGB", [pix.width, pix.height], pix.samples).save(
                Path(ctx.root, "assets/images/catalogues", f"{slug}.webp"), "WEBP", quality=88, method=6)
        info = {"pdf": item["pdf"].lstrip("/"), "revision": revision, "pages": len(document),
                "ratio": round(first.rect.height / first.rect.width, 6)}
    for old in Path(ctx.root, "assets/images/catalogues/pages").glob(f"{slug}-*"):
        if old != page_dir and old.name[len(slug) + 1:].isalnum() and len(old.name) == len(slug) + 9:
            shutil.rmtree(old)
    return info


def reader_info(ctx, slug):
    """{revision, pages, ratio} for the current PDF, rendering images if needed; None if unavailable."""
    if not hasattr(ctx, "_readers"):
        ctx._readers = _manifest(ctx)
    item = ctx.catalogues[slug]
    pdf = _pdf(ctx, item)
    if not pdf.is_file():
        print(f"warning: catalogue {slug}: PDF {item['pdf']} not found", file=sys.stderr)
        return None
    revision = hashlib.sha256(pdf.read_bytes()).hexdigest()[:8]
    info = ctx._readers.get(slug)
    if info and info["revision"] == revision and info["pdf"] == item["pdf"].lstrip("/"):
        return info
    if ctx.write:
        info = _render_reader_images(ctx, slug, item, revision)
        if info:
            ctx._readers[slug] = info
            Path(ctx.root, MANIFEST).write_text(json.dumps(ctx._readers, indent=2) + "\n", encoding="utf-8")
            return info
    print(f"warning: catalogue {slug}: reader images for this PDF need PyMuPDF and Pillow; built without the reader",
          file=sys.stderr)
    return None


def asset_version(ctx) -> str:
    root = Path(ctx.root, "assets")
    return hashlib.sha256((root / "flipbook.js").read_bytes() + (root / "flipbook.css").read_bytes()).hexdigest()[:10]


def size_label(ctx, item) -> str:
    return f"{_pdf(ctx, item).stat().st_size / 1_000_000:.1f} MB"


def index_card(ctx, r, slug) -> str:
    item = ctx.catalogues[slug]
    info = reader_info(ctx, slug)
    pages = f' · {info["pages"]} pages' if info else ""
    title = esc(item["title"])
    return (
        f'<article class="group"><a class="block" href="{r}catalogues/{slug}/?reader=3"><div class="cover aspect-3/4" '
        f'style="position:relative"><img src="{r}{esc(cover(ctx, slug))}" alt="{title} cover" loading="lazy" '
        f'decoding="async" style="width:100%;height:100%;object-fit:contain">{NEW_BADGE if item.get("new") else ""}</div>'
        f'<div class="mt-3.5"><h3 class="font-display text-[1.0625rem] leading-snug">{title}</h3><p class="mt-1 '
        f'text-[0.8125rem] text-ink-3">{esc(item.get("category", ""))} · {esc(item.get("year", ""))}{pages}</p></div>'
        "</a></article>"
    )


def index_cards(ctx, r) -> str:
    return "".join(index_card(ctx, r, s) for s, _ in ordered(ctx))


def _more_card(ctx, r, slug) -> str:
    item = ctx.catalogues[slug]
    title = esc(item["title"])
    return (
        f'<article class="group"><a class="block" href="{r}catalogues/{slug}/"><div class="cover aspect-3/4"><div '
        f'class="relative overflow-hidden bg-paper-3 h-full w-full" style="aspect-ratio:3/4"><img alt="{title} — catalogue '
        f'cover" loading="lazy" decoding="async" data-nimg="fill" class="{ZOOM}" style="{FILL}" src="{r}'
        f'{esc(cover(ctx, slug))}"/></div></div><div class="mt-3.5"><h3 class="font-display text-[1.0625rem] leading-snug '
        f'transition-colors group-hover:text-accent">{title}</h3><p class="mt-1 text-[0.8125rem] text-ink-3">'
        f'{esc(item.get("category", ""))} · {esc(item.get("year", ""))}</p></div></a></article>'
    )


def _reader(r, item, slug, info, pdf_href) -> str:
    title = esc(item["title"])
    return f'''<section id="catalogue-reader" aria-label="Interactive catalogue">
<div class="catalogue-reader" data-catalogue-reader data-title="{title}" data-pages="{r}assets/images/catalogues/pages/{slug}-{info["revision"]}/" data-count="{info["pages"]}" data-ratio="{info["ratio"]:.6f}" data-return="../" role="dialog" aria-modal="true" aria-label="{title}" tabindex="0">
<div class="reader-book" tabindex="0" aria-label="Catalogue pages"></div>
<div class="reader-cover-fallback"><img src="{r}{esc(cover_path_for(item, slug))}" alt="{title} cover" fetchpriority="high"></div>
<button class="reader-exit" type="button" aria-label="Close catalogue">×</button>
<button class="reader-edge prev" type="button" data-prev aria-label="Previous pages" disabled>‹</button>
<button class="reader-edge next" type="button" data-next aria-label="Next pages" disabled>›</button>
<p class="reader-status" role="status" aria-live="polite">…</p>
<p class="reader-help">Drag a page corner or swipe to turn. Use left and right arrows. Double-click a page to read it enlarged. Escape closes the catalogue.</p>
<div class="reader-magnifier" hidden><img alt="Enlarged catalogue page"><button type="button" aria-label="Close enlarged page">×</button></div>
<noscript><a href="{pdf_href}">Open PDF catalogue</a></noscript></div></section>'''


def cover_path_for(item, slug) -> str:
    return (item.get("cover") or f"/assets/images/catalogues/{slug}.webp").lstrip("/")


def render(ctx, slug: str) -> tuple:
    item = ctx.catalogues[slug]
    path = f"catalogues/{slug}/"
    r = prefix_for(path)
    info = reader_info(ctx, slug)
    title = esc(item["title"])
    pdf_href = f'{r}{esc(item["pdf"].lstrip("/"))}'
    description = (f'<div class="prose-editorial mt-7">{markdown.to_html(item["description"])}</div>'
                   if item.get("description") else "")
    read = '<a href="#catalogue-reader" class="btn btn-primary">Read catalogue</a>' if info else ""
    books = ctx.books_in("catalogue", slug)
    titles = ""
    if books:
        cards = "".join(book_card(ctx, r, s, b) for s, b in books)
        n = len(books)
        titles = (
            '<section class="py-14 md:py-20 ground-paper"><div><div class="shell"><div class="mb-8 flex flex-col gap-4 '
            'md:mb-11 md:flex-row md:items-end md:justify-between"><div class="max-w-2xl"><h2 class="text-display-md">'
            'Titles in this catalogue</h2><p class="mt-3 text-[0.9375rem] leading-relaxed text-ink-2">'
            f'{n} {"title" if n == 1 else "titles"}</p></div></div><div class="grid grid-cols-2 gap-x-6 gap-y-10 '
            f'sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">{cards}</div></div></div></section>'
        )
    others = "".join(_more_card(ctx, r, s) for s, _ in ordered(ctx) if s != slug)
    more = (
        '<section class="py-14 md:py-20"><div><div class="shell"><div class="mb-8 flex flex-col gap-4 md:mb-11 '
        'md:flex-row md:items-end md:justify-between"><div class="max-w-2xl"><h2 class="text-display-md">More in Books '
        f'&amp; Publications</h2></div><div class="shrink-0"><a class="link-arrow text-sm" href="{r}catalogues/">All '
        f'catalogues{ARROW}</a></div></div><div class="grid grid-cols-2 gap-x-6 gap-y-10 sm:grid-cols-3 lg:grid-cols-4 '
        f'xl:grid-cols-5">{others}</div></div></div></section>' if others else ""
    )
    main = (
        '<main id="main" class="flex-1"><section class="py-14 md:py-20"><div><div class="shell"><nav aria-label="Breadcrumb" '
        'class="text-xs text-ink-3 mb-10"><ol class="flex flex-wrap items-center gap-x-2 gap-y-1"><li class="flex '
        f'items-center gap-2"><a class="hover:text-ink" href="{r}">Home</a><span aria-hidden="true">/</span></li><li '
        f'class="flex items-center gap-2"><a class="hover:text-ink" href="{r}catalogues/">Catalogues</a><span '
        f'aria-hidden="true">/</span></li><li class="flex items-center gap-2"><a class="hover:text-ink" href="{r}catalogues/'
        '#books-publications">Books &amp; Publications</a><span aria-hidden="true">/</span></li><li class="flex items-center '
        f'gap-2"><span aria-current="page" class="text-ink-2">{title}</span></li></ol></nav><div class="grid gap-10 '
        'lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)] lg:gap-16"><div class="cover aspect-3/4 w-full max-w-xs '
        'lg:max-w-none"><div class="relative overflow-hidden bg-paper-3 h-full w-full" style="aspect-ratio:3/4"><img '
        f'alt="{title} — catalogue cover" decoding="async" data-nimg="fill" class="object-cover" style="{FILL}" '
        f'src="{r}{esc(cover(ctx, slug))}"/></div></div><div><p class="eyebrow">Books &amp; Publications</p><h1 '
        f'class="mt-3 text-display-lg">{title}</h1><div class="mt-5 flex flex-wrap gap-2"><span class="chip chip-quiet">'
        f'{esc(item.get("category", ""))}</span><span class="chip chip-quiet">{esc(item.get("year", ""))}</span></div>'
        f'{description}<div class="mt-9 flex flex-wrap gap-3">{read}<a href="{pdf_href}" download="" class="btn '
        f'btn-outline">Download ({size_label(ctx, item)})</a></div></div></div></div></div></section>'
        + (_reader(r, item, slug, info, pdf_href) if info else "")
        + titles + more + "<!--$--><!--/$--></main>"
    )
    version = asset_version(ctx)
    head_extra = tail_extra = ""
    if info:
        head_extra = (f'{LAYOUT_CSS}<link rel="stylesheet" href="~/assets/catalogue-reader-v3.css?v={version}"><link '
                      f'data-reader-preload rel="preload" as="image" href="~/{esc(cover(ctx, slug))}">')
        tail_extra = (f'<script defer src="~/assets/vendor/page-flip.browser.js?v=2.0.7"></script><script defer '
                      f'src="~/assets/catalogue-reader-v3.js?v={version}"></script>')
    pages_note = f'{info["pages"]}-page ' if info else ""
    fallback = (f'{item["title"]}: {pages_note}rights catalogue from {ctx.settings["site_name"]}'
                + (f' with {len(books)} titles' if books else "") + ". Read it online or download the PDF.")
    doc = {"@type": "DigitalDocument", "name": item["title"], "url": seo.url(ctx, path),
           "image": seo.url(ctx, cover(ctx, slug)), "encodingFormat": "application/pdf",
           "publisher": {"@type": "Organization", "name": ctx.settings["site_name"], "url": seo.url(ctx, "")},
           "associatedMedia": {"@type": "MediaObject", "contentUrl": seo.url(ctx, item["pdf"]), "encodingFormat": "application/pdf"}}
    meta = seo.Seo(path=path, title=item["title"], description=seo.describe(item, item.get("description"), fallback),
                   image="/" + cover(ctx, slug),
                   jsonld=[doc, seo.breadcrumbs(ctx, [("Home", ""), ("Catalogues", "catalogues/"), (item["title"], path)])])
    return path, shell.page(r, path, ctx.settings, seo.title_html(ctx, item, item["title"]), main, head_extra=head_extra,
                            tail_extra=tail_extra, seo_html=seo.head_tags(ctx, meta))
